from models.stock import Stock
from sqlalchemy import select
from sqlalchemy.orm import Session



def create_stock(session: Session, product_id: int, warehouse_id: int, quantity: int) -> Stock:
    stock = Stock(product_id=product_id, warehouse_id=warehouse_id, quantity=quantity)
    
    session.add(stock)
    session.flush()
    
    return stock

def get_stock_by_warehouse_id_product_id(session: Session, warehouse_id: int, product_id: int) -> Stock | None:
    stmt = select(Stock).where(Stock.warehouse_id == warehouse_id, Stock.product_id == product_id)
    stock = session.execute(stmt).scalar_one_or_none()
    
    return stock

def get_all_stock_by_warehouse(session: Session, warehouse_id: int) -> list[Stock]:
    stmt = select(Stock).where(Stock.warehouse_id == warehouse_id)
    stocks = session.execute(stmt).scalars().all()
    
    return stocks

def update_stock_quantity(session: Session, warehouse_id: int, product_id: int, quantity: int) -> Stock:
    stmt = select(Stock).where(Stock.warehouse_id == warehouse_id, Stock.product_id == product_id)
    stock = session.execute(stmt).scalar_one_or_none()
    
    if stock is None:
        raise ValueError("Stock not found in the database.")
    
    stock.quantity = quantity
    session.flush()
    
    return stock