from app.db.session import SessionLocal
from app.models.user import User
from app.models.shop import Shop  # keep this import
from app.core.security import hash_password
from app.core.constants import Roles

db = SessionLocal()

admin = User(
    name="Admin",
    email="admin@tyreshop.com",
    password=hash_password("admin123"),
    role=Roles.ADMIN,
    status="APPROVED"   # 🔥 FIX HERE
)

db.add(admin)
db.commit()

print("✅ Admin created successfully")