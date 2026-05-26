from database.database import Base
from datetime import datetime
from enum import Enum
from sqlalchemy import CheckConstraint, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

# if TYPE_CHECKING:
# from models.product import Product
# from models.warehouse import Warehouse



class MovementTypeEnum(Enum):
    SALE = "SALE"
    TRANSFER = "TRANSFER"
    SUPPLIER_RECEPTION = "SUPPLIER_RECEPTION"
    ADJUSTMENT = "ADJUSTMENT"

class Stock_movement(Base):
    __tablename__ = "stock_movements"

    id: Mapped[int] = mapped_column(primary_key=True, 
        init=False
    )

    product_id : Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), 
        nullable=False
    )
    
    quantity: Mapped[int] = mapped_column(Integer, 
        nullable=False
    )

    movement_type: Mapped[MovementTypeEnum] = mapped_column(SQLEnum(MovementTypeEnum, name="stock_movement_type_enum"),
        nullable=False
    )

    src_warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"), 
        nullable=True,
        default=None
    )

    dest_warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"), 
        nullable=True,
        default=None
    )

    reason: Mapped[str] = mapped_column(String(255),
        nullable=True,
        default=None
    )

    movement_date: Mapped[datetime] = mapped_column(DateTime, 
        nullable=False, 
        default=func.now(timezone=True),
        init=False
    )



    product: Mapped["Product"] = relationship("Product", 
        back_populates="stock_movements",
        init=False
    )

    src_warehouse: Mapped["Warehouse | None"] = relationship("Warehouse", 
        foreign_keys=[src_warehouse_id],
        back_populates="outgoing_stock_movements",
        default=None,
        init=False
    )

    dest_warehouse: Mapped["Warehouse | None"] = relationship("Warehouse", 
        foreign_keys=[dest_warehouse_id],
        back_populates="incoming_stock_movements",
        default=None,
        init=False
    )   


    __table_args__ = (
            CheckConstraint('quantity > 0', name='check_quantity_positive'),
        )