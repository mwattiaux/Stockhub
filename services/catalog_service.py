from decimal import Decimal
from sqlalchemy.orm import Session
from models.product import Product
from crud.product_crud import create_product, get_product_by_sku, get_product_by_id, update_product

def register_product(session: Session, sku: str, name: str, unit_price_ex_vat: Decimal, default_vat_rate: Decimal | None = None) -> Product:
    """
    Business Logic: Handles the enrollment of new products into the catalog.
    Validates core pricing and taxation business rules before persistence.
    """
    # Business Rule: The unit price ex-VAT must be strictly greater than 0
    if unit_price_ex_vat <= Decimal("0.00"):
        raise ValueError("Business Logic Error: Unit price ex-VAT must be strictly greater than 0.")
        
    # Business Rule: Default VAT rate is set to 21.00% if not specified (Belgian Standard)
    if default_vat_rate is None:
        default_vat_rate = Decimal("21.00")
    elif default_vat_rate < Decimal("0.00"):
        raise ValueError("Business Logic Error: VAT rate cannot be negative.")
        
    # Business Logic: Integrity check to prevent duplicate SKUs before hitting DB constraints
    existing = get_product_by_sku(session, sku)
    if existing:
        raise ValueError(f"Business Logic Error: Product SKU '{sku}' already exists in the catalog.")
        
    return create_product(
        session=session,
        sku=sku,
        name=name,
        unit_price_ex_vat=unit_price_ex_vat,
        default_vat_rate=default_vat_rate
    )

def modify_product(session: Session, product_id: int, name: str | None = None, unit_price_ex_vat: Decimal | None = None, default_vat_rate: Decimal | None = None) -> Product:
    """
    Business Logic: Manages updates to existing product catalog records.
    Ensures that updated values do not bypass core financial constraints.
    """
    product = get_product_by_id(session, product_id)
    if not product:
        raise ValueError("Business Logic Error: Product not found.")

    # Business Rule Reinforcement: Re-validate price threshold if an update is requested
    if unit_price_ex_vat is not None and unit_price_ex_vat <= Decimal("0.00"):
        raise ValueError("Business Logic Error: Updated unit price ex-VAT must be strictly greater than 0.")

    # Business Rule Reinforcement: Re-validate VAT rate constraints
    if default_vat_rate is not None and default_vat_rate < Decimal("0.00"):
        raise ValueError("Business Logic Error: Updated VAT rate cannot be negative.")

    return update_product(
        session=session,
        product_id=product_id,
        name=name,
        unit_price_ex_vat=unit_price_ex_vat,
        default_vat_rate=default_vat_rate
    )