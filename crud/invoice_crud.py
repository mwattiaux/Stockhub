from decimal import Decimal
from models.invoice import Invoice, InvoiceStatusEnum
from sqlalchemy import select
from sqlalchemy.orm import Session



def create_invoice(session: Session, order_id: int, total_ex_vat: Decimal, vat_amount: Decimal, total_inc_vat: Decimal, status: InvoiceStatusEnum) -> Invoice:
    invoice = Invoice(order_id=order_id, total_ex_vat=total_ex_vat, vat_amount=vat_amount, total_inc_vat=total_inc_vat, status=status)
    
    session.add(invoice)
    session.flush()
    
    return invoice

def get_invoice_by_id(session: Session, invoice_id: int) -> Invoice | None:
    stmt = select(Invoice).where(Invoice.id == invoice_id)
    invoice = session.execute(stmt).scalar_one_or_none()
    
    return invoice

def get_invoice_by_order_id(session: Session, order_id: int) -> Invoice | None:
    stmt = select(Invoice).where(Invoice.order_id == order_id)
    invoice = session.execute(stmt).scalar_one_or_none()
    
    return invoice