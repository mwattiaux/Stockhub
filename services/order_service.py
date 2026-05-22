from decimal import Decimal
from sqlalchemy.orm import Session
from models.order import Order, OrderStatusEnum
from models.invoice import Invoice, InvoiceStatusEnum
from models.stock_movement import MovementTypeEnum
from models.warehouse import WarehouseTypeEnum

from crud.order_crud import get_order_by_id, update_order_status
from crud.order_line_crud import create_order_line
from crud.stock_crud import get_stock_by_warehouse_id_product_id, update_stock_quantity
from crud.invoice_crud import create_invoice
from crud.stock_movement_crud import create_stock_movement

def add_product_to_order(session: Session, order_id: int, product_id: int, quantity: int, price: Decimal):
    """
    Business Logic: Inserts commercial cart items into an order.
    Enforces state immutability patterns dictated by sales workflows.
    """
    order = get_order_by_id(session, order_id)
    if not order:
        raise ValueError("Business Logic Error: Order not found.")
        
    # Business Rule (Modification Condition): Orders can only be altered if status is 'Draft'
    if order.status != OrderStatusEnum.DRAFT:
        raise ValueError("Business Logic Error: Orders can only be modified or deleted if their status is 'Draft'.")
        
    if quantity <= 0:
        raise ValueError("Business Logic Error: Ordered quantity must be strictly positive.")
        
    return create_order_line(session, order_id=order.id, product_id=product_id, quantity=quantity, price=price)

# def modify_order_metadata(session: Session, order_id: int, customer_id: int | None = None, warehouse_id: int | None = None) -> Order:
#     """
#     Business Logic: Updates core order structural properties (Customer or Fulfillment Center).
#     Guards workflow safety constraints during order preparation.
#     """
#     order = get_order_by_id(session, order_id)
#     if not order:
#         raise ValueError("Business Logic Error: Order not found.")

#     # Business Rule (Modification Condition): Protect workflow immutability boundaries
#     if order.status != OrderStatusEnum.DRAFT:
#         raise ValueError("Business Logic Error: Order structural properties are immutable once validated or cancelled.")

#     return update_order(
#         session=session,
#         order_id=order_id,
#         customer_id=customer_id,
#         warehouse_id=warehouse_id
#     )

def validate_and_finalize_order(session: Session, order_id: int):
    """
    Business Logic: The engine room of sales finalization. Orchestrates order checkout workflows:
    1. Validates strict logistical routing bans.
    2. Runs cross-entity physical inventory availability lockdowns.
    3. Triggers atomic data updates (Order locking, material release, financial invoicing).
    """
    order = get_order_by_id(session, order_id)
    if not order:
        raise ValueError("Business Logic Error: Order not found.")
        
    if order.status != OrderStatusEnum.DRAFT:
        raise ValueError("Business Logic Error: Order has already traveled out of modification bounds.")
        
    if not order.order_lines:
        raise ValueError("Business Logic Error: Cannot finalize an order lacking itemized lines.")

    # 1. Blocking Condition (Logistics Restriction): Central warehouses are banned from direct customer shipments
    if order.warehouse.warehouse_type == WarehouseTypeEnum.CENTRAL:
        raise ValueError("Business Logic Error: A warehouse typed as 'Central' cannot directly ship an order to a customer.")

    # 2. Blocking Condition (Stock Availability): Verify physical balance levels across the cart
    allocations = []
    for line in order.order_lines:
        product = line.product # ORM multi-table traversal
        stock = get_stock_by_warehouse_id_product_id(session, order.warehouse_id, product.id)
        
        if not stock or stock.quantity < line.quantity:
            available = stock.quantity if stock else 0
            raise ValueError(
                f"Business Logic Error: Insufficient stock for '{product.name}' in fulfillment center '{order.warehouse.name}' "
                f"(Requested: {line.quantity}, Available physical balance: {available})."
            )
        # Stage mutation variables for safe execution post-validation
        allocations.append((stock, stock.quantity - line.quantity, line))

    # 3. Business Logic (Financial Calculations): Tabulate legal invoicing ledgers via high-precision decimals
    total_ex_vat = Decimal("0.00")
    vat_amount = Decimal("0.00")
    
    for line in order.order_lines:
        line_ex_vat = line.historical_price_ex_vat * Decimal(line.quantity)
        line_vat = line_ex_vat * (line.product.default_vat_rate / Decimal("100.00"))
        
        total_ex_vat += line_ex_vat
        vat_amount += line_vat
        
    total_inc_vat = total_ex_vat + vat_amount

    # 4. Atomic Mutation Phase (Process execution state changes)
    # A. Lock the Order state (Status transitions legally binding and immutable)
    update_order_status(session, order.id, OrderStatusEnum.VALIDATED)
    
    # B. Discharge physical stock balances & generate immutable history audit trail entries
    for stock_obj, new_qty, line in allocations:
        update_stock_quantity(session, order.warehouse_id, line.product_id, new_qty)
        
        # Log allocation movement (Destination warehouse is NULL because it represents a direct customer sale)
        create_stock_movement(
            session=session,
            product_id=line.product_id,
            src_warehouse_id=order.warehouse_id,
            dest_warehouse_id=None,
            quantity=line.quantity,
            movement_type=MovementTypeEnum.SALE,
            reason=f"Order #{order.id} Dispatch Validation"
        )

    # C. Financial Flow Automation: Automatically generate associated accounting Invoice (1-to-1 relationship)
    invoice = create_invoice(
        session=session,
        order_id=order.id,
        total_ex_vat=total_ex_vat,
        vat_amount=vat_amount,
        total_inc_vat=total_inc_vat,
        status=InvoiceStatusEnum.PENDING_PAYMENT # Invoiced workflow sets status initialization to "Pending Payment"
    )

    return invoice

