from database.database import Base
from enum import Enum
from sqlalchemy import CheckConstraint, Enum as SQLEnum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.order import Order
    from models.stock import Stock 
    from models.stock_movement import Stock_movement



class WarehouseTypeEnum(Enum):
    CENTRAL = "CENTRAL"
    PROXIMITY = "PROXIMITY"
    HUB = "HUB"

class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(primary_key=True, 
        init=False
    )

    name: Mapped[str] = mapped_column(String(100),
        unique=True,
        nullable=False
    )

    city: Mapped[str] = mapped_column(String(100), 
        nullable=False
    )

    warehouse_type: Mapped[WarehouseTypeEnum] = mapped_column(SQLEnum(WarehouseTypeEnum, name="warehouse_type_enum"), 
        nullable=False
    )

    max_capacity: Mapped[int] = mapped_column(Integer, 
        nullable=False
    )



    incoming_stock_movements: Mapped[list["Stock_movement"]] = relationship("Stock_movement",
        foreign_keys="[Stock_movement.dest_warehouse_id]",
        back_populates="dest_warehouse",
        default_factory=list,
        init=False
    )

    outgoing_stock_movements: Mapped[list["Stock_movement"]] = relationship("Stock_movement",
        foreign_keys="[Stock_movement.src_warehouse_id]",
        back_populates="src_warehouse",
        default_factory=list,
        init=False
    )

    orders: Mapped[list["Order"]] = relationship("Order",
        back_populates="warehouse",
        default_factory=list,
        init=False
    )    

    stocks: Mapped[list["Stock"]] = relationship("Stock", 
        back_populates="warehouse",
        cascade="all, delete-orphan",
        default_factory=list,
        init=False
    )



    __table_args__ = (
        CheckConstraint('max_capacity > 0', name='check_max_capacity_positive'),
    )