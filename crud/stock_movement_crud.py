from models.stock_movement import MovementTypeEnum, Stock_movement
from sqlalchemy import insert, select
from sqlalchemy.orm import Session



def create_stock_movement(session, product_id, src_warehouse_id, dest_warehouse_id, quantity, movement_type, reason):
    # Utilisation de la syntaxe insert() au lieu du constructeur d'objet
    stmt = insert(Stock_movement).values(
        product_id=product_id,
        src_warehouse_id=src_warehouse_id,
        dest_warehouse_id=dest_warehouse_id,
        quantity=quantity,
        movement_type=movement_type,
        reason=reason
    )
    
    result = session.execute(stmt)
    session.flush()
    return result

def get_stock_movement_by_id(session: Session, stock_movement_id: int) -> Stock_movement | None:
    stmt = select(Stock_movement).where(Stock_movement.id == stock_movement_id)
    stock_movement = session.execute(stmt).scalar_one_or_none()
    
    return stock_movement

def get_all_stock_movements(session: Session) -> list[Stock_movement]:
    stmt = select(Stock_movement)
    stock_movements = session.execute(stmt).scalars().all()
    
    return stock_movements

def get_stock_movements_filtered(
    session: Session,
    product_id: int | None = None,
    warehouse_id: int | None = None,  # Cherche si c'est la source OU la destination
    movement_type: MovementTypeEnum | None = None
) -> list[Stock_movement]:
    """Une seule fonction pour remplacer toutes les requêtes spécifiques !"""
    stmt = select(Stock_movement)
    
    if product_id is not None:
        stmt = stmt.where(Stock_movement.product_id == product_id)
        
    if warehouse_id is not None:
        # Reprend ta logique OR hyper propre
        stmt = stmt.where(
            (Stock_movement.src_warehouse_id == warehouse_id) | 
            (Stock_movement.dest_warehouse_id == warehouse_id)
        )
        
    if movement_type is not None:
        stmt = stmt.where(Stock_movement.movement_type == movement_type)
        
    return session.execute(stmt).scalars().all()