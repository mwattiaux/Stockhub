import re  # Import the built-in regular expression module
from sqlalchemy.orm import Session
from models.warehouse import Warehouse, WarehouseTypeEnum
from models.customer import Customer
from crud.warehouse_crud import create_warehouse, get_warehouse_by_name, get_warehouse_by_id, update_warehouse
from crud.customer_crud import create_customer, get_customer_by_email, get_customer_by_id, update_customer
from crud.stock_crud import get_all_stock_by_warehouse

# Regular Expression pattern for standard email validation
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

# ==========================================
# LOGISTICS BUSINESS LOGIC (Warehouses)
# ==========================================

def register_warehouse(session: Session, name: str, city: str, warehouse_type: WarehouseTypeEnum, max_capacity: int) -> Warehouse:
    """
    Business Logic: Orchestrates the creation of new physical warehouses.
    Enforces logistical initialization guardrails.
    """
    # Business Rule: Maximum capacity must be strictly greater than 0
    if max_capacity <= 0:
        raise ValueError("Business Rule Violation: Maximum capacity must be strictly greater than 0.")
        
    name = name.strip()
    city = city.strip()
    if not name or not city:
        raise ValueError("Business Logic Error: Warehouse name and city cannot be empty strings.")

    if get_warehouse_by_name(session, name):
        raise ValueError(f"Business Logic Error: A warehouse named '{name}' already exists.")

    return create_warehouse(
        session=session,
        name=name,
        city=city,
        warehouse_type=warehouse_type,
        max_capacity=max_capacity
    )

def modify_warehouse(session: Session, warehouse_id: int, name: str | None = None, city: str | None = None, max_capacity: int | None = None) -> Warehouse:
    """
    Business Logic: Handles updates to warehouse configurations.
    Protects physical data consistency by preventing capacity down-sizing below active stock.
    """
    warehouse = get_warehouse_by_id(session, warehouse_id)
    if not warehouse:
        raise ValueError("Business Logic Error: Warehouse not found.")

    if max_capacity is not None:
        # Business Rule Reinforcement
        if max_capacity <= 0:
            raise ValueError("Business Logic Error: Maximum capacity must be strictly greater than 0.")
        
        # Business Logic: Physical consistency check. Cannot shrink max capacity 
        # below the actual amount of items currently stored inside the warehouse.
        current_total_items = sum(stock.quantity for stock in get_all_stock_by_warehouse(session, warehouse_id))
        if max_capacity < current_total_items:
            raise ValueError(
                f"Business Logic Error: Cannot reduce maximum capacity to {max_capacity}. "
                f"Warehouse currently holds {current_total_items} items."
            )

    return update_warehouse(
        session=session,
        warehouse_id=warehouse_id,
        name=name,
        city=city,
        max_capacity=max_capacity
    )

# ==========================================
# CRM BUSINESS LOGIC (Customers)
# ==========================================

def register_customer(session: Session, first_name: str, last_name: str, address: str, email: str) -> Customer:
    """
    Business Logic: Validates CRM / Customer record enrollment data.
    Ensures mandatory database fields are sanitized and structurally accurate using a Regex pattern.
    """
    first_name = first_name.strip()
    last_name = last_name.strip()
    address = address.strip()
    email = email.strip().lower()

    # Business Logic: Sanity checks to catch empty strings before database insertion (NN attributes from image_4e9914.png)
    if not first_name or not last_name or not address or not email:
        raise ValueError("Business Logic Error: All customer fields (First Name, Last Name, Address, Email) are mandatory.")

    # Business Logic: Strict structural validation using the Regular Expression pattern
    if not re.match(EMAIL_REGEX, email):
        raise ValueError(f"Business Logic Error: The email address '{email}' is not formatted correctly.")

    # Business Logic: Prevent duplicate emails to keep customer identity integrity
    if get_customer_by_email(session, email):
        raise ValueError(f"Business Logic Error: A customer with email '{email}' already exists.")

    return create_customer(
        session=session,
        first_name=first_name,
        last_name=last_name,
        address=address,
        email=email
    )

def modify_customer(session: Session, customer_id: int, first_name: str | None = None, last_name: str | None = None, address: str | None = None, email: str | None = None) -> Customer:
    """
    Business Logic: Manages updates to existing customer profiles.
    Enforces the same validation guardrails (Regex, Uniqueness, Not Null) upon modifications.
    """
    customer = get_customer_by_id(session, customer_id)
    if not customer:
        raise ValueError("Business Logic Error: Customer not found.")

    # Sanitize and validate inputs if they are provided in the update request
    if first_name is not None:
        first_name = first_name.strip()
        if not first_name:
            raise ValueError("Business Logic Error: First name cannot be updated to an empty string.")

    if last_name is not None:
        last_name = last_name.strip()
        if not last_name:
            raise ValueError("Business Logic Error: Last name cannot be updated to an empty string.")

    if address is not None:
        address = address.strip()
        if not address:
            raise ValueError("Business Logic Error: Address cannot be updated to an empty string.")

    if email is not None:
        email = email.strip().lower()
        if not email:
            raise ValueError("Business Logic Error: Email cannot be updated to an empty string.")
        
        # Business Logic Reinforcement: Strict structural check on new email
        if not re.match(EMAIL_REGEX, email):
            raise ValueError(f"Business Logic Error: The new email address '{email}' is not formatted correctly.")
        
        # Business Logic Reinforcement: Ensure the new email doesn't collide with another customer
        existing_owner = get_customer_by_email(session, email)
        if existing_owner and existing_owner.id != customer_id:
            raise ValueError(f"Business Logic Error: Another customer is already registered with the email '{email}'.")

    return update_customer(
        session=session,
        customer_id=customer_id,
        first_name=first_name,
        last_name=last_name,
        address=address,
        email=email
    )