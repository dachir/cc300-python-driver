from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


class Payment(BaseModel):
    """Payment information for a bill"""
    mode: Literal["V", "C", "M", "D", "E", "A"] = Field(
        ...,
        description="Payment modes: V=virement, C=carte bancaire, M=Mobile money, D=chèques, E=espèces, A=autre"
    )
    amount: float = Field(..., description="Montant Payé")


class Product(BaseModel):
    """Product/item information for a bill"""
    label: str = Field(..., max_length=60, description="Libellé de l'article")
    bar_code: Optional[str] = Field(None, max_length=24, description="Code Barre de l'article")
    tax: Literal["A", "B", "C", "D", "E", "F"] = Field(
        ...,
        description="Taux d'imposition: A=Exonéré, B=Taxable, C=Exportation, D=TVA régime d'exception, E=Régime fiscal TPS, F=Taxe de séjour"
    )
    price: float = Field(..., description="Prix avec TVA (sans Taxe Spécifique si applicable)")
    items: Optional[float] = Field(None, description="Quantité")
    specific_tax: Optional[float] = Field(None, description="Taxe spécifique, montant total incluant TVA")
    specific_tax_desc: Optional[str] = Field(None, max_length=16, description="Description de Taxe spécifique")
    original_price: Optional[float] = Field(None, description="Prix d'origine en cas de changement de prix")
    price_change_explanation: Optional[str] = Field(None, max_length=24, description="Description du changement de prix")


class BillBase(BaseModel):
    """Base bill information common to all bill types"""
    seller_id: str = Field(..., description="Numero (identifiant) du vendeur")
    seller_name: str = Field(..., max_length=30, description="Nom du vendeur")
    buyer_ifu: Optional[str] = Field(None, description="IFU de l'acheteur")
    buyer_name: Optional[str] = Field(None, description="Nom de l'acheteur")
    aib: Optional[Literal["1%", "5%", "N/A"]] = Field(None, description="AIB de l'acheteur si applicable")
    payments: List[Payment] = Field(..., min_length=1, description="Liste des paiements")
    products: List[Product] = Field(..., min_length=1, description="Liste des produits")


class RefundBill(BillBase):
    """Facture d'avoir (refund bill)"""
    rt: Literal["FA", "CA", "EA", "ER"] = Field(
        ...,
        description="Type de facture d'avoir: FA=Facture d'avoir, CA=Copie, EA=Exportation, ER=Copie exportation"
    )
    rn: str = Field(..., description="Numéro de référence de la facture originale (format NIM-TC)")
    vt: Optional[str] = Field(None, exclude=True)


class SaleBill(BillBase):
    """Facture de vente (sale bill)"""
    vt: Literal["FV", "CV", "EV", "EC"] = Field(
        ...,
        description="Type de facture de vente: FV=Facture de vente, CV=Copie, EV=Exportation, EC=Copie exportation"
    )
    rt: Optional[str] = Field(None, exclude=True)
    rn: Optional[str] = Field(None, exclude=True)


class DeviceInfo(BaseModel):
    """Device and taxpayer information"""
    NIM: str
    IFU: str
    TIME: str
    COUNTER: str
    SellBillCounter: str
    SettlementBillCounter: str
    TaxA: str
    TaxB: str
    TaxC: str
    TaxD: str
    CompanyName: str
    CompanyLocationAddress: str
    CompanyLocationCity: str
    CompanyContactPhone: str
    CompanyContactEmail: str
    LastConnectionToServer: str
    DocumentOnDeviceCount: str
    UploadedDocumentCount: str


class StatusResponse(BaseModel):
    """Simple status response"""
    status: Literal["DeviceNotConnected", "Ready"]


class BillResponse(BaseModel):
    """Bill creation response"""
    qr_code: str
