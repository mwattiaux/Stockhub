import streamlit as st
import pandas as pd
from crud.warehouse_crud import get_all_warehouses
from crud.order_crud import get_all_orders
from models.invoice import InvoiceStatusEnum
from models.warehouse import WarehouseTypeEnum

st.header("📊 Dashboard & Statistics")

# Ensure the database session is available from session state
session = st.session_state.db

# Organize the interface into three functional tabs
tab1, tab2, tab3 = st.tabs(["🏗️ Capacity", "💰 Revenue", "📈 Advanced Analytics"])

# --- TAB 1: WAREHOUSE CAPACITY ---
with tab1:
    st.subheader("Warehouse Fill Rate")
    warehouses = get_all_warehouses(session)
    
    # Prepare warehouse data list
    data = []
    for w in warehouses:
        # Calculate total stock quantity by summing the 'quantity' field of all stock records
        current_total_quantity = sum(s.quantity for s in w.stocks)
        fill_rate = (current_total_quantity / w.max_capacity) * 100 if w.max_capacity > 0 else 0
        data.append({
            "Warehouse": w.name, 
            "Fill Rate (%)": fill_rate, 
            "Type": w.warehouse_type.value
        })
    
    df_w = pd.DataFrame(data).set_index("Warehouse")
    
    # Filter by Warehouse Type
    type_options = ["All"] + [t.value for t in WarehouseTypeEnum]
    selected_type = st.selectbox("Filter by Type:", type_options)
    
    if selected_type != "All":
        df_w = df_w[df_w["Type"] == selected_type]
    
    # Toggle between Global Overview and Detailed view
    selection = st.selectbox("View by:", ["General Overview", "Per Warehouse"])
    
    if selection == "General Overview":
        st.metric("Average Fill Rate", f"{df_w['Fill Rate (%)'].mean():.2f} %")
        # Visualizing utilization using progress bars as a visual scale
        for warehouse_name, row in df_w.iterrows():
            st.write(f"**{warehouse_name}** ({row['Type']})")
            st.progress(min(row["Fill Rate (%)"] / 100, 1.0), text=f"{row['Fill Rate (%)']:.1f}%")
            
    else:
        selected_wh = st.selectbox("Select Warehouse:", df_w.index)
        rate = df_w.loc[selected_wh, "Fill Rate (%)"]
        st.metric(f"Fill Rate: {selected_wh}", f"{rate:.2f} %")
        st.progress(min(rate / 100, 1.0), text=f"{rate:.1f}% of capacity used")

# --- TAB 2: PENDING REVENUE ---
with tab2:
    st.subheader("Pending Revenue Evolution")
    
    orders = get_all_orders(session)
    # Filter for orders with PENDING_PAYMENT status
    pending_orders = [o for o in orders if o.invoice and o.invoice.status == InvoiceStatusEnum.PENDING_PAYMENT]
    
    if pending_orders:
        df_rev = pd.DataFrame([
            {"Date": pd.to_datetime(o.order_date), "Amount": float(o.invoice.total_inc_vat)} 
            for o in pending_orders if o.invoice is not None
        ])
        
        # Dynamic grouping by time period
        period = st.radio("Group by:", ["Day", "Month", "Year"], horizontal=True)
        period_map = {"Day": "D", "Month": "M", "Year": "Y"}
        
        df_grouped = df_rev.groupby(df_rev['Date'].dt.to_period(period_map[period]))['Amount'].sum().reset_index()
        df_grouped['Date'] = df_grouped['Date'].astype(str)
        df_grouped = df_grouped.set_index('Date')
        
        # Display revenue bar chart
        st.bar_chart(df_grouped)
        st.metric("Total Pending Revenue", f"{df_grouped['Amount'].sum():,.2f} €")
    else:
        st.info("No pending payments found.")

# --- TAB 3: ADVANCED ANALYTICS ---
with tab3:
    st.subheader("Advanced Operations Monitoring")
    
    # 1. Inventory Turnover (Simplified visualization)
    with st.expander("🔄 Inventory Turnover Analysis"):
        st.info("Monitor products with high vs. low stock rotation frequency.")
        st.write("Turnover data calculation based on recent outbound stock movements.")

    # 3. Revenue by City (Geographic performance)
    with st.expander("📍 Revenue by City"):
        orders = get_all_orders(session)
        df_city = pd.DataFrame([
            {"City": o.warehouse.city, "Amount": float(o.invoice.total_inc_vat)}
            for o in orders if o.invoice and o.warehouse
        ])
        if not df_city.empty:
            df_city_grouped = df_city.groupby("City")["Amount"].sum()
            st.bar_chart(df_city_grouped)
        else:
            st.write("No geographic revenue data available.")

    # 5. Low Stock Alerts
    with st.expander("⚠️ Critical Stock Alerts"):
        warehouses = get_all_warehouses(session)
        low_stock_items = []
        
        # Define threshold for low stock alert
        alert_threshold = 5 
        
        for w in warehouses:
            for s in w.stocks:
                if s.quantity < alert_threshold:
                    low_stock_items.append({
                        "Warehouse": w.name,
                        "Product": s.product.name,
                        "Current Qty": s.quantity
                    })
        
        if low_stock_items:
            st.warning(f"Products below threshold ({alert_threshold} units):")
            st.table(pd.DataFrame(low_stock_items))
        else:
            st.success("All stock levels are optimal.")