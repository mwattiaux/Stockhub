from database.database import Base
from datetime import datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.order import Order



class invoice_status_enum(Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    VALIDATED = "VALIDATED"

class Invoice(Base):
    __tablename__ = "invoices"
    
    id: Mapped[int] = mapped_column(primary_key=True,
        init=False
    )

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False
    )

    total_ex_vat: Mapped[Decimal] = mapped_column(Numeric(10, 2),
        nullable=False
    )

    vat_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2),
        nullable=False
    )

    total_inc_vat: Mapped[Decimal] = mapped_column(Numeric(10, 2),
        nullable=False
    )

    status: Mapped[invoice_status_enum] = mapped_column(name="invoice_status_enum",
        default=invoice_status_enum.PENDING_PAYMENT,
        nullable=False
    )

    invoice_date: Mapped[datetime] = mapped_column(DateTime,
        default=func.now(timezone=True),
        nullable=False,
        init=False
    )



    order: Mapped["Order"] = relationship("Order",
        back_populates="invoice",
        default=None,
        init=False
    )