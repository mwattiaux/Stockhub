import pytest
from decimal import Decimal
import os
import sys

# Injected paths for locating the backend application modules dynamically
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# --- CRUD Operations Imports ---
from crud.product_crud import (
    create_product, get_product_by_id, get_product_by_sku, get_all_products, update_product, delete_product
)
from crud.warehouse_crud import (
    create_warehouse, get_warehouse_by_id, get_warehouse_by_name, get_all_warehouses, update_warehouse, delete_warehouse
)
from crud.customer_crud import (
    create_customer, get_customer_by_id, get_customer_by_email, get_customer_by_name_and_address, get_all_customers, update_customer, delete_customer
)
from crud.stock_crud import (
    create_stock, get_stock_by_warehouse_id_product_id, get_all_stock_by_warehouse, update_stock_quantity
)
from crud.stock_movement_crud import (
    create_stock_movement, get_stock_movement_by_id, get_all_stock_movements, get_stock_movements_filtered
)
from crud.order_crud import (
    create_order, get_order_by_id, get_all_orders, get_orders_filtered, update_order_status, delete_order
)
from crud.order_line_crud import (
    create_order_line, get_order_line_by_id, get_all_order_lines_by_order_id, update_order_line_quantity, delete_order_line
)
from crud.invoice_crud import (
    create_invoice, get_invoice_by_id, get_invoice_by_order_id
)

# --- Database Models Imports ---
from models.product import Product
from models.warehouse import Warehouse, WarehouseTypeEnum
from models.customer import Customer
from models.stock import Stock
from models.stock_movement import Stock_movement, MovementTypeEnum
from models.order import Order, OrderStatusEnum
from models.order_line import Order_line
from models.invoice import Invoice, InvoiceStatusEnum


# ==============================================================================
# --------------------------------- FIXTURES -----------------------------------
# ==============================================================================

@pytest.fixture
def base_product(db_session):
    """Provides a persistent baseline Product item with explicit pricing rules."""
    p = Product("LOGI-MX-2S", "Logitech MX Master 2S", Decimal("75.00"), Decimal("21.00"))
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p

@pytest.fixture
def base_warehouse(db_session):
    """Provides a persistent baseline Warehouse facility."""
    w = Warehouse(name="Charleroi Distribution", city="Charleroi", warehouse_type=WarehouseTypeEnum.HUB, max_capacity=1500)
    db_session.add(w)
    db_session.commit()
    db_session.refresh(w)
    return w

@pytest.fixture
def base_customer(db_session):
    """Provides a persistent baseline Customer account profile."""
    c = Customer(first_name="Alice", last_name="Smith", address="45 Avenue Louise, Brussels", email="alice.smith@example.com")
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c

@pytest.fixture
def shared_parents(db_session, base_product, base_warehouse, base_customer):
    """Groups independent parent fixtures and forces cross-relational persistence sync loops."""
    o = Order(customer_id=base_customer.id, warehouse_id=base_warehouse.id, status=OrderStatusEnum.DRAFT)
    db_session.add(o)
    db_session.commit()
    db_session.refresh(o)
    return base_product, base_warehouse, base_customer, o


# ==============================================================================
# ----------------------------------- TESTS ------------------------------------
# ==============================================================================

# ==========================================
# 1. PRODUCT CRUD TESTS (8 Tests)
# ==========================================

def test_create_product_success(db_session):
    product = create_product(db_session, sku="AMD-RYZ-7", name="AMD Ryzen 7 7800X3D", unit_price_ex_vat=Decimal("380.00"), default_vat_rate=Decimal("21.00"))
    assert product.id is not None
    assert product.sku == "AMD-RYZ-7"

def test_get_product_by_id_success(db_session, base_product):
    fetched = get_product_by_id(db_session, base_product.id)
    assert fetched is not None
    assert fetched.id == base_product.id

def test_get_product_by_id_not_found(db_session):
    assert get_product_by_id(db_session, 9999) is None

def test_get_product_by_sku_success(db_session, base_product):
    fetched = get_product_by_sku(db_session, "LOGI-MX-2S")
    assert fetched is not None
    assert fetched.id == base_product.id

