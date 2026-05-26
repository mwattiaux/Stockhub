import streamlit as st
from services.crm_and_logistics_service import modify_customer

# Ensure the user is authenticated
if not st.session_state.get("logged_in"):
    st.error("Please log in.")
    st.stop()

st.header("👤 My Profile")
user = st.session_state.user_data
session = st.session_state.db

with st.form("profile_form"):
    # Display fields from the customers table as shown in image_9f9fa8.png
    st.text_input("First Name", value=user.first_name, disabled=True)
    st.text_input("Last Name", value=user.last_name, disabled=True)
    st.text_input("Email", value=user.email, disabled=True)
    
    # Format the created_at timestamp to display only up to the minute
    formatted_date = user.created_at.strftime("%Y-%m-%d %H:%M")
    st.text_input("Account Created At", value=formatted_date, disabled=True)
    
    # Address is the only modifiable field
    new_address = st.text_input("Address", value=user.address)
    
    # Handle profile update submission
    if st.form_submit_button("Update Address"):
        try:
            # Call the service to update only the address
            updated_user = modify_customer(
                session, 
                customer_id=user.id, 
                address=new_address
            )
            # Sync session state with the database result
            st.session_state.user_data = updated_user
            st.success("Address updated successfully!")
        except Exception as e:
            st.error(f"Error: {e}")

st.write("Need to change your email or name? Please contact the admin.")