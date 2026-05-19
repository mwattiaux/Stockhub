from database.database import Base
from datetime import datetime
from sqlalchemy import DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True, 
        init=False
    )

    first_name: Mapped[str] = mapped_column(String(100),
        nullable=False
    )

    last_name: Mapped[str] = mapped_column(String(100), 
        nullable=False
    )

    address: Mapped[str] = mapped_column(String(200), 
        nullable=False
    )

    email: Mapped[str] = mapped_column(String(100), 
        unique=True, 
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, 
        nullable=False,
        default=func.now(timezone=True),
        init = False
    )



    __table_args__ = (
        UniqueConstraint('first_name', 'last_name', 'address', name='_user_address_uc'),
    )