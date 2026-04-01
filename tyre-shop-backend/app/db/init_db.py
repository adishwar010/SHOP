from app.db.session import engine, Base

# Import models (VERY IMPORTANT)
from app.models.user import User
from app.models.shop import Shop

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()