def generate_invoice_html(invoice: Invoice) -> str:
    """
    Business Logic: Generates a clean, professional HTML/CSS template for the invoice.
    This HTML structure is perfectly optimized for browser-based PDF rendering (Ctrl+P) 
    and native Streamlit display.
    """
    order = invoice.order
    customer = order.customer
    warehouse = order.warehouse
    
    # Building itemized rows dynamically using legal data records
    item_rows_html = ""
    for line in order.order_lines:
        line_total_ex_vat = line.historical_price_ex_vat * line.quantity
        item_rows_html += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #ddd;">{line.product.name} (SKU: {line.product.sku})</td>
            <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: center;">{line.quantity}</td>
            <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: right;">{line.historical_price_ex_vat:,.2f} €</td>
            <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: right;">{line.product.default_vat_rate}%</td>
            <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: right;">{line_total_ex_vat:,.2f} €</td>
        </tr>
        """

    # Complete clean accounting template layout
    html_template = f"""
    <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333; max-width: 800px; margin: auto; padding: 30px; border: 1px solid #eee; box-shadow: 0 0 10px rgba(0, 0, 0, 0.15); background-color: #fff;">
        <!-- Invoice Header -->
        <table style="width: 100%; line-height: inherit; text-align: left;" cellspacing="0" cellpadding="0">
            <tr>
                <td style="font-size: 28px; line-height: 35px; font-weight: bold; color: #1e3a8a;">
                    INVOICE / FACTURE
                </td>
                <td style="text-align: right; font-weight: bold;">
                    Invoice ID: #{invoice.id}<br>
                    Date: {invoice.invoice_date.strftime('%Y-%m-%d %H:%M') if invoice.invoice_date else 'N/A'}
                </td>
            </tr>
        </table>
        
        <hr style="border: 0; border-top: 2px solid #1e3a8a; margin: 20px 0;">
        
        <!-- Entity Information CRM & Logistics Mapping -->
        <table style="width: 100%; line-height: 22px; margin-bottom: 30px;" cellspacing="0" cellpadding="0">
            <tr>
                <td style="width: 50%; vertical-align: top;">
                    <strong style="color: #1e3a8a;">Billed To (Customer):</strong><br>
                    {customer.first_name} {customer.last_name}<br>
                    {customer.address}<br>
                    {customer.email}
                </td>
                <td style="width: 50%; vertical-align: top; text-align: right;">
                    <strong style="color: #1e3a8a;">Shipped From (Fulfillment Facility):</strong><br>
                    Warehouse: {warehouse.name}<br>
                    Location: {warehouse.city}<br>
                    Order Reference: #{order.id}
                </td>
            </tr>
        </table>

        <!-- Itemized Legal Financial Summary Table -->
        <table style="width: 100%; text-align: left; border-collapse: collapse; margin-bottom: 30px;" cellspacing="0" cellpadding="0">
            <thead>
                <tr style="background-color: #f8fafc; color: #1e3a8a; font-weight: bold;">
                    <th style="padding: 12px; border-bottom: 2px solid #cbd5e1;">Designation</th>
                    <th style="padding: 12px; border-bottom: 2px solid #cbd5e1; text-align: center;">Qty</th>
                    <th style="padding: 12px; border-bottom: 2px solid #cbd5e1; text-align: right;">Unit Price HT</th>
                    <th style="padding: 12px; border-bottom: 2px solid #cbd5e1; text-align: right;">VAT Rate</th>
                    <th style="padding: 12px; border-bottom: CBD5E1; text-align: right;">Total HT</th>
                </tr>
            </thead>
            <tbody>
                {item_rows_html}
            </tbody>
        </table>

        <!-- Financial Totals Block -->
        <table style="width: 100%; line-height: 24px;" cellspacing="0" cellpadding="0">
            <tr>
                <td style="width: 60%;"></td>
                <td style="width: 40%;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 6px 0; border-bottom: 1px solid #eee;"><strong>Total Ex-VAT (Net):</strong></td>
                            <td style="text-align: right; padding: 6px 0; border-bottom: 1px solid #eee;">{invoice.total_ex_vat:,.2f} €</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 0; border-bottom: 1px solid #eee;"><strong>VAT Amount (TVA):</strong></td>
                            <td style="text-align: right; padding: 6px 0; border-bottom: 1px solid #eee;">{invoice.vat_amount:,.2f} €</td>
                        </tr>
                        <tr style="font-size: 18px; color: #1e3a8a;">
                            <td style="padding: 10px 0;"><strong>Total Inc-VAT (Gross):</strong></td>
                            <td style="text-align: right; padding: 10px 0;"><strong>{invoice.total_inc_vat:,.2f} €</strong></td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        
        <!-- Legal Footer Note -->
        <div style="margin-top: 50px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 15px;">
            Thank you for your business. Payment Status: <strong>{invoice.status}</strong>.<br>
            Generated automatically by the Logistics ERP System.
        </div>
    </div>
    """
    return html_template