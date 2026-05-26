import streamlit as st
import pandas as pd
from services.order_service import validate_and_finalize_order, generate_invoice_html, generate_invoice_pdf
from crud.order_crud import get_all_orders
from models.order import OrderStatusEnum

# --- ACCESS CONTROL ---
if st.session_state.get("role") != "Admin":
    st.error("Access Denied!")
    st.stop()

st.header("📦 Order Validation Center")
session = st.session_state.db

# --- TABS NAVIGATION ---
# Removed the manual 'active_tab' state logic. 
# Streamlit manages visibility of tab content natively.
tabs = st.tabs(["Pending Review", "Validated Orders & Invoices"])

# --- TAB 1: PENDING ORDERS ---
with tabs[0]:
    all_orders = get_all_orders(session)
    pending_orders = [o for o in all_orders if o.status == OrderStatusEnum.PENDING_REVIEW]
    
    if not pending_orders:
        st.info("No orders currently pending review.")
    else:
        order_data = [
            {"ID": o.id, "Customer": f"{o.customer.first_name} {o.customer.last_name}", 
             "Warehouse": o.warehouse.name} for o in pending_orders
        ]
        st.table(pd.DataFrame(order_data))
        
        selected_id = st.selectbox("Select Order ID to validate", [o.id for o in pending_orders])
        if st.button("Validate and Finalize"):
            try:
                validate_and_finalize_order(session, int(selected_id))
                st.success(f"Order #{selected_id} finalized!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# --- TAB 2: VALIDATED ORDERS ---
with tabs[1]:
    st.subheader("Validated Orders & Invoices")
    all_orders = get_all_orders(session)
    validated_orders = [o for o in all_orders if o.status == OrderStatusEnum.VALIDATED]

    if not validated_orders:
        st.info("No validated orders found.")
    else:
        for order in validated_orders:
            inv = getattr(order, 'invoice', None)
            if inv:
                with st.expander(f"Invoice #{inv.id} - Order #{order.id} ({order.customer.first_name} {order.customer.last_name})"):
                    st.write(f"**Total Inc. VAT:** {inv.total_inc_vat:,.2f} €")
                    if st.button("View Invoice", key=f"view_{inv.id}"):
                        st.session_state.invoice_to_show = inv
                        st.rerun()

# --- PREVIEW SECTION ---
# This remains visible until "Close Preview" is explicitly clicked, 
# regardless of which tab the user is currently looking at.
if "invoice_to_show" in st.session_state:
    inv = st.session_state.invoice_to_show
    st.divider()
    
    col_close, col_download = st.columns([1, 1])
    with col_close:
        if st.button("⬅ Close Preview"):
            del st.session_state.invoice_to_show
            st.rerun()
            
    with col_download:
        # Generate the PDF binary data only when needed
        pdf_data = generate_invoice_pdf(inv)
        st.download_button(
            label="📥 Download Real PDF",
            data=pdf_data,
            file_name=f"Invoice_{inv.id}.pdf",
            mime="application/pdf"
        )
    
    # Preview the HTML version for immediate visual feedback
    st.components.v1.html(generate_invoice_html(inv), height=800, scrolling=True)