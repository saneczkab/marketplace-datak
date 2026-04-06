from fastapi import FastAPI
from api import category


app = FastAPI()

app.include_router(category.router)
