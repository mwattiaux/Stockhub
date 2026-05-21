import pytest
from sqlalchemy.exc import IntegrityError
from decimal import Decimal
import os
import sys

# Injected paths for locating the backend application modules dynamically
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Models imports
from models.customer import Customer
from models.warehouse import Warehouse, WarehouseTypeEnum  # <--- Ajout de WarehouseTypeEnum ici
from models.product import Product
from models.order import Order, OrderStatusEnum
from models.invoice import Invoice, InvoiceStatusEnum
from models.order_line import Order_line
from models.stock import Stock
from models.stock_movement import Stock_movement, MovementTypeEnum

# ==========================================
# ---------------- FIXTURES ----------------
# ==========================================

@pytest.fixture
def sample_customer(db_session):
    """
    Provides a persistent Customer record inside the database session.
    Used as a baseline parent entity for order and invoicing tests.
    """
    c = Customer(
        first_name="John", 
        last_name="Doe", 
        address="10 rue de la Paix", 
        email="john@test.be")
    db_session.add(c)
    db_session.commit()
    return c

@pytest.fixture
def sample_warehouse(db_session):
    """
    Provides a persistent Warehouse record representing a distribution center.
    Used for physical inventory tracking, orders routing, and stock movements.
    """
    w = Warehouse(
        name="Central Hub", 
        city="Namur", 
        warehouse_type=WarehouseTypeEnum.HUB,  # <--- CORRECTION: Chaîne "Hub" remplacée par l'Enum
        max_capacity=100
    )
    db_session.add(w)
    db_session.commit()
    return w

@pytest.fixture
def sample_product(db_session):
    """
    Provides a persistent Product record with structured financial defaults.
    Used to validate calculations on order lines, stocks, and historical entries.
    """
    p = Product(
        sku="IPH-16-BLK", 
        name="iPhone 16 Black", 
        unit_price_ex_vat=Decimal("800.00"), 
        default_vat_rate=Decimal("21.00")
    )
    db_session.add(p)
    db_session.commit()
    return p

@pytest.fixture
def sample_order(db_session, sample_customer, sample_warehouse):
    """
    Provides a persistent base Order initialized in a DRAFT state.
    Requires an active Customer and assigned fulfillment Warehouse.
    """
    o = Order(
        customer_id=sample_customer.id, 
        warehouse_id=sample_warehouse.id, 
        status=OrderStatusEnum.DRAFT
    )
    db_session.add(o)
    db_session.commit()
    return o

@pytest.fixture
def sample_order_line(db_session, sample_order, sample_product):
    """
    Provides an Order_line mapping a Product quantity to an active Order.
    Includes an immutable snapshot price simulating point-of-sale pricing logs.
    """
    ol = Order_line(
        order_id=sample_order.id, 
        product_id=sample_product.id, 
        quantity=2, 
        historical_price_ex_vat=Decimal("20.00")
    )
    db_session.add(ol)
    db_session.commit()
    return ol

@pytest.fixture
def sample_stock(db_session, sample_warehouse, sample_product):
    """
    Establishes an active physical batch of inventory within a distinct warehouse location.
    Acts as the baseline setup for composite primary key conflict scenarios.
    """
    s = Stock(
        warehouse_id=sample_warehouse.id, 
        product_id=sample_product.id, 
        quantity=50
    )
    db_session.add(s)
    db_session.commit()
    return s

@pytest.fixture
def sample_movement(db_session, sample_product, sample_warehouse):
    """
    Generates an inbound stock ledger entry representing arriving vendor goods.
    Used to track inventory delta variations without impacting current order pipelines.
    """
    m = Stock_movement(
        product_id=sample_product.id,
        quantity=10,
        movement_type=MovementTypeEnum.SUPPLIER_RECEPTION,
        dest_warehouse_id=sample_warehouse.id
    )
    db_session.add(m)
    db_session.commit()
    return m

@pytest.fixture
def sample_invoice(db_session, sample_order):
    """
    Generates a financial accounting record linked to an existing order.
    Calculates absolute balances for VAT thresholds to check accounting consistency.
    """
    i = Invoice(
        order_id=sample_order.id,
        total_ex_vat=Decimal("100.00"),
        vat_amount=Decimal("21.00"),
        total_inc_vat=Decimal("121.00")
    )
    db_session.add(i)
    db_session.commit()
    return i


# ==========================================
# ---              TESTS                 ---
# ==========================================

# --- CUSTOMER TESTS ---

def test_customer_unique_email(db_session, sample_customer):
    """
    Ensures that two distinct customers cannot share the same email address.
    Verifies that the unique constraint rules on the database engine throw an IntegrityError.
    """
    c2 = Customer(first_name="A", last_name="B", address="1 rue", email="john@test.be")
    db_session.add(c2)
    with pytest.raises(IntegrityError):
        db_session.commit()


