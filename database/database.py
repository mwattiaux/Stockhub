import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass, sessionmaker

class Base(DeclarativeBase, MappedAsDataclass):
    pass

# FORCE IMPORT de TOUS les modèles ici. 
# C'est la seule façon de garantir que SQLAlchemy connaît 
# l'existence de toutes les classes avant le premier CRUD.
from models.product import Product
from models.order import Order
from models.order_line import Order_line
from models.customer import Customer
from models.stock import Stock
from models.stock_movement import Stock_movement
from models.warehouse import Warehouse
from models.invoice import Invoice

load_dotenv()

DATABASE_URL = (
    f"postgresql+psycopg://"
    f"{os.getenv('POSTGRES_USER')}:"
    f"{os.getenv('POSTGRES_PASSWORD')}@"
    f"{os.getenv('POSTGRES_HOST')}:"
    f"{os.getenv('POSTGRES_PORT')}/"
    f"{os.getenv('POSTGRES_DB')}"
)

engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(bind=engine)