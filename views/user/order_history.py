import streamlit as st
from decimal import Decimal
from crud.order_crud import get_orders_filtered, delete_order
from services.order_service import generate_invoice_pdf, generate_invoice_html

if not st.session_state.get("logged_in"):
    st.error("Please log in to view your order history.")
    st.stop()

st.header("📜 My Order History")
session = st.session_state.db
user_id = st.session_state.user_data.id

# Fetch user orders
orders = get_orders_filtered(session, customer_id=user_id)

if orders:
    for o in orders:
        # Get status safely
        status_str = o.status.value if hasattr(o.status, 'value') else str(o.status)
        
        with st.expander(f"Order #{o.id} | Status: {status_str}"):
            
            # --- ACTIONS : SUPPRESSION / PREVIEW / PDF ---
            col_a, col_b = st.columns([1, 1])
            
            # 1. DELETE DRAFT
            if "DRAFT" in status_str.upper():
                if col_a.button("Delete Draft", key=f"del_{o.id}", type="primary"):
                    delete_order(session, o.id)
                    st.rerun()
            
            # 2. PREVIEW & DOWNLOAD (Pour commandes Validated/Pending)
            if hasattr(o, 'invoice') and o.invoice is not None:
                with col_a:
                    if st.button("👁️ View Invoice", key=f"view_{o.id}"):
                        st.session_state.invoice_to_show = o.invoice
                        st.rerun()
                
                with col_b:
                    pdf_data = generate_invoice_pdf(o.invoice)
                    st.download_button(
                        label="📥 Download PDF",
                        data=pdf_data,
                        file_name=f"Invoice_{o.id}.pdf",
                        mime="application/pdf"
                    )
            
            st.divider()
            
            # --- DÉTAILS DES ARTICLES ---
            if o.order_lines:
                total_inc_vat = Decimal("0.00")
                for line in o.order_lines:
                    price_ex_vat = line.historical_price_ex_vat
                    qty = Decimal(str(line.quantity))
                    vat_rate = line.product.default_vat_rate if line.product else Decimal("0.00")
                    
                    line_total_ex_vat = price_ex_vat * qty
                    line_vat_amount = line_total_ex_vat * (vat_rate / Decimal("100.00"))
                    line_total_inc_vat = line_total_ex_vat + line_vat_amount
                    total_inc_vat += line_total_inc_vat
                    
                    c1, c2 = st.columns([2, 1])
                    c1.markdown(f"**{line.product.name}** (Qty: {line.quantity})")
                    c2.markdown(
                        f"Inc. VAT: **{line_total_inc_vat:.2f}€**", 
                        unsafe_allow_html=True
                    )
                    st.divider()
                
                st.subheader(f"Total Amount (Inc. VAT): {total_inc_vat:.2f}€")
            else:
                st.write("Your cart is empty.")

    # --- SECTION MODAL DE PRÉVISUALISATION ---
    if "invoice_to_show" in st.session_state:
        st.divider()
        inv = st.session_state.invoice_to_show
        
        if st.button("⬅ Close Preview"):
            del st.session_state.invoice_to_show
            st.rerun()
            
        # Rendu HTML (Preview)
        st.components.v1.html(generate_invoice_html(inv), height=800, scrolling=True)

else:
    st.info("No orders found.")