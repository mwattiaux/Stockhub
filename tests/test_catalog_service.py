import pytest
from decimal import Decimal
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

# Import the service functions under test
from services.catalog_service import register_product, modify_product

# -------------------------------------------------------------------------
# TESTS: register_product
# -------------------------------------------------------------------------

def test_register_product_success_with_custom_vat():
    """
    Happy Path Scenario: Verifies that a valid product enrollment request 
    with an explicitly provided custom VAT rate succeeds.
    """
    # Arrange: Initialize a dummy SQLAlchemy Session mock object
    session_mock = MagicMock(spec=Session)
    
    # Intercept runtime calls to simulate that the requested SKU does not exist yet
    with MagicMock() as mock_get_sku:
        import services.catalog_service
        services.catalog_service.get_product_by_sku = mock_get_sku
        mock_get_sku.return_value = None
        
        # FIX: Use a MagicMock instead of an actual Product instance to bypass 
        # both custom __init__ restrictions and SQLAlchemy mapper initialization errors.
        expected_product = MagicMock()
        expected_product.id = 1
        expected_product.sku = "PROD-OK"
        expected_product.name = "Article Test"
        expected_product.unit_price_ex_vat = Decimal("10.00")
        expected_product.default_vat_rate = Decimal("6.00")
        
        services.catalog_service.create_product = MagicMock(return_value=expected_product)

        # Act: Execute the target service function with an explicit 6% VAT rate
        result = register_product(
            session=session_mock,
            sku="PROD-OK",
            name="Article Test",
            unit_price_ex_vat=Decimal("10.00"),
            default_vat_rate=Decimal("6.00")
        )

        # Assert: Validate that the returned record matches expectations and keeps properties
        assert result == expected_product
        assert result.default_vat_rate == Decimal("6.00")


def test_register_product_success_fallback_to_belgian_vat():
    """
    Business Rule Validation: Ensures that when no default VAT rate is supplied, 
    the system automatically applies the 21% Belgian Standard fallback rate.
    """
    # Arrange: Setup the isolated session mock
    session_mock = MagicMock(spec=Session)
    
    with MagicMock() as mock_get_sku:
        import services.catalog_service
        services.catalog_service.get_product_by_sku = mock_get_sku
        mock_get_sku.return_value = None
        
        # Track parameters sent downstream to the database layer
        mock_create = MagicMock()
        services.catalog_service.create_product = mock_create

        # Act: Execute registration omitting the optional VAT argument
        register_product(
            session=session_mock, 
            sku="PROD-VAT", 
            name="Test Default VAT", 
            unit_price_ex_vat=Decimal("100.00")
        )

        # Assert: Verify that the CRUD layer was triggered with the automatic 21.00% VAT rate
        mock_create.assert_called_once_with(
            session=session_mock,
            sku="PROD-VAT",
            name="Test Default VAT",
            unit_price_ex_vat=Decimal("100.00"),
            default_vat_rate=Decimal("21.00")
        )


def test_register_product_invalid_price():
    """
    Business Rule Violation: Enforces that the net unit price (ex-VAT) 
    must be strictly greater than zero.
    """
    # Arrange: Instantiate the mock context
    session_mock = MagicMock(spec=Session)

    # Edge Case Assertion 1: Reject a price configuration equal to exactly 0.00
    with pytest.raises(ValueError, match="Business Logic Error: Unit price ex-VAT must be strictly greater than 0."):
        register_product(session_mock, "SKU-0", "Free Item", Decimal("0.00"))

    # Edge Case Assertion 2: Reject a negative price layout
    with pytest.raises(ValueError, match="Business Logic Error: Unit price ex-VAT must be strictly greater than 0."):
        register_product(session_mock, "SKU-NEG", "Debt Item", Decimal("-5.50"))


def test_register_product_negative_vat():
    """
    Business Logic Guardrail: Ensures registration fails instantly 
    if a negative VAT rate is provided.
    """
    # Arrange: Setup mock environment
    session_mock = MagicMock(spec=Session)

    # Act & Assert: Capture and validate the negative exception feedback loop
    with pytest.raises(ValueError, match="Business Logic Error: VAT rate cannot be negative."):
        register_product(session_mock, "SKU-TVA", "Bad VAT", Decimal("10.00"), default_vat_rate=Decimal("-1.00"))


