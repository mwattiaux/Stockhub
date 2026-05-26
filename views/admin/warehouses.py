import streamlit as st
import pandas as pd
from services.crm_and_logistics_service import register_warehouse
from crud.warehouse_crud import get_all_warehouses, get_warehouses_filtered  # Ensure this is imported
from models.warehouse import WarehouseTypeEnum

# --- ACCESS CONTROL ---
if st.session_state.get("role") != "Admin":
    st.error("Access Denied!")
    st.stop()

st.header("Warehouse Management")
session = st.session_state.db

# --- TABS NAVIGATION ---
tab1, tab2 = st.tabs(["🏢 Existing Warehouses", "➕ Add New Warehouse"])

# --- TAB 1: LISTING & FILTERING ---
with tab1:
    st.subheader("Manage Warehouses")
    
    # Filtering UI
    col1, col2 = st.columns(2)
    with col1:
        city_filter = st.text_input("Filter by City")
    with col2:
        # Include an "All" option for the Enum
        type_options = ["All"] + [t for t in WarehouseTypeEnum]
        selected_type = st.selectbox("Filter by Type", options=type_options)
    
    # Determine filter values
    city_val = city_filter if city_filter else None
    type_val = selected_type if selected_type != "All" else None
    
    # Use your backend filtering function
    warehouses = get_warehouses_filtered(session, city=city_val, warehouse_type=type_val)
    
    warehouse_data = [
        {
            "ID": w.id,
            "Name": w.name,
            "City": w.city,
            "Type": w.warehouse_type.value,
            "Max Capacity": w.max_capacity
        }
        for w in warehouses
    ]

    if warehouse_data:
        st.dataframe(pd.DataFrame(warehouse_data), use_container_width=True)
    else:
        st.info("No warehouses match your criteria.")

# --- TAB 2: ADD WAREHOUSE ---
with tab2:
    st.subheader("Register a New Warehouse")
    with st.form("add_warehouse_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            w_name = st.text_input("Warehouse Name")
            w_city = st.text_input("City")
        with col2:
            w_type = st.selectbox("Type", options=[t for t in WarehouseTypeEnum])
            w_capacity = st.number_input("Max Capacity", min_value=1, step=1)
        
        if st.form_submit_button("Register Warehouse"):
            if w_name and w_city:
                try:
                    register_warehouse(session, w_name, w_city, w_type, int(w_capacity))
                    st.success(f"Warehouse '{w_name}' registered successfully.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("Please fill in all fields.")