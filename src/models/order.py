from database.database import Base
from datetime import datetime
from enum import Enum
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.customer import Customer
    from models.warehouse import Warehouse
    


class OrderStatusEnum(Enum):
    # Draft, Validated, Cancelled
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    CANCELLED = "CANCELLED"

class Order(Base):
    __tablename__ = "orders"
    
    id: Mapped[int] = mapped_column(primary_key=True, 
        init=False
    )

    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False
    )

    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False
    )

    order_date: Mapped[datetime] = mapped_column(DateTime,
        default=func.now(timezone=True),
        nullable=False,
        init=False
    )

    status: Mapped[OrderStatusEnum] = mapped_column(name="order_status_enum",
        default=OrderStatusEnum.DRAFT,
        nullable=False
    )



    customer: Mapped["Customer"] = relationship("Customer",
        back_populates="orders",
        default=None,
        init=False
    )

    warehouse: Mapped["Warehouse"] = relationship("Warehouse",
        back_populates="orders",
        default=None,
        init=False  
    )