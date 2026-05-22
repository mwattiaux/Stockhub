import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

# Importation des enums métiers requis
from models.order import OrderStatusEnum
from models.invoice import InvoiceStatusEnum
from models.stock_movement import MovementTypeEnum
from models.warehouse import WarehouseTypeEnum

# Importation des fonctions du service (sans modify_order_metadata)
from services.order_service import (
    add_product_to_order,
    validate_and_finalize_order,
    generate_invoice_html
)

# -------------------------------------------------------------------------
# TESTS: ADD PRODUCT TO ORDER
# -------------------------------------------------------------------------

def test_add_product_to_order_success():
    """Happy Path: Verifies item insertion when the target order is in Draft status."""
    session_mock = MagicMock(spec=Session)
    order_mock = MagicMock(id=10, status=OrderStatusEnum.DRAFT)
    
    with patch('services.order_service.get_order_by_id', return_value=order_mock), \
         patch('services.order_service.create_order_line') as mock_create_line:
        
        add_product_to_order(session_mock, order_id=10, product_id=1, quantity=5, price=Decimal("19.99"))
        
        mock_create_line.assert_called_once_with(
            session_mock, order_id=10, product_id=1, quantity=5, price=Decimal("19.99")
        )


def test_add_product_to_order_not_found():
    """Guardrail: Fails immediately if the order reference does not exist."""
    session_mock = MagicMock(spec=Session)
    
    with patch('services.order_service.get_order_by_id', return_value=None):
        with pytest.raises(ValueError, match="Business Logic Error: Order not found."):
            add_product_to_order(session_mock, order_id=404, product_id=1, quantity=1, price=Decimal("10.00"))


@pytest.mark.parametrize("invalid_status", [
    OrderStatusEnum.VALIDATED,
])
def test_add_product_to_order_immutable_state(invalid_status):
    """Guardrail: Rejects item insertions if the order state has shifted out of Draft bounds."""
    session_mock = MagicMock(spec=Session)
    order_mock = MagicMock(id=10, status=invalid_status)
    
    with patch('services.order_service.get_order_by_id', return_value=order_mock):
        with pytest.raises(ValueError, match="Orders can only be modified or deleted if their status is 'Draft'"):
            add_product_to_order(session_mock, order_id=10, product_id=1, quantity=5, price=Decimal("10.00"))


def test_add_product_to_order_invalid_quantity():
    """Guardrail: Rejects structural inputs with zero or negative quantities."""
    session_mock = MagicMock(spec=Session)
    order_mock = MagicMock(id=10, status=OrderStatusEnum.DRAFT)
    
    with patch('services.order_service.get_order_by_id', return_value=order_mock):
        with pytest.raises(ValueError, match="Ordered quantity must be strictly positive."):
            add_product_to_order(session_mock, order_id=10, product_id=1, quantity=0, price=Decimal("10.00"))


# -------------------------------------------------------------------------
# TESTS: VALIDATE AND FINALIZE ORDER
# -------------------------------------------------------------------------

def test_validate_order_central_warehouse_ban():
    """Logistics Restriction: Central hubs cannot be used to ship directly to final customers."""
    session_mock = MagicMock(spec=Session)
    
    order_mock = MagicMock()
    order_mock.status = OrderStatusEnum.DRAFT
    order_mock.order_lines = [MagicMock()]  # Has item lines
    order_mock.warehouse.warehouse_type = WarehouseTypeEnum.CENTRAL  # Banned setup
    
    with patch('services.order_service.get_order_by_id', return_value=order_mock):
        with pytest.raises(ValueError, match="A warehouse typed as 'Central' cannot directly ship an order"):
            validate_and_finalize_order(session_mock, order_id=10)


def test_validate_order_insufficient_stock():
    """Stock Management: Aborts the transaction chain if available physical items fall short."""
    session_mock = MagicMock(spec=Session)
    
    # Mocking order structure and relationships
    order_mock = MagicMock(warehouse_id=2)
    order_mock.status = OrderStatusEnum.DRAFT
    order_mock.warehouse.name = "Regional Hub"
    order_mock.warehouse.warehouse_type = WarehouseTypeEnum.HUB
    
    # Mock single line asking for 50 units
    line_mock = MagicMock(quantity=50)
    line_mock.product.id = 1
    line_mock.product.name = "Pro Laptop"
    order_mock.order_lines = [line_mock]
    
    # DB stock table only holds 20 units
    stock_mock = MagicMock(quantity=20)
    
    with patch('services.order_service.get_order_by_id', return_value=order_mock), \
         patch('services.order_service.get_stock_by_warehouse_id_product_id', return_value=stock_mock):
        
        # FIX: Escaped the parentheses in the regex match tracking to align with the actual error output
        expected_error_regex = r"Insufficient stock for 'Pro Laptop' .* \(Requested: 50, Available physical balance: 20\)\."
        
        with pytest.raises(ValueError, match=expected_error_regex):
            validate_and_finalize_order(session_mock, order_id=10)


