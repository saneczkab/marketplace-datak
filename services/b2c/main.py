from fastapi import FastAPI
from api import category, product


app = FastAPI()

app.include_router(category.router)
app.include_router(product.router)
