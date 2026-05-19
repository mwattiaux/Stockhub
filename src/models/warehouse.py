from database.database import Base
from enum import Enum
from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

class WarehouseTypeEnum(Enum):
    CENTRAL = "Central"
    PROXIMITY = "Proximity"
    HUB = "Hub"

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

    warehouse_type: Mapped[WarehouseTypeEnum] = mapped_column(name="warehouse_type_enum", 
        nullable=False
    )

    max_capacity: Mapped[int] = mapped_column(Integer, 
        nullable=False
    )



    __table_args__ = (
        CheckConstraint('max_capacity > 0', name='check_max_capacity_positive'),
    )