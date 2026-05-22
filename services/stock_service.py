from sqlalchemy.orm import Session
from models.stock_movement import MovementTypeEnum
from crud.stock_crud import get_stock_by_warehouse_id_product_id, create_stock, update_stock_quantity, get_all_stock_by_warehouse
from crud.warehouse_crud import get_warehouse_by_id
from crud.stock_movement_crud import create_stock_movement

def add_supplier_reception(session: Session, product_id: int, warehouse_id: int, quantity: int, reason: str = "Réception Fournisseur") -> None:
    """
    Business Logic: Processes external supplier inventory intake.
    Ensures that intake operations do not saturate warehouse volume boundaries.
    """
    if quantity <= 0:
        raise ValueError("Business Logic Error: Reception quantity must be strictly positive.")
        
    warehouse = get_warehouse_by_id(session, warehouse_id)
    if not warehouse:
        raise ValueError("Business Logic Error: Target warehouse not found.")
        
    # Business Logic: Calculate current saturation level across all items in the warehouse
    current_total_items = sum(stock.quantity for stock in get_all_stock_by_warehouse(session, warehouse_id))
    
    # Business Rule: Enforce that total items + new intake does not exceed maximum capacity
    if current_total_items + quantity > warehouse.max_capacity:
        raise ValueError(
            f"Business Logic Error : Warehouse '{warehouse.name}' cannot accommodate this reception. "
            f"(Current volume: {current_total_items}/{warehouse.max_capacity}, Requested: +{quantity})."
        )
        
    # Business Logic: Resolve inventory record state (Upsert behavior on the stocks table from image_4e9914.png)
    stock_record = get_stock_by_warehouse_id_product_id(session, warehouse_id, product_id)
    if stock_record:
        update_stock_quantity(session, warehouse_id, product_id, stock_record.quantity + quantity)
    else:
        create_stock(session, product_id, warehouse_id, quantity)
        
    # Business Rule (Audit Trail): Generate immutable flow history trace
    # Source warehouse is NULL because it is an external intake (as shown on image_4e9914.png)
    create_stock_movement(
        session=session,
        product_id=product_id,
        src_warehouse_id=None,
        dest_warehouse_id=warehouse_id,
        quantity=quantity,
        movement_type=MovementTypeEnum.SUPPLIER_RECEPTION,
        reason=reason
    )

def transfer_stock_inter_warehouse(session: Session, product_id: int, src_warehouse_id: int, dest_warehouse_id: int, quantity: int) -> None:
    """
    Business Logic: Executes an internal logistical inter-warehouse transfer.
    Runs sequential blocking conditions to preserve material and volume balance integrity.
    """
    if quantity <= 0:
        raise ValueError("Business Logic Error: Transfer quantity must be strictly positive.")
    if src_warehouse_id == dest_warehouse_id:
        raise ValueError("Business Logic Error: Source and destination warehouses must be distinct.")
        
    # 1. Blocking Condition (Source Sufficiency): Source warehouse must hold enough stock
    src_stock = get_stock_by_warehouse_id_product_id(session, src_warehouse_id, product_id)
    if not src_stock or src_stock.quantity < quantity:
        raise ValueError("Business Logic Error: Insufficient stock in source warehouse to fulfill transfer.")
        
    # 2. Blocking Condition (Destination Capacity): Target warehouse must have available volume capacity
    dest_warehouse = get_warehouse_by_id(session, dest_warehouse_id)
    if not dest_warehouse:
        raise ValueError("Business Logic Error: Destination warehouse not found.")
        
    dest_total_items = sum(stock.quantity for stock in get_all_stock_by_warehouse(session, dest_warehouse_id))
    if dest_total_items + quantity > dest_warehouse.max_capacity:
        raise ValueError(
            f"Business Logic Error : Destination warehouse exceeds maximum volume capacity "
            f"({dest_total_items + quantity}/{dest_warehouse.max_capacity})."
        )
        
    # 3. Business Logic: Execute matching double-entry ledger update (Debit / Credit mechanics)
    update_stock_quantity(session, src_warehouse_id, product_id, src_stock.quantity - quantity)
    
    dest_stock = get_stock_by_warehouse_id_product_id(session, dest_warehouse_id, product_id)
    if dest_stock:
        update_stock_quantity(session, dest_warehouse_id, product_id, dest_stock.quantity + quantity)
    else:
        create_stock(session, product_id, dest_warehouse_id, quantity)
        
    # 4. Business Rule (Audit Trail): Commit immutable transactional ledger trace for traceability
    create_stock_movement(
        session=session,
        product_id=product_id,
        src_warehouse_id=src_warehouse_id,
        dest_warehouse_id=dest_warehouse_id,
        quantity=quantity,
        movement_type=MovementTypeEnum.TRANSFER,
        reason=f"Inter-warehouse transfer from #{src_warehouse_id} to #{dest_warehouse_id}"
    )