def test_validate_and_finalize_order_success():
    """
    Happy Path Engine Check:
    1. Compares and reduces quantities.
    2. Calculates High-Precision financial totals (Ex-VAT, VAT, Inc-VAT).
    3. Commits database updates, logs movements, and instantiates the pending invoice.
    """
    session_mock = MagicMock(spec=Session)
    
    # Order structural setups
    order_mock = MagicMock(id=100, warehouse_id=2)
    order_mock.status = OrderStatusEnum.DRAFT
    order_mock.warehouse.warehouse_type = WarehouseTypeEnum.HUB
    
    # Setup Cart Items: 2 items of 100.00€ HT with 21% VAT
    line_mock = MagicMock(product_id=1, quantity=2, historical_price_ex_vat=Decimal("100.00"))
    line_mock.product.id = 1
    line_mock.product.default_vat_rate = Decimal("21.00")
    order_mock.order_lines = [line_mock]
    
    # Available stock matches requirement (10 items available)
    stock_mock = MagicMock(quantity=10)
    
    # Capturing execution patches
    with patch('services.order_service.get_order_by_id', return_value=order_mock), \
         patch('services.order_service.get_stock_by_warehouse_id_product_id', return_value=stock_mock), \
         patch('services.order_service.update_order_status') as mock_status, \
         patch('services.order_service.update_stock_quantity') as mock_stock_update, \
         patch('services.order_service.create_stock_movement') as mock_movement, \
         patch('services.order_service.create_invoice') as mock_invoice:
        
        validate_and_finalize_order(session_mock, order_id=100)
        
        # A. Status validation locked down
        mock_status.assert_called_once_with(session_mock, 100, OrderStatusEnum.VALIDATED)
        
        # B. Inventory deducted: 10 original - 2 ordered = 8 remaining
        mock_stock_update.assert_called_once_with(session_mock, 2, 1, 8)
        
        # C. Audit trail movement captured correctly
        mock_movement.assert_called_once_with(
            session=session_mock,
            product_id=1,
            src_warehouse_id=2,
            dest_warehouse_id=None,
            quantity=2,
            movement_type=MovementTypeEnum.SALE,
            reason="Order #100 Dispatch Validation"
        )
        
        # D. High precision calculations verified (200.00 Net, 42.00 Tax, 242.00 Gross)
        mock_invoice.assert_called_once_with(
            session=session_mock,
            order_id=100,
            total_ex_vat=Decimal("200.00"),
            vat_amount=Decimal("42.00"),
            total_inc_vat=Decimal("242.00"),
            status=InvoiceStatusEnum.PENDING_PAYMENT
        )


# -------------------------------------------------------------------------
# TESTS: INVOICE HTML GENERATION
# -------------------------------------------------------------------------

def test_generate_invoice_html_layout():
    """Template Isolation: Assures string compilation injects records accurately into formatting brackets."""
    invoice_mock = MagicMock(id=77, total_ex_vat=Decimal("150.00"), vat_amount=Decimal("31.50"), total_inc_vat=Decimal("181.50"), status="Pending Payment")
    invoice_mock.invoice_date = None
    
    order_mock = invoice_mock.order
    order_mock.id = 100
    
    order_mock.customer.first_name = "Maxime"
    order_mock.customer.last_name = "Doe"
    order_mock.customer.address = "Brussels"
    order_mock.customer.email = "max@hub.be"
    
    order_mock.warehouse.name = "Antwerp Hub"
    order_mock.warehouse.city = "Antwerp"
    
    line_mock = MagicMock(quantity=1, historical_price_ex_vat=Decimal("150.00"))
    line_mock.product.name = "Mechanical Keyboard"
    line_mock.product.sku = "KEY-MX"
    line_mock.product.default_vat_rate = Decimal("21.00")
    order_mock.order_lines = [line_mock]
    
    html_output = generate_invoice_html(invoice_mock)
    
    # Structural content layout validations
    assert "INVOICE / FACTURE" in html_output
    assert "Invoice ID: #77" in html_output
    assert "Maxime Doe" in html_output
    assert "Mechanical Keyboard" in html_output
    assert "KEY-MX" in html_output
    assert "150.00 €" in html_output
    assert "181.50 €" in html_output