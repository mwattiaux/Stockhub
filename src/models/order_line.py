from decimal import Decimal

from database.database import Base
from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.order import Order
    from models.product import Product

class Order_line(Base):
    __tablename__ = "order_lines"

    id: Mapped[int] = mapped_column(primary_key=True, 
        init=False
    )

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False
    )

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"),

        nullable=False
    )

    quantity: Mapped[int] = mapped_column(Integer, 
        nullable=False
    )

    historical_price_ex_vat: Mapped[Decimal] = mapped_column(Numeric(10, 2),
        nullable=False
    )



    order: Mapped["Order"] = relationship("Order",
        back_populates="order_lines",
        init=False
    )

    product: Mapped["Product"] = relationship("Product",
        back_populates="order_lines",
        init=False
    )



    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_quantity_positive'),
        CheckConstraint('historical_price_ex_vat >= 0', name='check_historical_price_positive'),
    )