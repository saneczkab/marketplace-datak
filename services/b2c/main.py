from fastapi import FastAPI
from api import category, product, breadcrumbs, cart


app = FastAPI()

app.include_router(category.router)
app.include_router(product.router)
app.include_router(breadcrumbs.router)
app.include_router(cart.router)
app.include_router(cart.validate_router)