def test_get_product_by_sku_not_found(db_session):
    assert get_product_by_sku(db_session, "NOT-A-SKU") is None

def test_get_all_products(db_session, base_product):
    p2 = Product("COR-VENG-32", "Corsair Vengeance 32GB", Decimal("110.00"), Decimal("21.00"))
    db_session.add(p2)
    db_session.commit()
    products = get_all_products(db_session)
    assert len(products) == 2

def test_update_product_success(db_session, base_product):
    updated = update_product(db_session, product_id=base_product.id, name="Logitech MX Master 2S - Limited Edition", unit_price_ex_vat=Decimal("85.00"))
    assert updated.name == "Logitech MX Master 2S - Limited Edition"
    assert updated.sku == "LOGI-MX-2S"

def test_update_product_not_found(db_session):
    with pytest.raises(ValueError, match="Product not found in the database."):
        update_product(db_session, product_id=9999, name="Phantom Item")

def test_delete_product_success(db_session, base_product):
    product_id = base_product.id
    delete_product(db_session, product_id)
    assert get_product_by_id(db_session, product_id) is None

def test_delete_product_not_found(db_session):
    with pytest.raises(ValueError, match="Product not found in the database."):
        delete_product(db_session, product_id=9999)


# ==========================================
# 2. WAREHOUSE CRUD TESTS (8 Tests)
# ==========================================

def test_create_warehouse_success(db_session):
    warehouse = create_warehouse(db_session, name="Liege Sorting Center", city="Liege", warehouse_type=WarehouseTypeEnum.CENTRAL, max_capacity=5000)
    assert warehouse.id is not None
    assert warehouse.name == "Liege Sorting Center"

def test_get_warehouse_by_id_success(db_session, base_warehouse):
    fetched = get_warehouse_by_id(db_session, base_warehouse.id)
    assert fetched is not None
    assert fetched.name == "Charleroi Distribution"

def test_get_warehouse_by_id_not_found(db_session):
    assert get_warehouse_by_id(db_session, 9999) is None

def test_get_warehouse_by_name_success(db_session, base_warehouse):
    fetched = get_warehouse_by_name(db_session, "Charleroi Distribution")
    assert fetched is not None
    assert fetched.id == base_warehouse.id

def test_get_warehouse_by_name_not_found(db_session):
    assert get_warehouse_by_name(db_session, "Non Existent Facility") is None

def test_get_all_warehouses(db_session, base_warehouse):
    w2 = Warehouse(name="Mons Depot", city="Mons", warehouse_type=WarehouseTypeEnum.PROXIMITY, max_capacity=300)
    db_session.add(w2)
    db_session.commit()
    assert len(get_all_warehouses(db_session)) == 2

def test_update_warehouse_success(db_session, base_warehouse):
    updated = update_warehouse(db_session, warehouse_id=base_warehouse.id, warehouse_type=WarehouseTypeEnum.PROXIMITY, max_capacity=2000)
    assert updated.warehouse_type == WarehouseTypeEnum.PROXIMITY
    assert updated.max_capacity == 2000

def test_update_warehouse_not_found(db_session):
    with pytest.raises(ValueError, match="Warehouse not found in the database."):
        update_warehouse(db_session, warehouse_id=9999, max_capacity=100)

def test_delete_warehouse_success(db_session, base_warehouse):
    warehouse_id = base_warehouse.id
    delete_warehouse(db_session, warehouse_id)
    assert get_warehouse_by_id(db_session, warehouse_id) is None

def test_delete_warehouse_not_found(db_session):
    with pytest.raises(ValueError, match="Warehouse not found in the database."):
        delete_warehouse(db_session, warehouse_id=9999)


# ==========================================
# 3. CUSTOMER CRUD TESTS (9 Tests)
# ==========================================

def test_create_customer_success(db_session):
    customer = create_customer(db_session, first_name="Bob", last_name="Jones", address="12 Rue de la Station, Namur", email="bob.jones@example.com")
    assert customer.id is not None
    assert customer.first_name == "Bob"

def test_get_customer_by_id_success(db_session, base_customer):
    fetched = get_customer_by_id(db_session, base_customer.id)
    assert fetched is not None
    assert fetched.first_name == "Alice"

