import streamlit as st
import pandas as pd
from services.stock_service import add_supplier_reception
from crud.warehouse_crud import get_all_warehouses
from crud.product_crud import get_all_products
from crud.stock_movement_crud import get_stock_movements_filtered
from models.stock_movement import MovementTypeEnum

# --- SECURITY CHECK ---
if st.session_state.get("role") != "Admin":
    st.error("Access Denied!")
    st.stop()

st.header("🚚 Supplier Delivery Management")
session = st.session_state.db

# --- TABS NAVIGATION ---
tab1, tab2 = st.tabs(["New Delivery", "Delivery History"])

# --- TAB 1: NEW DELIVERY ---
with tab1:
    warehouses = get_all_warehouses(session)
    products = get_all_products(session)

    wh_options = {wh.name: wh.id for wh in warehouses}
    prod_options = {prod.name: prod.id for prod in products}

    with st.form("delivery_form", clear_on_submit=True):
        st.subheader("Register New Supplier Delivery")
        dest_wh_name = st.selectbox("Destination Warehouse", options=list(wh_options.keys()))
        product_name = st.selectbox("Product", options=list(prod_options.keys()))
        quantity = st.number_input("Quantity", min_value=1, step=1)
        
        if st.form_submit_button("Confirm Delivery"):
            try:
                add_supplier_reception(
                    session=session, 
                    product_id=prod_options[product_name], 
                    warehouse_id=wh_options[dest_wh_name], 
                    quantity=int(quantity)
                )
                st.success(f"Successfully added {quantity} units to {dest_wh_name}.")
            except Exception as e:
                st.error(f"Error: {e}")

# --- TAB 2: DELIVERY HISTORY WITH FILTERS ---
with tab2:
    st.subheader("Filter Supplier Reception History")
    
    # Define filter controls
    col_f1, col_f2 = st.columns(2)
    
    # Build filter options
    prod_filter_map = {p.name: p.id for p in products}
    wh_filter_map = {w.name: w.id for w in warehouses}
    
    with col_f1:
        f_prod = st.selectbox("Filter by Product", ["All"] + list(prod_filter_map.keys()))
    with col_f2:
        f_wh = st.selectbox("Filter by Warehouse", ["All"] + list(wh_filter_map.keys()))
    
    # Map UI selection to function arguments
    p_id = prod_filter_map.get(f_prod) if f_prod != "All" else None
    w_id = wh_filter_map.get(f_wh) if f_wh != "All" else None
    
    # Fetch filtered data
    movements = get_stock_movements_filtered(
        session=session, 
        product_id=p_id,
        warehouse_id=w_id,
        movement_type=MovementTypeEnum.SUPPLIER_RECEPTION
    )
    
    # Prepare data for DataFrame
    history_data = [
        {
            "Date": m.movement_date,
            "Product": m.product.name,
            "Warehouse": m.dest_warehouse.name if m.dest_warehouse else "N/A",
            "Qty": m.quantity,
            "Reason": m.reason
        }
        for m in movements
    ]
    
    if history_data:
        st.dataframe(pd.DataFrame(history_data), use_container_width=True)
    else:
        st.info("No deliveries found matching the selected filters.")