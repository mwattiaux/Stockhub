import streamlit as st
from database.database import engine, Base
from sqlalchemy.orm import sessionmaker
from services.crm_and_logistics_service import get_customer_by_email, register_customer
import re

# 1. Config
st.set_page_config(page_title="Stockhub", layout="wide")

# 2. Database Session
if "db" not in st.session_state:
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    st.session_state.db = Session()

# 3. Auth State
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_data = None

# 4. Logic
def login_page():
    st.title("🔐 Stockhub Login")
    
    # Tabs to separate Login from Registration
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        role = st.selectbox("I am a:", ["User", "Admin"], key="role_select")
        
        if role == "Admin":
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                if password == "admin":
                    st.session_state.logged_in = True
                    st.session_state.role = "Admin"
                    st.rerun()
                else:
                    st.error("Incorrect password")
        else:
            email = st.text_input("Email address")
            if st.button("Login"):
                user = get_customer_by_email(st.session_state.db, email)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.role = "User"
                    st.session_state.user_data = user
                    st.rerun()
                else:
                    st.error("Email not found")

    with tab2:
        st.subheader("New Customer Registration")
        reg_first = st.text_input("First Name")
        reg_last = st.text_input("Last Name")
        reg_addr = st.text_input("Address")
        reg_email = st.text_input("Email")
        
        if st.button("Register"):
            try:
                # Appelle la fonction de service sécurisée
                new_cust = register_customer(
                    st.session_state.db, 
                    reg_first, reg_last, reg_addr, reg_email
                )
                st.success(f"Account created for {new_cust.first_name}! You can now login.")
            except Exception as e:
                st.error(f"Registration failed: {e}")

# 5. Main navigation
if not st.session_state.logged_in:
    login_page()
else:
    # Sidebar Logout
    st.sidebar.title("Navigation")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.user_data = None
        st.rerun()
        
    # Pages mapping
    if st.session_state.role == "Admin":
        pages = [
            st.Page("views/admin/catalog.py", title="📋 Product Catalog"),
            st.Page("views/admin/warehouses.py", title="🏢 Warehouses"),
            st.Page("views/admin/customers.py", title="👤 Customers"),
            st.Page("views/admin/delivery.py", title="🚚 Supplier Delivery"),
            st.Page("views/admin/transfer.py", title="🔄 Inter-Warehouse Transfer"),
            st.Page("views/admin/order.py", title="📦 Order Validation Center"),
            st.Page("views/admin/statistics.py", title="📊 Statistics")
        ]
    else:
        pages = [
            st.Page("views/user/place_order.py", title="🛒 Place an Order"),
            st.Page("views/user/order_history.py", title="📜 My Order History"),
            st.Page("views/user/profile.py", title="👤 My Profile")
        ]
    
    nav = st.navigation(pages)
    nav.run()