from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models.stock_movement import MovementTypeEnum
from crud.stock_crud import get_stock_by_warehouse_id_product_id, create_stock, update_stock_quantity, get_all_stock_by_warehouse
from crud.warehouse_crud import get_warehouse_by_id
from crud.stock_movement_crud import create_stock_movement

# ==========================================
# STOCK BUSINESS LOGIC
# ==========================================

def add_supplier_reception(session: Session, product_id: int, warehouse_id: int, quantity: int, reason: str = "Réception Fournisseur") -> None:
    # 1. Validation métier
    if quantity <= 0:
        raise ValueError("Business Logic Error: Reception quantity must be strictly positive.")
    
    warehouse = get_warehouse_by_id(session, warehouse_id)
    if not warehouse:
        raise ValueError("Business Logic Error: Target warehouse not found.")
        
    current_total_items = sum(stock.quantity for stock in get_all_stock_by_warehouse(session, warehouse_id))
    if current_total_items + quantity > warehouse.max_capacity:
        raise ValueError(f"Business Logic Error: Warehouse '{warehouse.name}' capacity exceeded.")

    # 2. Persistance sécurisée
    try:
        stock_record = get_stock_by_warehouse_id_product_id(session, warehouse_id, product_id)
        if stock_record:
            update_stock_quantity(session, warehouse_id, product_id, stock_record.quantity + quantity)
        else:
            create_stock(session, product_id, warehouse_id, quantity)
        
        create_stock_movement(
            session=session,
            product_id=product_id,
            src_warehouse_id=None,
            dest_warehouse_id=warehouse_id,
            quantity=quantity,
            movement_type=MovementTypeEnum.SUPPLIER_RECEPTION,
            reason=reason
        )
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        raise RuntimeError(f"Database error during supplier reception: {e}")

def transfer_stock_inter_warehouse(session: Session, product_id: int, src_warehouse_id: int, dest_warehouse_id: int, quantity: int) -> None:
    # 1. Validation métier
    if quantity <= 0:
        raise ValueError("Business Logic Error: Transfer quantity must be strictly positive.")
    if src_warehouse_id == dest_warehouse_id:
        raise ValueError("Business Logic Error: Source and destination warehouses must be distinct.")
        
    src_stock = get_stock_by_warehouse_id_product_id(session, src_warehouse_id, product_id)
    if not src_stock or src_stock.quantity < quantity:
        raise ValueError("Business Logic Error: Insufficient stock in source warehouse.")
        
    dest_warehouse = get_warehouse_by_id(session, dest_warehouse_id)
    if not dest_warehouse:
        raise ValueError("Business Logic Error: Destination warehouse not found.")
        
    dest_total_items = sum(stock.quantity for stock in get_all_stock_by_warehouse(session, dest_warehouse_id))
    if dest_total_items + quantity > dest_warehouse.max_capacity:
        raise ValueError("Business Logic Error: Destination warehouse capacity exceeded.")
        
    # 2. Persistance sécurisée (Double-entry ledger logic)
    try:
        # Débit source
        update_stock_quantity(session, src_warehouse_id, product_id, src_stock.quantity - quantity)
        
        # Crédit destination
        dest_stock = get_stock_by_warehouse_id_product_id(session, dest_warehouse_id, product_id)
        if dest_stock:
            update_stock_quantity(session, dest_warehouse_id, product_id, dest_stock.quantity + quantity)
        else:
            create_stock(session, product_id, dest_warehouse_id, quantity)
            
        # Traçabilité
        create_stock_movement(
            session=session,
            product_id=product_id,
            src_warehouse_id=src_warehouse_id,
            dest_warehouse_id=dest_warehouse_id,
            quantity=quantity,
            movement_type=MovementTypeEnum.TRANSFER,
            reason=f"Inter-warehouse transfer from #{src_warehouse_id} to #{dest_warehouse_id}"
        )
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        raise RuntimeError(f"Database error during stock transfer: {e}")