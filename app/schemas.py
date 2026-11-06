
from pydantic import BaseModel, Field
from typing import List, Optional


class InvoiceItem(BaseModel):
    description: str
    quantity: float
    unit: Optional[str] = None
    unit_price: float = Field(ge=0)
    total: float = Field(ge=0)


class InvoiceData(BaseModel):
    is_invoice: bool = Field(
        description="True only if the uploaded document is a genuine invoice."
    )
    
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    supplier_name: Optional[str] = None
    items: List[InvoiceItem] = Field(default_factory=list)
    subtotal: Optional[float] = Field(default=None, ge=0)
    vat: Optional[float] = Field(default=None, ge=0)
    total_amount: Optional[float] = Field(default=None, ge=0)
