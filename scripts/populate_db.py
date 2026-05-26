import os
import random
import sys
from decimal import Decimal
from faker import Faker
from sqlalchemy.orm import Session

# Configuration du chemin pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from database.database import SessionLocal, engine, Base  # <--- Import Base here
from models.warehouse import Warehouse, WarehouseTypeEnum
from models.product import Product
from models.customer import Customer
from models.order import Order, OrderStatusEnum
from models.order_line import Order_line
from models.stock import Stock
from models.invoice import Invoice, InvoiceStatusEnum
from models.stock_movement import Stock_movement, MovementTypeEnum

from services.catalog_service import register_product
from services.crm_and_logistics_service import register_customer, register_warehouse

fake = Faker('fr_FR')

def clean_database():
    print("🧹 Nettoyage de la base de données...")
    # Supprime toutes les tables et recrée-les pour un état parfaitement propre
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✨ Base de données réinitialisée.")

def populate():
    session = SessionLocal()
    
    # 1. Nettoyage initial
    clean_database()
    
    print("--- Peuplement de la base de données ---")

    # 2. Génération de 5 Entrepôts
    try:
        register_warehouse(session, "Central Hub", "Charleroi", WarehouseTypeEnum.CENTRAL, 5000)
        for _ in range(4):
            capacity = random.randint(5, 20) * 100
            register_warehouse(
                session=session,
                name=f"Dépôt {fake.city()}",
                city=fake.city(),
                warehouse_type=WarehouseTypeEnum.PROXIMITY,
                max_capacity=capacity
            )
        print("✅ 5 entrepôts générés.")
    except Exception as e:
        print(f"⚠️ Erreur entrepôts : {e}")

    # 3. Génération de 15 Produits
    try:
        tva_choices = [Decimal("6.0"), Decimal("12.0"), Decimal("21.0")]
        for _ in range(15):
            register_product(
                session=session,
                sku=fake.unique.bothify(text='PROD-####'),
                name=fake.catch_phrase(),
                unit_price_ex_vat=Decimal(str(random.randint(10, 500))),
                default_vat_rate=random.choice(tva_choices)
            )
        print("✅ 15 produits générés.")
    except Exception as e:
        print(f"⚠️ Erreur produits : {e}")

    # 4. Génération de 15 Clients
    try:
        for _ in range(15):
            register_customer(
                session=session,
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                address=fake.address().replace('\n', ', '),
                email=fake.unique.email()
            )
        print("✅ 15 clients générés.")
    except Exception as e:
        print(f"⚠️ Erreur clients : {e}")

    session.close()
    print("--- Peuplement terminé avec succès ! ---")

if __name__ == "__main__":
    populate()