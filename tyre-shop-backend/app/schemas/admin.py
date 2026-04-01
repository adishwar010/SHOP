from pydantic import BaseModel, EmailStr

class CreateShopAdmin(BaseModel):
    name: str
    email: EmailStr
    password: str
    shop_name: str
    gst_number: str