# --- WAREHOUSE TESTS ---

def test_warehouse_creation(db_session):
    """
    Validates regular creation logic for a standard fulfillment warehouse configuration.
    Confirms attributes persist accurately and autoincrement sequence returns a valid primary key.
    """
    w = Warehouse(
        name="Logistics One", 
        city="Liege", 
        warehouse_type=WarehouseTypeEnum.CENTRAL,  # <--- CORRECTION: "Central" -> WarehouseTypeEnum.CENTRAL
        max_capacity=500
    )
    db_session.add(w)
    db_session.commit()
    assert w.id is not None
    assert w.name == "Logistics One"

def test_warehouse_capacity_must_be_positive(db_session):
    """
    Ensures maximum volumetric metrics adhere to structural constraints (> 0).
    Verifies that the underlying database level CheckConstraint triggers a hard rollback when violated.
    """
    w = Warehouse(
        name="Invalid Capacity WH", 
        city="Mons", 
        warehouse_type=WarehouseTypeEnum.PROXIMITY,  # <--- CORRECTION: "Proximity" -> WarehouseTypeEnum.PROXIMITY
        max_capacity=0
    )
    db_session.add(w)
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_warehouse_unique_name(db_session, sample_warehouse):
    """
    Guarantees naming schemes remain isolated for location routing processes.
    Re-submitting an existing warehouse name across facilities must trigger an item duplicity error.
    """
    w2 = Warehouse(
        name="Central Hub", 
        city="Charleroi", 
        warehouse_type=WarehouseTypeEnum.HUB,  # <--- CORRECTION: "Hub" -> WarehouseTypeEnum.HUB
        max_capacity=200
    )
    db_session.add(w2)
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_warehouse_relationships(db_session, sample_warehouse):
    """
    Validates relationship collections initialize correctly as empty lists.
    Ensures that unlinked entities return an empty sequence instead of causing unexpected None exceptions.
    """
    assert sample_warehouse.incoming_stock_movements == []
    assert sample_warehouse.outgoing_stock_movements == []
    assert sample_warehouse.orders == []
    assert sample_warehouse.stocks == []


# --- PRODUCT TESTS ---

def test_product_creation(db_session):
    """
    Verifies successful row composition for stock keeping items using valid parameters.
    Confirms automatic defaults (such as standard national tax percentages) load natively if left unspecified.
    """
    p = Product(
        sku="MAC-AIR-13", 
        name="MacBook Air 13", 
        unit_price_ex_vat=Decimal("1200.00")
    )
    db_session.add(p)
    db_session.commit()
    assert p.id is not None
    assert p.default_vat_rate == Decimal("21.00")

def test_product_price_must_be_positive(db_session):
    """
    Ensures catalog items cannot be listed with non-positive price parameters.
    Checks that a zero or negative value fails the check constraint configuration.
    """
    p = Product(
        sku="BAD-PRICE", 
        name="Test", 
        unit_price_ex_vat=Decimal("0.00")
    )
    db_session.add(p)
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_product_unique_sku(db_session, sample_product):
    """
    Ensures that the Stock Keeping Unit (SKU) remains completely unique.
    Re-registering an identical identifier string across items must violate relational uniqueness.
    """
    p2 = Product(
        sku="IPH-16-BLK", 
        name="Another iPhone", 
        unit_price_ex_vat=Decimal("700.00")
    )
    db_session.add(p2)
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_product_relationships(db_session, sample_product):
    """
    Validates that a fresh product correctly references empty operational relationship tracking sets.
    Checks that lists for historical order entries and active physical inventory tracks are initialized.
    """
    assert sample_product.order_lines == []
    assert sample_product.stocks == []
    assert sample_product.stock_movements == []


# --- ORDER TESTS ---

def test_order_relationships_v1(db_session, sample_customer, sample_warehouse):
    """
    Checks relation paths using manual instantiation methods.
    Validates that explicitly tracking through relational keys properly wires access to linked items.
    """
    o = Order(customer_id=sample_customer.id, warehouse_id=sample_warehouse.id, status=OrderStatusEnum.DRAFT)
    db_session.add(o)
    db_session.commit()
    assert o.customer.first_name == "John"
    assert o.warehouse.name == "Central Hub"

