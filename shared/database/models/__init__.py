# Импортируем базу
from shared.database.core import Base

# Импортируем все модели
from .identity.user import User
from .catalog.base import Category, Product
from .catalog.variants import Sku, Characteristic, Image
from .catalog.inventory import Invoice, InvoiceItem
from .cart.item import CartItem
from .personal.profile import Favorite, Subscription
from .storefront.main import Banner, Collection, CollectionProduct

# Теперь Alembic видит всё через Base.metadata
__all__ = [
    "Base",
    "User",
    "Category",
    "Product",
    "Sku",
    "Characteristic",
    "Image",
    "Invoice",
    "InvoiceItem",
    "CartItem",
    "Favorite",
    "Subscription",
    "Banner",
    "Collection",
    "CollectionProduct",
]