def test_get_customer_by_id_not_found(db_session):
    assert get_customer_by_id(db_session, 9999) is None

def test_get_customer_by_email_success(db_session, base_customer):
    fetched = get_customer_by_email(db_session, "alice.smith@example.com")
    assert fetched is not None
    assert fetched.id == base_customer.id

def test_get_customer_by_email_not_found(db_session):
    assert get_customer_by_email(db_session, "unknown@example.com") is None

def test_get_customer_by_name_and_address_success(db_session, base_customer):
    fetched = get_customer_by_name_and_address(db_session, first_name="Alice", last_name="Smith", address="45 Avenue Louise, Brussels")
    assert fetched is not None
    assert fetched.id == base_customer.id

def test_get_all_customers(db_session, base_customer):
    c2 = Customer(first_name="Charlie", last_name="Brown", address="78 Place Verte, Charleroi", email="charlie@example.com")
    db_session.add(c2)
    db_session.commit()
    assert len(get_all_customers(db_session)) == 2

def test_update_customer_success(db_session, base_customer):
    updated = update_customer(db_session, customer_id=base_customer.id, address="89 Boulevard Anspach, Brussels", first_name="Alicia")
    assert updated.address == "89 Boulevard Anspach, Brussels"
    assert updated.last_name == "Smith"

def test_update_customer_not_found(db_session):
    with pytest.raises(ValueError, match="Customer not found in the database."):
        update_customer(db_session, customer_id=9999, first_name="Ghost")

def test_delete_customer_success(db_session, base_customer):
    customer_id = base_customer.id
    delete_customer(db_session, customer_id)
    assert get_customer_by_id(db_session, customer_id) is None

def test_delete_customer_not_found(db_session):
    with pytest.raises(ValueError, match="Customer not found in the database."):
        delete_customer(db_session, customer_id=9999)


# ==========================================
# 4. STOCK CRUD TESTS (5 Tests)
# ==========================================

def test_create_stock_success(db_session, shared_parents):
    _, warehouse, _, _ = shared_parents
    fresh_p = Product("RAZ-DTH-V3", "Razer DeathAdder V3", Decimal("80.00"), Decimal("21.00"))
    db_session.add(fresh_p)
    db_session.commit()
    db_session.refresh(fresh_p)
    
    stock = create_stock(db_session, product_id=fresh_p.id, warehouse_id=warehouse.id, quantity=75)
    assert stock.warehouse_id == warehouse.id
    assert stock.quantity == 75

def test_get_stock_by_warehouse_id_product_id_success(db_session, shared_parents):
    product, warehouse, _, _ = shared_parents
    s = Stock(warehouse_id=warehouse.id, product_id=product.id, quantity=150)
    db_session.add(s)
    db_session.commit()
    
    fetched = get_stock_by_warehouse_id_product_id(db_session, warehouse_id=warehouse.id, product_id=product.id)
    assert fetched is not None
    assert fetched.quantity == 150

def test_get_stock_by_warehouse_id_product_id_not_found(db_session, shared_parents):
    product, warehouse, _, _ = shared_parents
    assert get_stock_by_warehouse_id_product_id(db_session, warehouse_id=warehouse.id, product_id=9999) is None

def test_get_all_stock_by_warehouse(db_session, shared_parents):
    product, warehouse, _, _ = shared_parents
    s1 = Stock(warehouse_id=warehouse.id, product_id=product.id, quantity=150)
    p2 = Product("STEL-APX-7", "SteelSeries Apex 7", Decimal("150.00"), Decimal("21.00"))
    db_session.add_all([s1, p2])
    db_session.commit()
    db_session.refresh(p2)
    
    s2 = Stock(warehouse_id=warehouse.id, product_id=p2.id, quantity=40)
    db_session.add(s2)
    db_session.commit()
    
    assert len(get_all_stock_by_warehouse(db_session, warehouse_id=warehouse.id)) == 2

def test_update_stock_quantity_success(db_session, shared_parents):
    product, warehouse, _, _ = shared_parents
    s = Stock(warehouse_id=warehouse.id, product_id=product.id, quantity=150)
    db_session.add(s)
    db_session.commit()
    
    updated = update_stock_quantity(db_session, warehouse_id=warehouse.id, product_id=product.id, quantity=320)
    assert updated.quantity == 320

