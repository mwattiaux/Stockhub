import streamlit as st
import pandas as pd
from decimal import Decimal
from services.catalog_service import register_product
from crud.product_crud import get_products_filtered

# --- SECURITY CHECK ---
# Ensure only users with the 'Admin' role can access the product management interface
if st.session_state.get("role") != "Admin":
    st.error("Access Denied!")
    st.stop()

st.header("Product Catalog Management")
session = st.session_state.db

# --- TABS NAVIGATION ---
# Split the interface: Tab 1 for viewing/filtering, Tab 2 for creating new products
tab1, tab2 = st.tabs(["📋 Product Catalog", "➕ Add New Product"])

# --- TAB 1: CATALOG & FILTERS ---
with tab1:
    st.subheader("Current Catalog")
    
    # Filtering UI components arranged in columns for a compact layout
    col1, col2, col3 = st.columns(3)
    with col1:
        name_filter = st.text_input("🔍 Search by Name")
    with col2:
        min_price = st.number_input("Min Price", min_value=0.0, format="%.2f")
    with col3:
        max_price = st.number_input("Max Price", min_value=0.0, format="%.2f")
    
    # Prepare filter arguments for the backend function
    # Convert empty inputs to None to ensure precise database queries
    filter_name = name_filter if name_filter else None
    filter_min = Decimal(str(min_price)) if min_price > 0 else None
    filter_max = Decimal(str(max_price)) if max_price > 0 else None
    
    # Fetch filtered products directly from the database
    products = get_products_filtered(
        session, 
        name=filter_name, 
        min_price=filter_min, 
        max_price=filter_max
    )
    
    # Transform objects into a list of dictionaries for Pandas display
    product_data = [
        {
            "ID": p.id,
            "SKU": p.sku,
            "Name": p.name,
            "Price (excl. VAT)": float(p.unit_price_ex_vat),
            "VAT (%)": float(p.default_vat_rate)
        }
        for p in products
    ]

    if product_data:
        st.dataframe(pd.DataFrame(product_data), use_container_width=True)
    else:
        st.info("No products found matching these criteria.")

# --- TAB 2: ADD PRODUCT ---
with tab2:
    st.subheader("Register a New Product")
    
    # Registration form with 'clear_on_submit' for better user experience
    with st.form("add_product_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            sku = st.text_input("SKU")
            name = st.text_input("Product Name")
        with col2:
            price = st.number_input("Price (excl. VAT)", min_value=0.0, format="%.2f")
            vat = st.number_input("VAT (%)", value=21.0)
        
        # Handle form submission and backend registration
        if st.form_submit_button("Register Product"):
            if sku and name:
                try:
                    register_product(session, sku, name, Decimal(str(price)), Decimal(str(vat)))
                    st.success("Product registered successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to register product: {e}")
            else:
                st.error("Please fill in all mandatory fields (SKU and Name).")