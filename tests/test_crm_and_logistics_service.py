import pytest
import re
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

# On importe ton vrai Enum corrigé depuis tes modèles
from models.warehouse import WarehouseTypeEnum

# Import the logistics and CRM service functions under test
from services.crm_and_logistics_service import (
    register_warehouse, modify_warehouse,
    register_customer, modify_customer
)

# -------------------------------------------------------------------------
# TESTS: LOGISTICS BUSINESS LOGIC (Warehouses)
# -------------------------------------------------------------------------

def test_register_warehouse_success():
    """
    Happy Path Scenario: Verifies that a warehouse with valid configuration 
    properties is successfully trimmed, validated, and persisted.
    """
    session_mock = MagicMock(spec=Session)
    
    # Patch the validation check to simulate that the name is available
    with patch('services.crm_and_logistics_service.get_warehouse_by_name', return_value=None), \
         patch('services.crm_and_logistics_service.create_warehouse') as mock_create:
        
        expected_warehouse = MagicMock()
        expected_warehouse.id = 1
        mock_create.return_value = expected_warehouse
        
        result = register_warehouse(
            session=session_mock,
            name="   Liege Hub   ",  # Input with surrounding spaces to test sanitation trimming
            city="  Liege  ",
            warehouse_type=WarehouseTypeEnum.HUB,  # Corrigé ici
            max_capacity=500
        )
        
        # Assertions: Verify cleaning operations and down-stream CRUD handling
        assert result == expected_warehouse
        mock_create.assert_called_once_with(
            session=session_mock,
            name="Liege Hub",
            city="Liege",
            warehouse_type=WarehouseTypeEnum.HUB,
            max_capacity=500
        )


def test_register_warehouse_invalid_capacity():
    """Business Rule Violation: Maximum capacity must be strictly greater than 0."""
    session_mock = MagicMock(spec=Session)
    
    # Reject 0 capacity layout
    with pytest.raises(ValueError, match="Business Rule Violation: Maximum capacity must be strictly greater than 0."):
        register_warehouse(session_mock, "Antwerp", "Antwerp", WarehouseTypeEnum.HUB, max_capacity=0)
        
    # Reject negative capacity layout
    with pytest.raises(ValueError, match="Business Rule Violation: Maximum capacity must be strictly greater than 0."):
        register_warehouse(session_mock, "Antwerp", "Antwerp", WarehouseTypeEnum.HUB, max_capacity=-10)


def test_register_warehouse_empty_fields():
    """Business Logic Guardrail: Warehouse name and city cannot resolve to empty strings after trimming."""
    session_mock = MagicMock(spec=Session)
    
    with pytest.raises(ValueError, match="Business Logic Error: Warehouse name and city cannot be empty strings."):
        register_warehouse(session_mock, "   ", "Valid City", WarehouseTypeEnum.HUB, max_capacity=100)


def test_register_warehouse_duplicate_name():
    """Business Logic Guardrail: Rejects registration if a warehouse with the same name already exists."""
    session_mock = MagicMock(spec=Session)
    existing_warehouse = MagicMock()
    
    with patch('services.crm_and_logistics_service.get_warehouse_by_name', return_value=existing_warehouse):
        with pytest.raises(ValueError, match="Business Logic Error: A warehouse named 'Charleroi' already exists."):
            register_warehouse(session_mock, "Charleroi", "Charleroi", WarehouseTypeEnum.CENTRAL, max_capacity=1000)


def test_modify_warehouse_not_found():
    """Business Logic Guardrail: Ensures modifications targeting a missing warehouse identifier fail gracefully."""
    session_mock = MagicMock(spec=Session)
    
    with patch('services.crm_and_logistics_service.get_warehouse_by_id', return_value=None):
        with pytest.raises(ValueError, match="Business Logic Error: Warehouse not found."):
            modify_warehouse(session_mock, warehouse_id=404, name="New Name")