def test_register_product_duplicate_sku():
    """
    Business Logic Guardrail: Validates that unique catalog constraint safeguards 
    reject registrations containing an already taken SKU.
    """
    # Arrange: Initialize mock infrastructure
    session_mock = MagicMock(spec=Session)
    
    with MagicMock() as mock_get_sku:
        import services.catalog_service
        services.catalog_service.get_product_by_sku = mock_get_sku
        
        # FIX: Mock the existing product entity to fully avoid __init__ requirements
        existing_product_mock = MagicMock()
        existing_product_mock.id = 99
        existing_product_mock.sku = "DUPLICATE"
        mock_get_sku.return_value = existing_product_mock

        # Act & Assert: Verify that a duplicate registration attempt throws the proper domain exception
        with pytest.raises(ValueError, match="Business Logic Error: Product SKU 'DUPLICATE' already exists in the catalog."):
            register_product(session_mock, "DUPLICATE", "Clone Item", Decimal("15.00"))


# -------------------------------------------------------------------------
# TESTS: modify_product
# -------------------------------------------------------------------------

def test_modify_product_success():
    """
    Happy Path Scenario: Verifies that partial updates to an existing product 
    propagate correctly into the data storage abstraction layer.
    """
    # Arrange: Setup mock context and instantiate baseline mock data entity
    session_mock = MagicMock(spec=Session)
    
    # FIX: Use MagicMock instead of real model class
    existing_product_mock = MagicMock()
    existing_product_mock.id = 1
    existing_product_mock.sku = "EXISTING"

    with MagicMock() as mock_get_id:
        import services.catalog_service
        services.catalog_service.get_product_by_id = mock_get_id
        mock_get_id.return_value = existing_product_mock
        
        mock_update = MagicMock()
        services.catalog_service.update_product = mock_update

        # Act: Execute update routine mutating the product name and net price fields
        modify_product(session_mock, product_id=1, name="New Name", unit_price_ex_vat=Decimal("12.50"))

        # Assert: Validate that updated values are handed down while unprovided values remain untouched
        mock_update.assert_called_once_with(
            session=session_mock,
            product_id=1,
            name="New Name",
            unit_price_ex_vat=Decimal("12.50"),
            default_vat_rate=None  # Argument omitted from call, ensuring no accidental modifications
        )


def test_modify_product_not_found():
    """
    Business Logic Guardrail: Ensures that modifications targeting 
    a missing product identifier fail gracefully.
    """
    # Arrange: Initialize standalone mock session
    session_mock = MagicMock(spec=Session)

    with MagicMock() as mock_get_id:
        import services.catalog_service
        services.catalog_service.get_product_by_id = mock_get_id
        
        # Simulate query miss returning None from the repository layer
        mock_get_id.return_value = None  

        # Act & Assert: Enforce structured error handling responses for 404 domain misses
        with pytest.raises(ValueError, match="Business Logic Error: Product not found."):
            modify_product(session_mock, product_id=404, name="Ghost Update")


def test_modify_product_invalid_price():
    """
    Business Rule Reinforcement: Ensures that update pipelines block 
    and reject incoming requested price drops below or equal to zero.
    """
    # Arrange: Construct baseline mocked dependencies
    session_mock = MagicMock(spec=Session)
    
    # FIX: Use MagicMock
    existing_product_mock = MagicMock()
    existing_product_mock.id = 1

    with MagicMock() as mock_get_id:
        import services.catalog_service
        services.catalog_service.get_product_by_id = mock_get_id
        mock_get_id.return_value = existing_product_mock

        # Act & Assert: Validate that updating prices to zero triggers a business error block
        with pytest.raises(ValueError, match="Business Logic Error: Updated unit price ex-VAT must be strictly greater than 0."):
            modify_product(session_mock, product_id=1, unit_price_ex_vat=Decimal("0.00"))


def test_modify_product_negative_vat():
    """
    Business Rule Reinforcement: Ensures that update pipelines block 
    and reject updates containing a negative tax specification.
    """
    # Arrange: Build test boundary context
    session_mock = MagicMock(spec=Session)
    
    # FIX: Use MagicMock
    existing_product_mock = MagicMock()
    existing_product_mock.id = 1

    with MagicMock() as mock_get_id:
        import services.catalog_service
        services.catalog_service.get_product_by_id = mock_get_id
        mock_get_id.return_value = existing_product_mock

        # Act & Assert: Confirm that updating VAT to a negative percentage value is caught by guardrails
        with pytest.raises(ValueError, match="Business Logic Error: Updated VAT rate cannot be negative."):
            modify_product(session_mock, product_id=1, default_vat_rate=Decimal("-5.00"))