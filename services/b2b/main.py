from fastapi import FastAPI
from api.products import router as product_router
from api.categories import router as category_router
app = FastAPI(
    title="NeoMarket B2B API",
    description="API для кабинета продавца: управление товарами и складом",
    version="1.0.0"
)

app.include_router(product_router, prefix="/api/v1")
app.include_router(category_router, prefix="/api/v1")



@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "service": "NeoMarket B2B",
        "status": "online",
        "documentation": "/docs"
    }