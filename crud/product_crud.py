from decimal import Decimal
from typing import List
from models.product import Product
from sqlalchemy import select
from sqlalchemy.orm import Session



def create_product(session: Session, sku: str, name: str, unit_price_ex_vat: Decimal, default_vat_rate: Decimal) -> Product:
    product = Product(sku=sku, name=name, unit_price_ex_vat=unit_price_ex_vat, default_vat_rate=default_vat_rate)
    
    session.add(product)
    session.commit()
    session.refresh(product)
    
    return product

def get_product_by_id(session: Session, product_id: int) -> Product | None:
    stmt = select(Product).where(Product.id == product_id)
    product = session.execute(stmt).scalar_one_or_none()
    
    return product

def get_product_by_sku(session: Session, sku: str) -> Product | None:
    stmt = select(Product).where(Product.sku == sku)
    product = session.execute(stmt).scalar_one_or_none()
    
    return product

def get_all_products(session: Session) -> List[Product]:
    stmt = select(Product)
    products = session.execute(stmt).scalars().all()
    
    return products

def update_product(session: Session, product_id: int, **kwargs) -> Product:
    stmt = select(Product).where(Product.id == product_id)
    product = session.execute(stmt).scalar_one_or_none()
    
    if product is None:
        raise ValueError("Product not found in the database.")
    
    for key, value in kwargs.items():
        if hasattr(product, key) and value is not None:
            setattr(product, key, value)
            
    session.commit()
    session.refresh(product)
    
    return product

def delete_product(session: Session, product_id: int) -> None:
    stmt = select(Product).where(Product.id == product_id)
    product = session.execute(stmt).scalar_one_or_none()
    
    if product is None:
         raise ValueError("Product not found in the database.")
    
    session.delete(product)
    session.commit()

            