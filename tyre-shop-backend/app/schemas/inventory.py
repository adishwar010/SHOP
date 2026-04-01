from pydantic import BaseModel


class CreateTyre(BaseModel):
    brand: str
    size: str
    type: str | None = None


class PurchaseTyre(BaseModel):
    tyre_id: int
    quantity: int
    purchase_price: float


class SellTyre(BaseModel):
    tyre_id: int
    quantity: int
    selling_price: float