from database.database import Base
from sqlalchemy import CheckConstraint, ForeignKey, Integer, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from models.product import Product
    from models.warehouse import Warehouse



class Stock(Base):
    __tablename__ = "stocks"

    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="CASCADE"),
        nullable=False
    )

    product_id : Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), 
        nullable=False
    )

    quantity: Mapped[int] = mapped_column(Integer, 
        nullable=False
    )



    product: Mapped["Product"] = relationship("Product", 
        back_populates="stocks",
        init=False
    )

    warehouse: Mapped["Warehouse"] = relationship("Warehouse", 
        back_populates="stocks",
        init=False 
    )



    __table_args__ = (
        # Composite primary key on warehouse_id and product_id
        PrimaryKeyConstraint('warehouse_id', 'product_id'),
        CheckConstraint('quantity >= 0', name='check_quantity_non_negative'),
    )