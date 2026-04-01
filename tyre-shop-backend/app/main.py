from fastapi import FastAPI
from app.api import auth, shop, admin, inventory, user, dashboard
from app import models  # 🔥 ensures models are loaded

app = FastAPI()

app.include_router(auth.router, prefix="/auth")
app.include_router(shop.router, prefix="/shop")
app.include_router(admin.router, prefix="/admin")  # 🔥 NEW
app.include_router(inventory.router, prefix="/inventory")
app. include_router(user.router, prefix="/users")
app. include_router(dashboard.router, prefix="/dashboard")

@app.get("/")
def root():
    return {"message": "Tyre Shop Backend Running 🚀"}

