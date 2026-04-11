from fastapi import FastAPI
from api.sku import router as sku_router

app = FastAPI()

app.include_router(sku_router)

@app.get("/")
def read_root() -> dict[str, str]:
    return { "Hello": "World"}