def test_order_line_cascade_delete_v1(db_session, sample_customer, sample_warehouse, sample_product):
    """
    Confirms child item cascades trigger automatically across sales documents.
    Removing an order wrapper structure must completely purge dependendent items from database storage.
    """
    o = Order(customer_id=sample_customer.id, warehouse_id=sample_warehouse.id)
    db_session.add(o)
    db_session.flush()
    
    line = Order_line(order_id=o.id, product_id=sample_product.id, quantity=5, historical_price_ex_vat=Decimal("10.00"))
    db_session.add(line)
    db_session.commit()
    
    db_session.delete(o)
    db_session.commit()
    assert db_session.query(Order_line).count() == 0

def test_order_creation(db_session, sample_customer, sample_warehouse):
    """
    Verifies that a sales order commits with valid foreign references and sets status constraints correctly.
    Confirms timestamp logic applies a value automatically during engine execution.
    """
    o = Order(
        customer_id=sample_customer.id, 
        warehouse_id=sample_warehouse.id, 
        status=OrderStatusEnum.VALIDATED
    )
    db_session.add(o)
    db_session.commit()
    
    assert o.id is not None
    assert o.status == OrderStatusEnum.VALIDATED
    assert o.order_date is not None

def test_order_invalid_customer_fails(db_session, sample_warehouse):
    """
    Validates that foreign key constraints prevent orders from referencing non-existent customers.
    Requires 'PRAGMA foreign_keys=ON' to be enabled in SQLite to catch the relational violation.
    """
    o = Order(customer_id=999, warehouse_id=sample_warehouse.id)
    db_session.add(o)
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_order_cascade_delete_v2(db_session, sample_order, sample_product):
    """
    Validates database line cascade logic by referencing pre-existing mock order records.
    Ensures orphans are deleted when the parent order is deleted from the session.
    """
    line = Order_line(
        order_id=sample_order.id, 
        product_id=sample_product.id, 
        quantity=5, 
        historical_price_ex_vat=Decimal("10.00")
    )
    db_session.add(line)
    db_session.commit()
    
    db_session.delete(sample_order)
    db_session.commit()
    
    assert db_session.query(Order_line).filter_by(order_id=sample_order.id).count() == 0

def test_order_relationships_v2(db_session, sample_order, sample_customer, sample_warehouse):
    """
    Ensures parent reference relationships match fixture definitions accurately.
    Confirms dependent objects start with an empty array or evaluate as unlinked None elements.
    """
    assert sample_order.customer == sample_customer
    assert sample_order.warehouse == sample_warehouse
    assert sample_order.order_lines == []
    assert sample_order.invoice is None


# --- ORDER LINE TESTS ---

def test_order_line_creation(db_session, sample_order, sample_product):
    """
    Validates creation logic on items added to an active sales document ledger.
    Ensures quantity limits match assignment constraints and properties persist reliably.
    """
    ol = Order_line(
        order_id=sample_order.id, 
        product_id=sample_product.id, 
        quantity=1, 
        historical_price_ex_vat=Decimal("50.00")
    )
    db_session.add(ol)
    db_session.commit()
    assert ol.id is not None
    assert ol.quantity == 1

def test_order_line_quantity_positive(db_session, sample_order, sample_product):
    """
    Enforces rules that prevent ordering a zero or negative number of items.
    Checks that the 'check_quantity_positive' condition blocks invalid entries.
    """
    ol = Order_line(
        order_id=sample_order.id, 
        product_id=sample_product.id, 
        quantity=0, 
        historical_price_ex_vat=Decimal("10.00")
    )
    db_session.add(ol)
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_order_line_price_non_negative(db_session, sample_order, sample_product):
    """
    Ensures price entries on order lines cannot fall below zero.
    Checks that negative entries fail validation rules on the transaction block.
    """
    ol = Order_line(
        order_id=sample_order.id, 
        product_id=sample_product.id, 
        quantity=1, 
        historical_price_ex_vat=Decimal("-1.00")
    )
    db_session.add(ol)
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_order_line_relationships(db_session, sample_order_line, sample_order, sample_product):
    """
    Verifies that order line entities can navigate back to their parents.
    Checks that back-references resolve to the correct Order and Product objects.
    """
    assert sample_order_line.order == sample_order
    assert sample_order_line.product == sample_product


# --- STOCK TESTS ---

def test_stock_creation(db_session, sample_warehouse, sample_product):
    """
    Validates entry creation for physical inventory allocation rows.
    Confirms metrics reflect quantity values reliably on success.
    """
    s = Stock(
        warehouse_id=sample_warehouse.id, 
        product_id=sample_product.id, 
        quantity=10
    )
    db_session.add(s)
    db_session.commit()
    assert s.quantity == 10

