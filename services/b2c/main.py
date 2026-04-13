from fastapi import FastAPI
from api import category, product, breadcrumbs


app = FastAPI()

app.include_router(category.router)
app.include_router(product.router)
app.include_router(breadcrumbs.router)
