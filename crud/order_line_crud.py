from decimal import Decimal
from models.order_line import Order_line
from sqlalchemy import select
from sqlalchemy.orm import Session



def create_order_line(session: Session, order_id: int, product_id: int, quantity: int, price: Decimal) -> Order_line:
    order_line = Order_line(order_id=order_id, product_id=product_id, quantity=quantity, historical_price_ex_vat=price)
    
    session.add(order_line)
    session.flush()
    return order_line

def get_order_line_by_id(session: Session, order_line_id: int) -> Order_line | None:
    stmt = select(Order_line).where(Order_line.id == order_line_id)
    order_line = session.execute(stmt).scalar_one_or_none()
    
    return order_line

def get_all_order_lines_by_order_id(session: Session, order_id: int) -> list[Order_line]:
    stmt = select(Order_line).where(Order_line.order_id == order_id)
    order_lines = session.execute(stmt).scalars().all()
    
    return order_lines

def update_order_line_quantity(session: Session, order_line_id: int, quantity: int) -> Order_line:
    stmt = select(Order_line).where(Order_line.id == order_line_id)
    order_line = session.execute(stmt).scalar_one_or_none()
    
    if order_line is None:
        raise ValueError("Order line not found in the database.")
    
    order_line.quantity = quantity
    session.commit()
    session.refresh(order_line)
    
    return order_line

def delete_order_line(session: Session, order_line_id: int) -> None:
    stmt = select(Order_line).where(Order_line.id == order_line_id)
    order_line = session.execute(stmt).scalar_one_or_none()
    
    if order_line is None:
        raise ValueError("Order line not found in the database.")
    
    session.delete(order_line)
    session.commit()

