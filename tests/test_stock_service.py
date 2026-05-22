import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

# Importation des enums métiers requis
from models.stock_movement import MovementTypeEnum

# Importation des fonctions du service de stock sous test
from services.stock_service import (
    add_supplier_reception,
    transfer_stock_inter_warehouse
)

# -------------------------------------------------------------------------
# TESTS: ADD SUPPLIER RECEPTION (Réception Fournisseur)
# -------------------------------------------------------------------------

def test_add_supplier_reception_success_existing_stock():
    """
    Happy Path (Upsert - Update): Verifies supplier intake updates quantity
    when a stock record already exists for the product in that warehouse.
    """
    session_mock = MagicMock(spec=Session)
    
    # Setup warehouse with plenty of capacity
    warehouse_mock = MagicMock(id=1, max_capacity=1000)
    warehouse_mock.name = "Liege Hub"
    
    # Current inventory in warehouse holds a total of 100 items
    current_stock_item = MagicMock(quantity=100)
    
    # Specific stock record for this product already exists with 40 units
    existing_product_stock = MagicMock(quantity=40)
    
    with patch('services.stock_service.get_warehouse_by_id', return_value=warehouse_mock), \
         patch('services.stock_service.get_all_stock_by_warehouse', return_value=[current_stock_item]), \
         patch('services.stock_service.get_stock_by_warehouse_id_product_id', return_value=existing_product_stock), \
         patch('services.stock_service.update_stock_quantity') as mock_update_qty, \
         patch('services.stock_service.create_stock_movement') as mock_create_movement:
         
        add_supplier_reception(session_mock, product_id=10, warehouse_id=1, quantity=50, reason="Custom Intake")
        
        # Verify Upsert behavior: 40 existing + 50 received = 90
        mock_update_qty.assert_called_once_with(session_mock, 1, 10, 90)
        
        # Verify immutable audit trail generation (Source warehouse is None for external supplier)
        mock_create_movement.assert_called_once_with(
            session=session_mock,
            product_id=10,
            src_warehouse_id=None,
            dest_warehouse_id=1,
            quantity=50,
            movement_type=MovementTypeEnum.SUPPLIER_RECEPTION,
            reason="Custom Intake"
        )


def test_add_supplier_reception_success_new_stock():
    """
    Happy Path (Upsert - Create): Verifies supplier intake creates a new stock record
    if the product has never been stored in that warehouse before.
    """
    session_mock = MagicMock(spec=Session)
    warehouse_mock = MagicMock(id=1, max_capacity=500)
    
    with patch('services.stock_service.get_warehouse_by_id', return_value=warehouse_mock), \
         patch('services.stock_service.get_all_stock_by_warehouse', return_value=[]), \
         patch('services.stock_service.get_stock_by_warehouse_id_product_id', return_value=None), \
         patch('services.stock_service.create_stock') as mock_create_stock, \
         patch('services.stock_service.create_stock_movement'):
         
        add_supplier_reception(session_mock, product_id=10, warehouse_id=1, quantity=100)
        
        # Verify New Record creation since stock_record was None
        mock_create_stock.assert_called_once_with(session_mock, 10, 1, 100)


def test_add_supplier_reception_invalid_quantity():
    """Guardrail: Rejects supplier intake if quantity is zero or negative."""
    session_mock = MagicMock(spec=Session)
    
    with pytest.raises(ValueError, match="Reception quantity must be strictly positive."):
        add_supplier_reception(session_mock, product_id=10, warehouse_id=1, quantity=0)


def test_add_supplier_reception_warehouse_saturation():
    """Business Rule Violation: Blocks reception if the incoming quantity saturates the max capacity."""
    session_mock = MagicMock(spec=Session)
    
    warehouse_mock = MagicMock(id=1, max_capacity=200)
    warehouse_mock.name = "Antwerp Center"
    
    # Warehouse already holds 180 items total
    active_stock_mock = MagicMock(quantity=180)
    
    with patch('services.stock_service.get_warehouse_by_id', return_value=warehouse_mock), \
         patch('services.stock_service.get_all_stock_by_warehouse', return_value=[active_stock_mock]):
         
        # 180 current + 30 requested = 210 -> Exceeds max_capacity of 200
        expected_error = r"Warehouse 'Antwerp Center' cannot accommodate this reception\..*Current volume: 180/200, Requested: \+30"
        with pytest.raises(ValueError, match=expected_error):
            add_supplier_reception(session_mock, product_id=10, warehouse_id=1, quantity=30)


