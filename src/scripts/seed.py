import os
import sys
from decimal import Decimal
from sqlalchemy.orm import Session

# Configuration du chemin pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from database.database import engine, Base  # <--- Import Base here
from models.warehouse import Warehouse
from models.product import Product
from models.customer import Customer
from models.order import Order, OrderStatusEnum
from models.order_line import Order_line
from models.stock import Stock
from models.invoice import Invoice, InvoiceStatusEnum
from models.stock_movement import Stock_movement, MovementTypeEnum

def seed_data():
    # 0. Création des tables si elles n'existent pas
    Base.metadata.drop_all(engine)  # Supprimer les tables existantes pour repartir à zéro
    Base.metadata.create_all(engine)
    
    with Session(engine) as session:
        
        # 1. Entrepôts
        w1 = Warehouse(name="Central", city="Bruxelles", warehouse_type="Central", max_capacity=1000)
        session.add(w1)
        session.flush()

        # 2. Produits
        p1 = Product(sku="IPH-16-BLK", name="iPhone 16 Black", unit_price_ex_vat=Decimal("800.00"), default_vat_rate=Decimal("21.00"))
        p2 = Product(sku="MAC-AIR-13", name="MacBook Air 13", unit_price_ex_vat=Decimal("1200.00"), default_vat_rate=Decimal("21.00"))
        session.add_all([p1, p2])
        session.flush()

        # 3. Client
        c1 = Customer(first_name="Maxime", last_name="Wattiaux", address="Rue de la Paix 1, 1000 Bruxelles", email="maxime@example.com")
        session.add(c1)
        session.flush()
        print(w1.id, c1.id)
        
        ida = w1.id
        idb = c1.id

        # 4. Commande
        o1 = Order(customer_id=idb, warehouse_id=ida, status=OrderStatusEnum.DRAFT)
        session.add(o1)
        session.flush()

        # 5. Lignes de commande
        ol1 = Order_line(order=o1, product=p1, quantity=1, historical_price_ex_vat=Decimal("800.00"))
        session.add(ol1)

        # 6. Stock
        s1 = Stock(warehouse=w1, product=p1, quantity=50)
        session.add(s1)

        # 7. Facture
        inv1 = Invoice(
            order=o1, 
            total_ex_vat=Decimal("800.00"), 
            vat_amount=Decimal("168.00"), 
            total_inc_vat=Decimal("968.00"), 
            status=InvoiceStatusEnum.VALIDATED
        )
        session.add(inv1)

        # 8. Mouvement de stock
        sm1 = Stock_movement(
            product=p1,
            dest_warehouse=w1,
            quantity=50,
            movement_type=MovementTypeEnum.SUPPLIER_RECEPTION,
            reason="Initial stock intake"
        )
        session.add(sm1)

        session.commit()
        print("Base de données peuplée avec succès !")

if __name__ == "__main__":
    seed_data()