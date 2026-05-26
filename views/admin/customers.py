import streamlit as st
import pandas as pd
from services.crm_and_logistics_service import register_customer
from crud.customer_crud import get_customers_filtered 
from models.customer import Customer

# --- ACCESS CONTROL ---
# Ensure only users with the 'Admin' role can view or modify customer records
if st.session_state.get("role") != "Admin":
    st.error("Access Denied!")
    st.stop()

st.header("Customer Management")
session = st.session_state.db

# --- TABS NAVIGATION ---
# Split the interface: Tab 1 for viewing/filtering, Tab 2 for creation
tab1, tab2 = st.tabs(["👤 Existing Customers", "➕ Add New Customer"])

# --- TAB 1: LISTING & FILTERING ---
with tab1:
    st.subheader("Manage Customers")
    
    # Filtering UI components arranged in columns for a compact layout
    col1, col2, col3 = st.columns(3)
    with col1:
        f_name_filter = st.text_input("Filter by First Name")
    with col2:
        l_name_filter = st.text_input("Filter by Last Name")
    with col3:
        email_filter = st.text_input("Filter by Email")
    
    # Prepare filter arguments for the backend function
    # Convert empty strings to None for exact backend handling
    f_name_val = f_name_filter if f_name_filter else None
    l_name_val = l_name_filter if l_name_filter else None
    email_val = email_filter if email_filter else None
    
    # Fetch filtered customers directly from the database
    customers = get_customers_filtered(
        session, 
        first_name=f_name_val, 
        last_name=l_name_val, 
        email=email_val
    )
    
    # Transform objects into a list of dictionaries for display
    customer_data = [
        {
            "ID": c.id,
            "First Name": c.first_name,
            "Last Name": c.last_name,
            "Address": c.address,
            "Email": c.email,
            "Created At": c.created_at.strftime('%Y-%m-%d %H:%M') if c.created_at else "N/A"
        }
        for c in customers
    ]

    # Render the data
    if customer_data:
        st.dataframe(pd.DataFrame(customer_data), use_container_width=True)
    else:
        st.info("No customers found matching these criteria.")

# --- TAB 2: ADD CUSTOMER ---
with tab2:
    st.subheader("Register a New Customer")
    
    # Form to ensure data integrity
    with st.form("add_customer_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            f_name = st.text_input("First Name")
            l_name = st.text_input("Last Name")
        with col2:
            address = st.text_input("Address")
            email = st.text_input("Email")
            
        if st.form_submit_button("Register Customer"):
            if f_name and l_name and email:
                try:
                    register_customer(session, f_name, l_name, address, email)
                    st.success(f"Customer {f_name} {l_name} registered successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("Please fill in all mandatory fields.")