# -------------------------------------------------------------------------
# TESTS: INTER-WAREHOUSE STOCK TRANSFER (Transfert Inter-Entrepôt)
# -------------------------------------------------------------------------

def test_transfer_stock_success():
    """
    Happy Path Double-Entry Ledger: Verifies a valid transfer successfully
    deducts stock from source and increments destination stock.
    """
    session_mock = MagicMock(spec=Session)
    
    src_stock_mock = MagicMock(quantity=100) # Source has 100 units
    dest_warehouse_mock = MagicMock(id=2, max_capacity=500) # Dest has room
    dest_stock_mock = MagicMock(quantity=10) # Dest already has 10 units of this product
    
    with patch('services.stock_service.get_stock_by_warehouse_id_product_id') as mock_get_stock, \
         patch('services.stock_service.get_warehouse_by_id', return_value=dest_warehouse_mock), \
         patch('services.stock_service.get_all_stock_by_warehouse', return_value=[]), \
         patch('services.stock_service.update_stock_quantity') as mock_update_qty, \
         patch('services.stock_service.create_stock_movement') as mock_create_movement:
         
        # Side effect to return src_stock first, then dest_stock
        mock_get_stock.side_effect = [src_stock_mock, dest_stock_mock]
        
        transfer_stock_inter_warehouse(session_mock, product_id=5, src_warehouse_id=1, dest_warehouse_id=2, quantity=30)
        
        # Verify Double-Entry Mechanics
        # 1. Credit Source: 100 - 30 = 70
        mock_update_qty.assert_any_call(session_mock, 1, 5, 70)
        # 2. Debit Destination: 10 + 30 = 40
        mock_update_qty.assert_any_call(session_mock, 2, 5, 40)
        
        # Verify Movement Tracking Log
        mock_create_movement.assert_called_once_with(
            session=session_mock,
            product_id=5,
            src_warehouse_id=1,
            dest_warehouse_id=2,
            quantity=30,
            movement_type=MovementTypeEnum.TRANSFER,
            reason="Inter-warehouse transfer from #1 to #2"
        )


def test_transfer_stock_same_warehouse_error():
    """Guardrail: Aborts transfer instantly if source and destination identifiers match."""
    session_mock = MagicMock(spec=Session)
    
    with pytest.raises(ValueError, match="Source and destination warehouses must be distinct."):
        transfer_stock_inter_warehouse(session_mock, product_id=5, src_warehouse_id=1, dest_warehouse_id=1, quantity=10)


def test_transfer_stock_insufficient_source_stock():
    """Blocking Condition: Aborts if the source warehouse does not have enough stock available."""
    session_mock = MagicMock(spec=Session)
    src_stock_mock = MagicMock(quantity=5) # Only 5 units available
    
    with patch('services.stock_service.get_stock_by_warehouse_id_product_id', return_value=src_stock_mock):
        # Requesting 15 units while only having 5 must fail
        with pytest.raises(ValueError, match="Insufficient stock in source warehouse to fulfill transfer."):
            transfer_stock_inter_warehouse(session_mock, product_id=5, src_warehouse_id=1, dest_warehouse_id=2, quantity=15)


def test_transfer_stock_destination_saturation():
    """Blocking Condition: Aborts if the destination warehouse cannot accommodate the transferred volume."""
    session_mock = MagicMock(spec=Session)
    
    src_stock_mock = MagicMock(quantity=100)
    dest_warehouse_mock = MagicMock(id=2, max_capacity=100)
    
    # Destination already holds 90 items total
    dest_total_stock_mock = MagicMock(quantity=90)
    
    with patch('services.stock_service.get_stock_by_warehouse_id_product_id', return_value=src_stock_mock), \
         patch('services.stock_service.get_warehouse_by_id', return_value=dest_warehouse_mock), \
         patch('services.stock_service.get_all_stock_by_warehouse', return_value=[dest_total_stock_mock]):
         
        # 90 current + 20 transferred = 110 -> Exceeds max_capacity of 100
        with pytest.raises(ValueError, match=r"Destination warehouse exceeds maximum volume capacity.*110/100"):
            transfer_stock_inter_warehouse(session_mock, product_id=5, src_warehouse_id=1, dest_warehouse_id=2, quantity=20)