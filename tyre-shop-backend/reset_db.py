from app.db.session import engine, Base


from app.models.user import User
from app.models.shop import Shop
from app.models.tyre import Tyre
from app.models.inventory import Inventory
from app.models.purchase import Purchase
from app.models.sale import Sale
from app.models.join_request import JoinRequest

print("Dropping all tables...")
Base.metadata.drop_all(bind=engine)

print("Creating all tables...")
Base.metadata.create_all(bind=engine)

print("Done ✅")