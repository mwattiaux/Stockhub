import re
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models.warehouse import Warehouse, WarehouseTypeEnum
from models.customer import Customer
from crud.warehouse_crud import create_warehouse, get_warehouse_by_name, get_warehouse_by_id, update_warehouse
from crud.customer_crud import create_customer, get_customer_by_email, get_customer_by_id, update_customer
from crud.stock_crud import get_all_stock_by_warehouse

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

# ==========================================
# LOGISTICS BUSINESS LOGIC
# ==========================================

def register_warehouse(session: Session, name: str, city: str, warehouse_type: WarehouseTypeEnum, max_capacity: int) -> Warehouse:
    # 1. Validation métier
    if max_capacity <= 0:
        raise ValueError("Business Rule Violation: Maximum capacity must be strictly greater than 0.")
    name, city = name.strip(), city.strip()
    if not name or not city:
        raise ValueError("Business Logic Error: Warehouse name and city cannot be empty.")
    if get_warehouse_by_name(session, name):
        raise ValueError(f"Business Logic Error: A warehouse named '{name}' already exists.")

    # 2. Persistance sécurisée
    try:
        warehouse = create_warehouse(session, name=name, city=city, warehouse_type=warehouse_type, max_capacity=max_capacity)
        session.commit()
        return warehouse
    except SQLAlchemyError as e:
        session.rollback()
        raise RuntimeError(f"Database error during warehouse registration: {e}")

def modify_warehouse(session: Session, warehouse_id: int, name: str | None = None, city: str | None = None, max_capacity: int | None = None) -> Warehouse:
    warehouse = get_warehouse_by_id(session, warehouse_id)
    if not warehouse:
        raise ValueError("Business Logic Error: Warehouse not found.")

    if max_capacity is not None:
        if max_capacity <= 0:
            raise ValueError("Business Logic Error: Maximum capacity must be strictly greater than 0.")
        current_total_items = sum(stock.quantity for stock in get_all_stock_by_warehouse(session, warehouse_id))
        if max_capacity < current_total_items:
            raise ValueError(f"Business Logic Error: Cannot reduce capacity below current stock ({current_total_items}).")

    try:
        updated = update_warehouse(session, warehouse_id=warehouse_id, name=name, city=city, max_capacity=max_capacity)
        session.commit()
        return updated
    except SQLAlchemyError as e:
        session.rollback()
        raise RuntimeError(f"Database error during warehouse update: {e}")

# ==========================================
# CRM BUSINESS LOGIC
# ==========================================

def register_customer(session: Session, first_name: str, last_name: str, address: str, email: str) -> Customer:
    # 1. Validation métier
    first_name, last_name, address = first_name.strip(), last_name.strip(), address.strip()
    email = email.strip().lower()
    if not first_name or not last_name or not address or not email:
        raise ValueError("Business Logic Error: All customer fields are mandatory.")
    if not re.match(EMAIL_REGEX, email):
        raise ValueError(f"Business Logic Error: The email address '{email}' is not formatted correctly.")
    if get_customer_by_email(session, email):
        raise ValueError(f"Business Logic Error: A customer with email '{email}' already exists.")

    # 2. Persistance sécurisée
    try:
        customer = create_customer(session, first_name=first_name, last_name=last_name, address=address, email=email)
        session.commit()
        return customer
    except SQLAlchemyError as e:
        session.rollback()
        raise RuntimeError(f"Database error during customer registration: {e}")

def modify_customer(session: Session, customer_id: int, first_name: str | None = None, last_name: str | None = None, address: str | None = None, email: str | None = None) -> Customer:
    customer = get_customer_by_id(session, customer_id)
    if not customer:
        raise ValueError("Business Logic Error: Customer not found.")

    # Validation métier
    if first_name is not None and not first_name.strip(): raise ValueError("First name empty.")
    if last_name is not None and not last_name.strip(): raise ValueError("Last name empty.")
    if address is not None and not address.strip(): raise ValueError("Address empty.")
    if email is not None:
        email = email.strip().lower()
        if not re.match(EMAIL_REGEX, email): raise ValueError("Invalid email format.")
        existing = get_customer_by_email(session, email)
        if existing and existing.id != customer_id: raise ValueError("Email already in use.")

    # Persistance sécurisée
    try:
        updated = update_customer(session, customer_id=customer_id, first_name=first_name, last_name=last_name, address=address, email=email)
        session.commit()
        return updated
    except SQLAlchemyError as e:
        session.rollback()
        raise RuntimeError(f"Database error during customer update: {e}")