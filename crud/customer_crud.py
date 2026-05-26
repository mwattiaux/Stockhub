from models.customer import Customer
from sqlalchemy import select
from sqlalchemy.orm import Session



def create_customer(session: Session, first_name: str, last_name: str, address: str, email: str) -> Customer:
    customer = Customer(first_name=first_name, last_name=last_name, address=address, email=email)
    
    session.add(customer)
    session.flush()
    
    return customer

def get_customer_by_id(session: Session, customer_id: int) -> Customer | None:
    stmt = select(Customer).where(Customer.id == customer_id)
    customer = session.execute(stmt).scalar_one_or_none()
    
    return customer

def get_customer_by_email(session: Session, email: str) -> Customer | None:
    stmt = select(Customer).where(Customer.email == email)
    customer = session.execute(stmt).scalar_one_or_none()
    
    return customer

def get_customer_by_name_and_address(session: Session, first_name: str, last_name: str, address: str) -> Customer | None:
    stmt = select(Customer).where(
        Customer.first_name == first_name,
        Customer.last_name == last_name,
        Customer.address == address
    )
    customer = session.execute(stmt).scalar_one_or_none()
    
    return customer

def get_all_customers(session: Session) -> list[Customer]:
    stmt = select(Customer)
    customers = session.execute(stmt).scalars().all()
    
    return customers

def get_customers_filtered(session: Session, first_name: str | None = None, last_name: str | None = None, email: str | None = None) -> list[Customer]:
    stmt = select(Customer)
    
    if first_name is not None:
        stmt = stmt.where(Customer.first_name.ilike(f"%{first_name}%"))
        
    if last_name is not None:
        stmt = stmt.where(Customer.last_name.ilike(f"%{last_name}%"))
        
    if email is not None:
        stmt = stmt.where(Customer.email.ilike(f"%{email}%"))
    
    customers = session.execute(stmt).scalars().all()
    
    return customers

def update_customer(session: Session, customer_id: int, **kwargs) -> Customer:
    stmt = select(Customer).where(Customer.id == customer_id)
    customer = session.execute(stmt).scalar_one_or_none()
    
    if customer is None:
        raise ValueError("Customer not found in the database.")
    
    for key, value in kwargs.items():
        if hasattr(customer, key) and value is not None:
            setattr(customer, key, value)
            
    session.flush()
    
    return customer

def delete_customer(session: Session, customer_id: int) -> None:
    stmt = select(Customer).where(Customer.id == customer_id)
    customer = session.execute(stmt).scalar_one_or_none()
    
    if customer is None:
        raise ValueError("Customer not found in the database.")
    
    session.delete(customer)
    session.commit()
    