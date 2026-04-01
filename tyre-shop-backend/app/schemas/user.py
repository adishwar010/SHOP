from pydantic import BaseModel, EmailStr
from datetime import date

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    dob: date | None = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str