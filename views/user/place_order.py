import streamlit as st
import random
from decimal import Decimal
from crud.product_crud import get_products_filtered
from crud.order_crud import create_order, get_orders_filtered
from crud.order_line_crud import get_all_order_lines_by_order_id, delete_order_line
from crud.warehouse_crud import get_warehouses_filtered
from services.order_service import add_product_to_order, submit_order_for_review
from models.order import OrderStatusEnum
from models.warehouse import WarehouseTypeEnum

# --- ACCESS CONTROL ---
# Ensure the user is logged in before allowing access to order management
if not st.session_state.get("logged_in"):
    st.error("Please log in to continue.")
    st.stop()

# --- INITIALIZATION ---
# Track the current order context in the session state
if "initialized" not in st.session_state:
    st.session_state.current_order_id = None
    st.session_state.order_selector_index = 0
    st.session_state.initialized = True

st.header("🛒 Order Management")
session = st.session_state.db
user_id = st.session_state.user_data.id

# 1. Fetch existing drafts for the current customer
drafts = get_orders_filtered(session, customer_id=user_id, status=OrderStatusEnum.DRAFT)

# --- INTEGRITY CHECK ---
# If the current order is no longer in draft status, reset the context
if st.session_state.current_order_id:
    draft_ids = [o.id for o in drafts]
    if st.session_state.current_order_id not in draft_ids:
        st.session_state.current_order_id = None
        st.session_state.order_selector_index = 0
        st.rerun()

# 2. Selection interface for existing or new orders
st.subheader("Your Drafts")
order_options = {f"Order #{o.id} (Date: {o.order_date})": o.id for o in drafts}
order_options["+ Start a new order"] = "NEW"
options_list = list(order_options.keys())

selected_choice = st.selectbox(
    "Select an order to edit or start a new one:", 
    options=options_list,
    index=st.session_state.order_selector_index,
    key="order_selector_widget"
)

# --- IMMEDIATE CHANGE DETECTION ---
# Detects when the user changes selection to update the UI context
nouvel_index = options_list.index(selected_choice)
if nouvel_index != st.session_state.order_selector_index:
    st.session_state.order_selector_index = nouvel_index
    selected_id = order_options[selected_choice]
    st.session_state.current_order_id = selected_id if selected_id != "NEW" else None
    st.rerun()

selected_id = order_options[selected_choice]

# Logic to initialize a new draft with dynamic warehouse assignment
if selected_id == "NEW":
    if st.button("Initialize New Draft"):
        # Fetch eligible warehouses (HUB or PROXIMITY types)
        hubs = get_warehouses_filtered(session, warehouse_type=WarehouseTypeEnum.HUB)
        proxies = get_warehouses_filtered(session, warehouse_type=WarehouseTypeEnum.PROXIMITY)
        available_warehouses = hubs + proxies
        
        if not available_warehouses:
            st.error("No eligible warehouses (HUB or Proximity) available.")
        else:
            # Assign an eligible warehouse randomly for load distribution
            selected_wh = random.choice(available_warehouses)
            new_order = create_order(session, customer_id=user_id, warehouse_id=selected_wh.id)
            st.session_state.current_order_id = new_order.id
            st.rerun()

# 3. Editing interface
if st.session_state.current_order_id:
    st.info(f"Editing Order ID: {st.session_state.current_order_id}")
    
    st.subheader("Catalog")
    col1, col2, col3 = st.columns(3)
    search_name = col1.text_input("Search by name")
    min_price = col2.number_input("Min Price (€)", min_value=0.0, value=0.0)
    max_price = col3.number_input("Max Price (€)", min_value=0.0, value=1000.0)

    products = get_products_filtered(
        session, 
        name=search_name, 
        min_price=Decimal(str(min_price)), 
        max_price=Decimal(str(max_price))
    )

    if products:
        product_options = {f"{p.name} - {p.unit_price_ex_vat}€": p.id for p in products}
        with st.form("add_item", clear_on_submit=True):
            selected_label = st.selectbox("Select a product", options=list(product_options.keys()))
            qty = st.number_input("Quantity", min_value=1, step=1)
            if st.form_submit_button("Add to order"):
                product_id = product_options[selected_label]
                prod = next(p for p in products if p.id == product_id)
                add_product_to_order(session, st.session_state.current_order_id, prod.id, qty, prod.unit_price_ex_vat)
                st.success(f"Added: {prod.name}")
                st.rerun()
    
    st.subheader("Items in your cart")
    lines = get_all_order_lines_by_order_id(session, st.session_state.current_order_id)
    if lines:
        for line in lines:
            c1, c2 = st.columns([3, 1])
            c1.write(f"**{line.product.name}** | Qty: {line.quantity}")
            if c2.button("Remove", key=f"del_{line.id}"):
                delete_order_line(session, line.id)
                st.success("Item removed.")
                st.rerun()

        col_save, col_submit = st.columns(2)
        with col_save:
            if st.button("Save Draft & Exit"):
                st.session_state.current_order_id = None
                st.session_state.order_selector_index = 0
                st.success("Draft saved!")
                st.rerun()
        with col_submit:
            if st.button("Submit for Validation"):
                submit_order_for_review(session, st.session_state.current_order_id)
                st.session_state.current_order_id = None
                st.session_state.order_selector_index = 0
                st.success("Order submitted!")
                st.rerun()
    else:
        st.write("Your cart is empty.")
else:
    st.info("Please select a draft above or start a new one.")