def test_modify_warehouse_invalid_capacity():
    """Business Rule Reinforcement: Ensures capacity updates block if value is below or equal to zero."""
    session_mock = MagicMock(spec=Session)
    warehouse_mock = MagicMock()
    
    with patch('services.crm_and_logistics_service.get_warehouse_by_id', return_value=warehouse_mock):
        with pytest.raises(ValueError, match="Business Logic Error: Maximum capacity must be strictly greater than 0."):
            modify_warehouse(session_mock, warehouse_id=1, max_capacity=0)


def test_modify_warehouse_shrink_below_active_stock():
    """
    Business Logic Guardrail: Prevents down-sizing a facility's capacity 
    below the total quantity of physical items currently stored inside it.
    """
    session_mock = MagicMock(spec=Session)
    warehouse_mock = MagicMock()
    warehouse_mock.id = 1
    
    # Simulate that the warehouse currently holds a cumulative physical balance of 150 items
    stock_item_1 = MagicMock(quantity=100)
    stock_item_2 = MagicMock(quantity=50)
    active_stocks = [stock_item_1, stock_item_2]
    
    with patch('services.crm_and_logistics_service.get_warehouse_by_id', return_value=warehouse_mock), \
         patch('services.crm_and_logistics_service.get_all_stock_by_warehouse', return_value=active_stocks):
        
        # Requesting an update to 120 max capacity while holding 150 items must throw a business error
        with pytest.raises(ValueError, match="Cannot reduce maximum capacity to 120. Warehouse currently holds 150 items."):
            modify_warehouse(session_mock, warehouse_id=1, max_capacity=120)


def test_modify_warehouse_success():
    """Happy Path Scenario: Ensures valid modifications propagate correctly to the update CRUD layer."""
    session_mock = MagicMock(spec=Session)
    warehouse_mock = MagicMock()
    warehouse_mock.id = 1
    
    with patch('services.crm_and_logistics_service.get_warehouse_by_id', return_value=warehouse_mock), \
         patch('services.crm_and_logistics_service.get_all_stock_by_warehouse', return_value=[]), \
         patch('services.crm_and_logistics_service.update_warehouse') as mock_update:
        
        modify_warehouse(session_mock, warehouse_id=1, name="Updated Name", max_capacity=500)
        
        mock_update.assert_called_once_with(
            session=session_mock,
            warehouse_id=1,
            name="Updated Name",
            city=None,
            max_capacity=500
        )


# -------------------------------------------------------------------------
# TESTS: CRM BUSINESS LOGIC (Customers)
# -------------------------------------------------------------------------

def test_register_customer_success():
    """
    Happy Path Scenario: Ensures that customer details are properly trimmed, 
    lowercased for the email identity key, and registered.
    """
    session_mock = MagicMock(spec=Session)
    
    with patch('services.crm_and_logistics_service.get_customer_by_email', return_value=None), \
         patch('services.crm_and_logistics_service.create_customer') as mock_create:
        
        expected_customer = MagicMock()
        mock_create.return_value = expected_customer
        
        result = register_customer(
            session=session_mock,
            first_name="   Maxime  ",
            last_name="  Doe  ",
            address="  123 Rue de la Loi, Brussels  ",
            email="  Max.Doe@Domain.BE  "  # Mixed casing and spaces to check formatting normalization
        )
        
        assert result == expected_customer
        mock_create.assert_called_once_with(
            session=session_mock,
            first_name="Maxime",
            last_name="Doe",
            address="123 Rue de la Loi, Brussels",
            email="max.doe@domain.be"  # Clean sanitized output
        )


def test_register_customer_missing_fields():
    """Business Logic Guardrail: Rejects enrollment if any mandatory text field resolves to empty space."""
    session_mock = MagicMock(spec=Session)
    
    with pytest.raises(ValueError, match="All customer fields .* are mandatory"):
        register_customer(session_mock, "John", "   ", "Brussels", "john@doe.com")


@pytest.mark.parametrize("invalid_email", [
    "plainaddress",
    "john@domain",
    "john@@domain.com",
    "john.doe@.com",
    "@missingusername.com"
])
def test_register_customer_invalid_email_regex(invalid_email):
    """Business Logic Guardrail: Rejects structural enrollment attempts defying strict standard syntax regex matching."""
    session_mock = MagicMock(spec=Session)
    
    with pytest.raises(ValueError, match="is not formatted correctly"):
        register_customer(session_mock, "John", "Doe", "Brussels", invalid_email)


