from models.order import Order, OrderStatusEnum
from sqlalchemy import select
from sqlalchemy.orm import Session



def create_order(session: Session, customer_id: int, warehouse_id: int) -> Order:
    order = Order(customer_id=customer_id, warehouse_id=warehouse_id)
    
    session.add(order)
    session.commit()
    session.refresh(order)
    
    return order

def get_order_by_id(session: Session, order_id: int) -> Order | None:
    stmt = select(Order).where(Order.id == order_id)
    order = session.execute(stmt).scalar_one_or_none()
    
    return order

def get_all_orders(session: Session) -> list[Order]:
    stmt = select(Order)
    orders = session.execute(stmt).scalars().all()
    
    return orders

def get_orders_filtered(session: Session, customer_id: int | None = None, warehouse_id: int | None = None, status: OrderStatusEnum | None = None) -> list[Order]:
    stmt = select(Order)
    
    if customer_id is not None:
        stmt = stmt.where(Order.customer_id == customer_id)
        
    if warehouse_id is not None:
        stmt = stmt.where(Order.warehouse_id == warehouse_id)
        
    if status is not None:
        stmt = stmt.where(Order.status == status)
    
    orders = session.execute(stmt).scalars().all()
    
    return orders

def update_order_status(session: Session, order_id: int, new_status: OrderStatusEnum) -> Order:
    stmt = select(Order).where(Order.id == order_id)
    order = session.execute(stmt).scalar_one_or_none()
    
    if order is None:
        raise ValueError("Order not found in the database.")
    
    order.status = new_status
    session.commit()
    session.refresh(order)
    
    return order

def delete_order(session: Session, order_id: int) -> None:
    stmt = select(Order).where(Order.id == order_id)
    order = session.execute(stmt).scalar_one_or_none()
    
    if order is None:
        raise ValueError("Order not found in the database.")
    
    session.delete(order)
    session.commit()