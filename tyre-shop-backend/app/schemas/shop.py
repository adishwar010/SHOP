from pydantic import BaseModel

class JoinShopRequest(BaseModel):
    shop_code: str