def test_stock_quantity_non_negative(db_session, sample_warehouse, sample_product):
    """
    Ensures inventory records cannot contain negative balances.
    Checks that negative quantity entries are blocked by database-level verification rules.
    """
    s = Stock(
        warehouse_id=sample_warehouse.id, 
        product_id=sample_product.id, 
        quantity=-5
    )
    db_session.add(s)
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_stock_composite_primary_key(db_session, sample_stock, sample_warehouse, sample_product):
    """
    Validates that a warehouse-product combination can only have a single inventory record.
    Uses expunge() to clear memory tracking so SQLite handles the unique constraint validation directly.
    """
    # 1. Evict the fixture instance from the session cache
    db_session.expunge(sample_stock)
    
    # 2. Create the duplicate object
    s2 = Stock(
        warehouse_id=sample_warehouse.id, 
        product_id=sample_product.id, 
        quantity=20
    )
    db_session.add(s2)
    
    # 3. SQLite will now receive the raw INSERT, see the duplicate PK, and throw the IntegrityError
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_stock_cascade_delete_warehouse(db_session, sample_stock, sample_warehouse):
    """
    Verifies that removing a Warehouse deletes all associated Stock records.
    Requires relationship definitions or cascade rules to prevent primary key issues from blanking columns out.
    """
    db_session.delete(sample_warehouse)
    db_session.commit()
    assert db_session.query(Stock).count() == 0


# --- STOCK MOVEMENT TESTS ---

def test_movement_creation(db_session, sample_product, sample_warehouse):
    """
    Validates creation logic for stock transfer records (such as order shipments).
    Ensures that movement types map correctly to the defined options.
    """
    m = Stock_movement(
        product_id=sample_product.id,
        quantity=5,
        movement_type=MovementTypeEnum.SALE,
        src_warehouse_id=sample_warehouse.id
    )
    db_session.add(m)
    db_session.commit()
    assert m.id is not None
    assert m.movement_type == MovementTypeEnum.SALE

def test_movement_quantity_positive(db_session, sample_product):
    """
    Ensures inventory adjustments require values greater than zero.
    Verifies that zero-quantity logs fail check-constraint rule validation.
    """
    m = Stock_movement(
        product_id=sample_product.id,
        quantity=0,  
        movement_type=MovementTypeEnum.ADJUSTMENT
    )
    db_session.add(m)
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_movement_warehouse_relationships(db_session, sample_product, sample_warehouse):
    """
    Validates that transfer steps connect correctly to parent facilities.
    Assigns relationships directly in memory to handle constructor limitations set by init=False.
    """
    w_dest = sample_warehouse
    
    # 1. Create the movement using the ID (which your constructor allows)
    m = Stock_movement(
        product_id=sample_product.id,
        quantity=2,
        movement_type=MovementTypeEnum.TRANSFER,
        src_warehouse_id=None,
        dest_warehouse_id=w_dest.id  # Pass the ID here
    )
    
    # 2. THE FIX: Manually link the object in memory right after initialization
    m.dest_warehouse = w_dest
    
    db_session.add(m)
    db_session.commit()
    
    # 3. Refresh to guarantee the state matches the DB
    db_session.refresh(m)
    
    assert m.dest_warehouse == w_dest
    assert m.src_warehouse is None

def test_movement_product_relationship(db_session, sample_movement, sample_product):
    """
    Validates product links on stock transfer entries.
    Ensures that logistics records connect to the right product references.
    """
    assert sample_movement.product == sample_product


# --- INVOICE TESTS ---

def test_invoice_creation(db_session, sample_order):
    """
    Validates accounting document generation routines for completed orders.
    Ensures default payment status codes apply correctly if left unspecified.
    """
    i = Invoice(
        order_id=sample_order.id,
        total_ex_vat=Decimal("50.00"),
        vat_amount=Decimal("10.50"),
        total_inc_vat=Decimal("60.50")
    )
    db_session.add(i)
    db_session.commit()
    
    assert i.id is not None
    assert i.status == InvoiceStatusEnum.PENDING_PAYMENT
    assert i.invoice_date is not None

def test_invoice_unique_order(db_session, sample_invoice, sample_order):
    """
    Enforces a strict 1-to-1 relationship rule between invoices and orders.
    Prevents duplicate billing by ensuring an order cannot have more than one invoice record.
    """
    i2 = Invoice(
        order_id=sample_order.id, 
        total_ex_vat=Decimal("20.00"),
        vat_amount=Decimal("4.20"),
        total_inc_vat=Decimal("24.20")
    )
    db_session.add(i2)
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_invoice_relationship(db_session, sample_invoice, sample_order):
    """
    Verifies bidirectional references for billing models.
    Ensures parent billing entries link back to the correct order definitions.
    """
    assert sample_invoice.order == sample_order