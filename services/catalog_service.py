from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models.product import Product
from crud.product_crud import create_product, get_product_by_sku, get_product_by_id, update_product

def register_product(session: Session, sku: str, name: str, unit_price_ex_vat: Decimal, default_vat_rate: Decimal | None = None) -> Product:
    # 1. Validations métier (Pas besoin de rollback ici, on n'a rien touché à la DB)
    if unit_price_ex_vat <= Decimal("0.00"):
        raise ValueError("Business Logic Error: Unit price ex-VAT must be strictly greater than 0.")
    
    if default_vat_rate is None:
        default_vat_rate = Decimal("21.00")
    elif default_vat_rate < Decimal("0.00"):
        raise ValueError("Business Logic Error: VAT rate cannot be negative.")
        
    if get_product_by_sku(session, sku):
        raise ValueError(f"Business Logic Error: Product SKU '{sku}' already exists.")
        
    # 2. Tentative de persistance avec gestion de transaction
    try:
        product = create_product(
            session=session,
            sku=sku,
            name=name,
            unit_price_ex_vat=unit_price_ex_vat,
            default_vat_rate=default_vat_rate
        )
        session.commit() # Succès
        return product
    except SQLAlchemyError as e:
        session.rollback() # Annulation en cas d'erreur DB (UniqueViolation, etc.)
        raise RuntimeError(f"Database error during product registration: {e}")

def modify_product(session: Session, product_id: int, name: str | None = None, unit_price_ex_vat: Decimal | None = None, default_vat_rate: Decimal | None = None) -> Product:
    product = get_product_by_id(session, product_id)
    if not product:
        raise ValueError("Business Logic Error: Product not found.")

    if unit_price_ex_vat is not None and unit_price_ex_vat <= Decimal("0.00"):
        raise ValueError("Business Logic Error: Updated unit price ex-VAT must be strictly greater than 0.")

    if default_vat_rate is not None and default_vat_rate < Decimal("0.00"):
        raise ValueError("Business Logic Error: Updated VAT rate cannot be negative.")

    try:
        updated_product = update_product(
            session=session,
            product_id=product_id,
            name=name,
            unit_price_ex_vat=unit_price_ex_vat,
            default_vat_rate=default_vat_rate
        )
        session.commit()
        return updated_product
    except SQLAlchemyError as e:
        session.rollback()
        raise RuntimeError(f"Database error during product update: {e}")