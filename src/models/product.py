# Register a Product
# A product consists of:

# SKU (Unique reference, e.g., IPH-16-BLK)
# Name
# Unit Price Ex-VAT (Before taxes)
# Default VAT Rate
# Business Rules:

# The unit price ex-VAT must be strictly greater than 0.
# The default VAT rate is set to 21.00% by default (Belgian Standard).

from database.database import Base
from decimal import Decimal
from sqlalchemy import CheckConstraint, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from models.order_line import Order_line
    from models.stock import Stock
    from models.stock_movement import Stock_movement
    


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, 
        init=False
    )

    sku: Mapped[str] = mapped_column(
        String(50), 
        unique=True, 
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(100), 
        nullable=False
    )

    unit_price_ex_vat: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), 
        nullable=False
    )

    default_vat_rate: Mapped[Decimal] = mapped_column(
        Numeric(4, 2), 
        nullable=False, 
        default=21.00
    )



    order_lines: Mapped[list["Order_line"]] = relationship("Order_line",
        back_populates="product",
        default_factory=list,
        init=False
    )  

    stocks: Mapped[list["Stock"]] = relationship("Stock", 
        back_populates="product",
        default_factory=list,
        init=False
    )

    stock_movements: Mapped[list["Stock_movement"]] = relationship("Stock_movement", 
        back_populates="product",
        default_factory=list,
        init=False
    )



    __table_args__ = (
        CheckConstraint('unit_price_ex_vat > 0', name='check_unit_price_positive'),
    )