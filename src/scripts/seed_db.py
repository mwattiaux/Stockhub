import os
import random
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
    with Session(engine) as session:
        # --- 1. CLEANUP OF TRANSACTIONAL DATA ---
        # Note: We delete transactional data to recreate fresh flows every time
        session.query(Stock_movement).delete()
        session.query(Stock).delete()
        session.query(Invoice).delete()
        session.query(Order_line).delete()
        session.query(Order).delete()
        session.flush()

        # --- 2. REFERENTIAL DATA (Upsert logic) ---
        
        # Warehouses
        for n, c, t in [("Central", "Bruxelles", "Central"), ("Hub Nord", "Anvers", "Hub"), 
                        ("Dépôt Est", "Liège", "Proximity"), ("Dépôt Ouest", "Mons", "Proximity"), 
                        ("Dépôt Sud", "Namur", "Proximity")]:
            wh = session.query(Warehouse).filter_by(name=n).first()
            if wh:
                wh.city, wh.warehouse_type, wh.max_capacity = c, t, random.randint(200, 1000)
            else:
                session.add(Warehouse(name=n, city=c, warehouse_type=t, max_capacity=random.randint(200, 1000)))

        # Products
        for sku, name in [("IPH-16", "iPhone 16 Pro"), ("MAC-AIR", "MacBook Air M3"), 
                          ("IPAD-P", "iPad Pro 13"), ("WATCH-U", "Apple Watch Ultra"), ("APP-TV", "Apple TV 4K")]:
            prod = session.query(Product).filter_by(sku=sku).first()
            if prod:
                prod.unit_price_ex_vat = Decimal(random.randint(200, 2000))
            else:
                session.add(Product(sku=sku, name=name, unit_price_ex_vat=Decimal(random.randint(200, 2000))))

        # Customers
        for f, l in [("Alice", "Dupont"), ("Bob", "Martin"), ("Charlie", "Leroy"), ("David", "Dubois"), ("Eve", "Moreau")]:
            email = f"{f.lower()}.{l.lower()}@email.be"
            cust = session.query(Customer).filter_by(email=email).first()
            if cust:
                cust.address = f"{random.randint(1, 150)} Rue des Champs"
            else:
                session.add(Customer(first_name=f, last_name=l, address=f"{random.randint(1, 150)} Rue des Champs", email=email))
        
        session.flush()

        # --- 3. TRANSACTIONAL DATA ---
        all_wh = session.query(Warehouse).all()
        all_prod = session.query(Product).all()
        all_cust = session.query(Customer).all()

        # Orders (Always create new)
        orders = [Order(customer_id=random.choice(all_cust).id, 
                        warehouse_id=random.choice(all_wh).id, 
                        status=random.choice([OrderStatusEnum.DRAFT, OrderStatusEnum.VALIDATED])) for _ in range(5)]
        session.add_all(orders)
        session.flush()

        # Lines, Invoices & Movements
        for i in range(5):
            p = all_prod[i]
            # Order Lines
            session.add(Order_line(order_id=orders[i].id, product_id=p.id, quantity=random.randint(1, 5), 
                                   historical_price_ex_vat=p.unit_price_ex_vat))
            # Invoices
            price = Decimal("100.00")
            session.add(Invoice(order_id=orders[i].id, total_ex_vat=price, vat_amount=price*Decimal("0.21"), 
                                total_inc_vat=price*Decimal("1.21"), status=InvoiceStatusEnum.VALIDATED))
            # Stock Movements
            session.add(Stock_movement(product_id=p.id, quantity=random.randint(1, 10), 
                                       movement_type=MovementTypeEnum.SUPPLIER_RECEPTION, 
                                       dest_warehouse_id=all_wh[0].id, reason="Seed data"))
            
        # Stocks (Upsert for composite PK)
        for _ in range(5):
            wh_id, pr_id = random.choice(all_wh).id, random.choice(all_prod).id
            st = session.query(Stock).filter_by(warehouse_id=wh_id, product_id=pr_id).first()
            if st:
                st.quantity = random.randint(0, 100)
            else:
                session.add(Stock(warehouse_id=wh_id, product_id=pr_id, quantity=random.randint(0, 100)))

        session.commit()
        print("Database seeded successfully!")

if __name__ == "__main__":
    seed_data()