from models.warehouse import Warehouse, WarehouseTypeEnum
from sqlalchemy import select
from sqlalchemy.orm import Session


def create_warehouse(session: Session, name: str, city: str, warehouse_type: WarehouseTypeEnum, max_capacity: int) -> Warehouse:
    warehouse = Warehouse(name = name, city = city, warehouse_type = warehouse_type, max_capacity = max_capacity)
    
    session.add(warehouse)
    session.commit()
    session.refresh(warehouse)
    
    return warehouse

def get_warehouse_by_id(session: Session, warehouse_id: int) -> Warehouse | None:
    stmt = select(Warehouse).where(Warehouse.id == warehouse_id)
    warehouse = session.execute(stmt).scalar_one_or_none()
    
    return warehouse

def get_warehouse_by_name(session: Session, name: str) -> Warehouse | None:
    stmt = select(Warehouse).where(Warehouse.name == name)
    warehouse = session.execute(stmt).scalar_one_or_none()
    
    return warehouse

def get_all_warehouses(session: Session) -> list[Warehouse]:
    stmt = select(Warehouse)
    warehouses = session.execute(stmt).scalars().all()
    
    return warehouses

def update_warehouse(session: Session, warehouse_id: int, **kwargs) -> Warehouse:
    stmt = select(Warehouse).where(Warehouse.id == warehouse_id)
    warehouse = session.execute(stmt).scalar_one_or_none()
    
    if warehouse is None:
        raise ValueError("Warehouse not found in the database.")
    
    for key, value in kwargs.items():
        if hasattr(warehouse, key) and value is not None:
            setattr(warehouse, key, value)
            
    session.commit()
    session.refresh(warehouse)
    
    return warehouse

def delete_warehouse(session: Session, warehouse_id: int) -> None:
    stmt = select(Warehouse).where(Warehouse.id == warehouse_id)
    warehouse = session.execute(stmt).scalar_one_or_none()
    
    if warehouse is None:
        raise ValueError("Warehouse not found in the database.")
    
    session.delete(warehouse)
    session.commit()
    
