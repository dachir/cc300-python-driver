"""
Pydantic models for CC300 driver API
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class Payment(BaseModel):
    """Payment information"""
    mode: Literal["V", "C", "M", "D", "E", "A"] = Field(
        ...,
        description="Payment mode: V=virement, C=carte bancaire, M=Mobile money, D=chèques, E=espèces, A=autre"
    )
    amount: float = Field(..., description="Payment amount")


class Product(BaseModel):
    """Product information"""
    label: str = Field(..., max_length=60, description="Product label")
    tax: Literal["A", "B", "C", "D", "E", "F"] = Field(
        ...,
        description="Tax rate: A=Exonéré, B=Taxable, C=Export taxable, D=TVA exception, E=TPS, F=Reserved"
    )
    price: float = Field(..., description="Price with VAT")
    bar_code: Optional[str] = Field(None, max_length=24, description="Bar code")
    items: Optional[float] = Field(None, description="Quantity")
    specific_tax: Optional[float] = Field(None, description="Specific tax amount")
    specific_tax_desc: Optional[str] = Field(None, max_length=16, description="Specific tax description")
    original_price: Optional[float] = Field(None, description="Original price if changed")
    price_change_explanation: Optional[str] = Field(None, max_length=24, description="Price change explanation")


class BillBase(BaseModel):
    """Base bill information"""
    seller_id: str = Field(..., description="Seller ID")
    seller_name: str = Field(..., max_length=30, description="Seller name")
    payments: List[Payment] = Field(..., min_length=1, description="Payment methods")
    products: List[Product] = Field(..., min_length=1, description="Products")
    buyer_ifu: Optional[str] = Field(None, description="Buyer IFU")
    buyer_name: Optional[str] = Field(None, description="Buyer name")
    aib: Optional[Literal["1%", "5%", "N/A"]] = Field(None, description="AIB if applicable")


class SellBill(BillBase):
    """Sell bill (facture de vente)"""
    vt: Literal["FV", "CV", "EV", "EC"] = Field(
        ...,
        description="Bill type: FV=Facture de vente, CV=Copy, EV=Export, EC=Export copy"
    )


class RefundBill(BillBase):
    """Refund bill (facture d'avoir)"""
    rt: Literal["FA", "CA", "EA", "ER"] = Field(
        ...,
        description="Bill type: FA=Facture avoir, CA=Copy, EA=Export, ER=Export copy"
    )
    rn: str = Field(..., description="Original bill reference number")


class DeviceInfo(BaseModel):
    """Device information response"""
    NIM: str = Field(..., description="Device NIM")
    IFU: str = Field(..., description="Tax identification number")
    TIME: str = Field(..., description="Device time")
    COUNTER: str = Field(..., description="Bill counter")
    SellBillCounter: str = Field(..., description="Sell bill counter")
    SettlementBillCounter: str = Field(..., description="Settlement bill counter")
    TaxA: str = Field(..., description="Tax rate A")
    TaxB: str = Field(..., description="Tax rate B")
    TaxC: str = Field(..., description="Tax rate C")
    TaxD: str = Field(..., description="Tax rate D")
    CompanyName: str = Field(..., description="Company name")
    CompanyLocationAddress: str = Field(..., description="Company address")
    CompanyLocationCity: str = Field(..., description="Company city")
    CompanyContactPhone: str = Field(..., description="Company phone")
    CompanyContactEmail: str = Field(..., description="Company email")
    LastConnectionToServer: str = Field(..., description="Last server connection")
    DocumentOnDeviceCount: str = Field(..., description="Documents on device")
    UploadedDocumentCount: str = Field(..., description="Uploaded documents")


class StatusResponse(BaseModel):
    """Status response"""
    status: Literal["Ready", "DeviceNotConnected"]


class BillResponse(BaseModel):
    """Bill creation response"""
    qr_code: str = Field(..., description="QR code data")