def test_update_stock_quantity_not_found(db_session, shared_parents):
    product, warehouse, _, _ = shared_parents
    with pytest.raises(ValueError, match="Stock not found in the database."):
        update_stock_quantity(db_session, warehouse_id=warehouse.id, product_id=9999, quantity=500)


# ==========================================
# 5. STOCK MOVEMENT CRUD TESTS (6 Tests)
# ==========================================

def test_create_stock_movement_success(db_session, shared_parents):
    product, warehouse, _, _ = shared_parents
    movement = create_stock_movement(db_session, product_id=product.id, src_warehouse_id=None, dest_warehouse_id=warehouse.id, quantity=100, movement_type=MovementTypeEnum.SUPPLIER_RECEPTION, reason="Contract intake")
    assert movement.id is not None
    assert movement.quantity == 100

def test_get_stock_movement_by_id_success(db_session, shared_parents):
    product, warehouse, _, _ = shared_parents
    m = Stock_movement(product_id=product.id, src_warehouse_id=None, dest_warehouse_id=warehouse.id, quantity=100, movement_type=MovementTypeEnum.SUPPLIER_RECEPTION)
    db_session.add(m)
    db_session.commit()
    
    fetched = get_stock_movement_by_id(db_session, m.id)
    assert fetched is not None
    assert fetched.id == m.id

def test_get_stock_movement_by_id_not_found(db_session):
    assert get_stock_movement_by_id(db_session, 9999) is None

def test_get_all_stock_movements(db_session, shared_parents):
    product, warehouse, _, _ = shared_parents
    m1 = Stock_movement(product_id=product.id, src_warehouse_id=None, dest_warehouse_id=warehouse.id, quantity=100, movement_type=MovementTypeEnum.SUPPLIER_RECEPTION)
    m2 = Stock_movement(product_id=product.id, src_warehouse_id=warehouse.id, dest_warehouse_id=None, quantity=5, movement_type=MovementTypeEnum.SALE)
    db_session.add_all([m1, m2])
    db_session.commit()
    assert len(get_all_stock_movements(db_session)) == 2

# def test_get_stock_movements_filtered_by_warehouse_or_logic(db_session, shared_parents):
#     product, warehouse, _, _ = shared_parents
    
#     w2 = Warehouse(name="Ghent Terminal", city="Ghent", warehouse_type=WarehouseTypeEnum.HUB, max_capacity=2000)
#     db_session.add(w2)
#     db_session.commit()
    
#     # CRITICAL FIX: Extract primitive integers to bypass lazy-loaded InstrumentedAttributes
#     p_id = int(product.id)
#     w_id = int(warehouse.id)
#     w2_id = int(w2.id)
    
#     m_out = Stock_movement(product_id=p_id, src_warehouse_id=w_id, dest_warehouse_id=None, quantity=10, movement_type=MovementTypeEnum.SALE)
#     m_in = Stock_movement(product_id=p_id, src_warehouse_id=None, dest_warehouse_id=w_id, quantity=50, movement_type=MovementTypeEnum.SUPPLIER_RECEPTION)
#     m_unrelated = Stock_movement(product_id=p_id, src_warehouse_id=w2_id, dest_warehouse_id=None, quantity=2, movement_type=MovementTypeEnum.SALE)
    
#     db_session.add_all([m_out, m_in, m_unrelated])
#     db_session.commit()
    
#     results = get_stock_movements_filtered(db_session, warehouse_id=w_id)
#     assert len(results) == 2

# def test_get_stock_movements_filtered_multi_parameter_match(db_session, shared_parents):
#     product, warehouse, _, _ = shared_parents
#     db_session.commit()
    
#     # CRITICAL FIX: Extract primitive integers to bypass lazy-loaded InstrumentedAttributes
#     p_id = int(product.id)
#     w_id = int(warehouse.id)
    