def test_register_customer_duplicate_email():
    """Business Logic Guardrail: Ensures duplicate emails are blocked to preserve identity uniqueness integrity."""
    session_mock = MagicMock(spec=Session)
    existing_customer = MagicMock()
    
    with patch('services.crm_and_logistics_service.get_customer_by_email', return_value=existing_customer):
        with pytest.raises(ValueError, match="A customer with email 'duplicate@test.com' already exists."):
            register_customer(session_mock, "John", "Doe", "Namur", "duplicate@test.com")


def test_modify_customer_not_found():
    """Business Logic Guardrail: Ensures modifying an unmapped customer ID breaks immediately."""
    session_mock = MagicMock(spec=Session)
    
    with patch('services.crm_and_logistics_service.get_customer_by_id', return_value=None):
        with pytest.raises(ValueError, match="Customer not found."):
            modify_customer(session_mock, customer_id=999, first_name="Alice")


@pytest.mark.parametrize("field_key, kwargs", [
    ("First name", {"first_name": "   "}),
    ("Last name", {"last_name": "   "}),
    ("Address", {"address": "   "}),
    ("Email", {"email": "   "})
])
def test_modify_customer_empty_updates(field_key, kwargs):
    """Business Logic Guardrail: Blocks updating fields to empty whitespace strings."""
    session_mock = MagicMock(spec=Session)
    customer_mock = MagicMock()
    
    with patch('services.crm_and_logistics_service.get_customer_by_id', return_value=customer_mock):
        with pytest.raises(ValueError, match=f"Business Logic Error: {field_key} cannot be updated to an empty string."):
            modify_customer(session_mock, customer_id=1, **kwargs)


def test_modify_customer_email_invalid_regex():
    """Business Rule Reinforcement: Rejects update request if the requested new email format breaks the syntax Regex layout."""
    session_mock = MagicMock(spec=Session)
    customer_mock = MagicMock()
    
    with patch('services.crm_and_logistics_service.get_customer_by_id', return_value=customer_mock):
        with pytest.raises(ValueError, match="is not formatted correctly"):
            modify_customer(session_mock, customer_id=1, email="wrong_format@com")


def test_modify_customer_email_collision():
    """
    Business Logic Guardrail: Ensures profile updates modifying identity emails 
    block instantly if that target email string is already claimed by an ALTERNATE distinct customer profile.
    """
    session_mock = MagicMock(spec=Session)
    
    target_customer = MagicMock()
    target_customer.id = 5  # Customer being edited
    
    colliding_owner = MagicMock()
    colliding_owner.id = 42  # Another pre-existing record claiming the target address string
    
    with patch('services.crm_and_logistics_service.get_customer_by_id', return_value=target_customer), \
         patch('services.crm_and_logistics_service.get_customer_by_email', return_value=colliding_owner):
        
        with pytest.raises(ValueError, match="Another customer is already registered with the email 'taken@address.com'."):
            modify_customer(session_mock, customer_id=5, email="taken@address.com")


def test_modify_customer_email_no_collision_if_same_customer():
    """
    Edge Case Validation: Updating profile info while re-submitting the EXACT same email 
    already bound to this specific account must pass without triggering uniqueness errors.
    """
    session_mock = MagicMock(spec=Session)
    
    target_customer = MagicMock()
    target_customer.id = 5  # Customer being edited
    
    with patch('services.crm_and_logistics_service.get_customer_by_id', return_value=target_customer), \
         patch('services.crm_and_logistics_service.get_customer_by_email', return_value=target_customer), \
         patch('services.crm_and_logistics_service.update_customer') as mock_update:
        
        modify_customer(session_mock, customer_id=5, email="my_own_email@test.com", address="New Home")
        
        # Verify execution completed successfully and mapped calls correctly
        mock_update.assert_called_once_with(
            session=session_mock,
            customer_id=5,
            first_name=None,
            last_name=None,
            address="New Home",
            email="my_own_email@test.com"
        )