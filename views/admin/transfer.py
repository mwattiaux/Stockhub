import streamlit as st
import pandas as pd
from services.stock_service import transfer_stock_inter_warehouse
from crud.warehouse_crud import get_all_warehouses
from crud.product_crud import get_all_products
from crud.stock_crud import get_stock_by_warehouse_id_product_id
from crud.stock_movement_crud import get_stock_movements_filtered
from models.stock_movement import MovementTypeEnum

# --- SECURITY CHECK ---
if st.session_state.get("role") != "Admin":
    st.error("Access Denied!")
    st.stop()

st.header("🔄 Inter-Warehouse Transfer")
session = st.session_state.db

tab1, tab2 = st.tabs(["New Transfer", "Transfer History"])

# --- TAB 1: NEW TRANSFER ---
with tab1:
    # (Existing code for Tab 1 remains unchanged)
    warehouses = get_all_warehouses(session)
    products = get_all_products(session)
    wh_options = {wh.name: wh for wh in warehouses}
    prod_options = {p.name: p for p in products}

    col1, col2 = st.columns(2)
    with col1:
        src_name = st.selectbox("Source Warehouse", options=list(wh_options.keys()), key="src")
    with col2:
        dest_name = st.selectbox("Destination Warehouse", options=list(wh_options.keys()), key="dest")
    
    prod_name = st.selectbox("Product", options=list(prod_options.keys()))
    src_wh, dest_wh, product = wh_options[src_name], wh_options[dest_name], prod_options[prod_name]
    
    # Stock display logic
    src_stock = get_stock_by_warehouse_id_product_id(session, src_wh.id, product.id)
    src_qty = src_stock.quantity if src_stock else 0
    st.metric(f"Available in {src_name}", src_qty)

    with st.form("transfer_form"):
        quantity = st.number_input("Quantity", min_value=1, max_value=src_qty if src_qty > 0 else 1)
        if st.form_submit_button("Confirm Transfer"):
            try:
                transfer_stock_inter_warehouse(session, product.id, src_wh.id, dest_wh.id, int(quantity))
                st.success("Transfer completed!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# --- TAB 2: TRANSFER HISTORY WITH FILTERS ---
with tab2:
    st.subheader("Filter Movement History")
    
    # Filter Controls
    col_f1, col_f2, col_f3 = st.columns(3)
    
    # Create options including an "All" choice
    all_products = {p.name: p.id for p in products}
    all_warehouses = {w.name: w.id for w in warehouses}
    
    with col_f1:
        f_prod = st.selectbox("Filter by Product", ["All"] + list(all_products.keys()))
    with col_f2:
        f_wh = st.selectbox("Filter by Warehouse", ["All"] + list(all_warehouses.keys()))
    with col_f3:
        f_type = st.selectbox("Filter by Type", ["All"] + [t.value for t in MovementTypeEnum])
    
    # Map selection to function arguments
    p_id = all_products.get(f_prod) if f_prod != "All" else None
    w_id = all_warehouses.get(f_wh) if f_wh != "All" else None
    m_type = MovementTypeEnum(f_type) if f_type != "All" else None
    
    # Fetch filtered data
    movements = get_stock_movements_filtered(session, product_id=p_id, warehouse_id=w_id, movement_type=m_type)
    
    # Prepare data for DataFrame
    history_data = [
        {
            "Date": m.movement_date,
            "Product": m.product.name,
            "From": m.src_warehouse.name if m.src_warehouse else "Supplier",
            "To": m.dest_warehouse.name if m.dest_warehouse else "Client",
            "Qty": m.quantity,
            "Type": m.movement_type.value,
            "Reason": m.reason
        }
        for m in movements
    ]
    
    if history_data:
        st.dataframe(pd.DataFrame(history_data), use_container_width=True)
    else:
        st.info("No movements found matching these criteria.")