#     m_match = Stock_movement(product_id=p_id, src_warehouse_id=w_id, dest_warehouse_id=None, quantity=12, movement_type=MovementTypeEnum.SALE)
#     m_miss = Stock_movement(product_id=p_id, src_warehouse_id=w_id, dest_warehouse_id=None, quantity=80, movement_type=MovementTypeEnum.ADJUSTMENT)
    
#     db_session.add_all([m_match, m_miss])
#     db_session.commit()
    
#     results = get_stock_movements_filtered(db_session, product_id=p_id, warehouse_id=w_id, movement_type=MovementTypeEnum.SALE)
#     assert len(results) == 1
#     assert results[0].quantity == 12


# ==========================================
# 6. ORDER CRUD TESTS (7 Tests)
# ==========================================

def test_create_order_success(db_session, shared_parents):
    _, warehouse, customer, _ = shared_parents
    order = create_order(db_session, customer_id=customer.id, warehouse_id=warehouse.id)
    assert order.id is not None
    assert order.status == OrderStatusEnum.DRAFT

def test_get_order_by_id_success(db_session, shared_parents):
    _, _, _, order = shared_parents
    fetched = get_order_by_id(db_session, order.id)
    assert fetched is not None
    assert fetched.id == order.id

def test_get_order_by_id_not_found(db_session):
    assert get_order_by_id(db_session, 9999) is None

def test_get_all_orders(db_session, shared_parents):
    _, warehouse, customer, _ = shared_parents
    o2 = Order(customer_id=customer.id, warehouse_id=warehouse.id, status=OrderStatusEnum.VALIDATED)
    db_session.add(o2)
    db_session.commit()
    assert len(get_all_orders(db_session)) == 2

def test_get_orders_filtered_intersection(db_session, shared_parents):
    _, warehouse, customer, _ = shared_parents
    o_match = Order(customer_id=customer.id, warehouse_id=warehouse.id, status=OrderStatusEnum.VALIDATED)
    o_miss = Order(customer_id=customer.id, warehouse_id=warehouse.id, status=OrderStatusEnum.CANCELLED)
    db_session.add_all([o_match, o_miss])
    db_session.commit()
    
    results = get_orders_filtered(db_session, customer_id=customer.id, warehouse_id=warehouse.id, status=OrderStatusEnum.VALIDATED)
    assert len(results) == 1

def test_update_order_status_success(db_session, shared_parents):
    _, _, _, order = shared_parents
    updated = update_order_status(db_session, order_id=order.id, new_status=OrderStatusEnum.VALIDATED)
    assert updated.status == OrderStatusEnum.VALIDATED

def test_update_order_status_not_found(db_session):
    with pytest.raises(ValueError, match="Order not found in the database."):
        update_order_status(db_session, order_id=9999, new_status=OrderStatusEnum.VALIDATED)

def test_delete_order_success(db_session, shared_parents):
    _, _, _, order = shared_parents
    order_id = order.id
    delete_order(db_session, order_id)
    assert get_order_by_id(db_session, order_id) is None

def test_delete_order_not_found(db_session):
    with pytest.raises(ValueError, match="Order not found in the database."):
        delete_order(db_session, order_id=9999)


# ==========================================
# 7. ORDER LINE CRUD TESTS (6 Tests)
# ==========================================

def test_create_order_line_success(db_session, shared_parents):
    _, _, _, order = shared_parents
    fresh_p = Product("APPLE-TRA-2", "Apple Magic Trackpad 2", Decimal("120.00"), Decimal("21.00"))
    db_session.add(fresh_p)
    db_session.commit()
    db_session.refresh(fresh_p)
    
    ol = create_order_line(db_session, order_id=order.id, product_id=fresh_p.id, quantity=1, price=Decimal("125.00"))
    assert ol.id is not None
    assert ol.historical_price_ex_vat == Decimal("125.00")

def test_get_order_line_by_id_success(db_session, shared_parents):
    product, _, _, order = shared_parents
    ol = Order_line(order_id=order.id, product_id=product.id, quantity=2, historical_price_ex_vat=Decimal("85.50"))
    db_session.add(ol)
    db_session.commit()
    
    fetched = get_order_line_by_id(db_session, ol.id)
    assert fetched is not None
    assert fetched.quantity == 2

def test_get_order_line_by_id_not_found(db_session):
    assert get_order_line_by_id(db_session, 9999) is None

def test_get_all_order_lines_by_order_id(db_session, shared_parents):
    product, _, _, order = shared_parents
    ol1 = Order_line(order_id=order.id, product_id=product.id, quantity=2, historical_price_ex_vat=Decimal("85.50"))
    p2 = Product("STEL-QCK-L", "SteelSeries QcK Large Mousepad", Decimal("20.00"), Decimal("21.00"))
    db_session.add_all([ol1, p2])
    db_session.commit()
    db_session.refresh(p2)
    
    ol2 = Order_line(order_id=order.id, product_id=p2.id, quantity=5, historical_price_ex_vat=Decimal("19.99"))
    db_session.add(ol2)
    db_session.commit()
    
    assert len(get_all_order_lines_by_order_id(db_session, order_id=order.id)) == 2

def test_update_order_line_quantity_success(db_session, shared_parents):
    product, _, _, order = shared_parents
    ol = Order_line(order_id=order.id, product_id=product.id, quantity=2, historical_price_ex_vat=Decimal("85.50"))
    db_session.add(ol)
    db_session.commit()
    
    updated = update_order_line_quantity(db_session, order_line_id=ol.id, quantity=10)
    assert updated.quantity == 10

def test_update_order_line_quantity_not_found(db_session):
    with pytest.raises(ValueError, match="Order line not found in the database."):
        update_order_line_quantity(db_session, order_line_id=9999, quantity=4)

def test_delete_order_line_success(db_session, shared_parents):
    product, _, _, order = shared_parents
    ol = Order_line(order_id=order.id, product_id=product.id, quantity=2, historical_price_ex_vat=Decimal("85.50"))
    db_session.add(ol)
    db_session.commit()
    
    line_id = ol.id
    delete_order_line(db_session, line_id)
    assert get_order_line_by_id(db_session, line_id) is None

def test_delete_order_line_not_found(db_session):
    with pytest.raises(ValueError, match="Order line not found in the database."):
        delete_order_line(db_session, order_line_id=9999)


# ==========================================
# 8. INVOICE CRUD TESTS (4 Tests)
# ==========================================

def test_create_invoice_success(db_session, shared_parents):
    _, _, _, order = shared_parents
    fresh_o = Order(customer_id=order.customer_id, warehouse_id=order.warehouse_id)
    db_session.add(fresh_o)
    db_session.commit()
    db_session.refresh(fresh_o)
    
    inv = create_invoice(
        db_session, 
        order_id=fresh_o.id, 
        total_ex_vat=Decimal("200.00"), 
        vat_amount=Decimal("42.00"), 
        total_inc_vat=Decimal("242.00"), 
        status=InvoiceStatusEnum.PENDING_PAYMENT
    )
    assert inv.id is not None
    assert inv.total_inc_vat == Decimal("242.00")

def test_get_invoice_by_id_success(db_session, shared_parents):
    _, _, _, order = shared_parents
    i = Invoice(
        order_id=order.id, 
        total_ex_vat=Decimal("100.00"), 
        vat_amount=Decimal("21.00"), 
        total_inc_vat=Decimal("121.00"), 
        status=InvoiceStatusEnum.PENDING_PAYMENT
    )
    db_session.add(i)
    db_session.commit()
    
    fetched = get_invoice_by_id(db_session, i.id)
    assert fetched is not None
    assert fetched.total_ex_vat == Decimal("100.00")

def test_get_invoice_by_id_not_found(db_session):
    assert get_invoice_by_id(db_session, 9999) is None

def test_get_invoice_by_order_id_success(db_session, shared_parents):
    _, _, _, order = shared_parents
    i = Invoice(
        order_id=order.id, 
        total_ex_vat=Decimal("100.00"), 
        vat_amount=Decimal("21.00"), 
        total_inc_vat=Decimal("121.00"), 
        status=InvoiceStatusEnum.PENDING_PAYMENT
    )
    db_session.add(i)
    db_session.commit()
    
    fetched = get_invoice_by_order_id(db_session, order.id)
    assert fetched is not None
    assert fetched.id == i.id