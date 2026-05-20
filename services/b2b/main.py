from fastapi import FastAPI
from api.sku import router as sku_router
from api.invoice import router as invoice_router
from api.products import router as product_router
from api.categories import router as category_router
from api.auth import router as auth_router
from middlewares.token_verification import verify_token


app = FastAPI(
	title="NeoMarket B2B API",
	description="API для кабинета продавца: управление товарами и складом",
	version="1.0.0",
)

app.middleware("http")(verify_token)
app.include_router(product_router, prefix="/api/v1")
app.include_router(category_router, prefix="/api/v1")
app.include_router(sku_router, prefix="/api/v1")
app.include_router(invoice_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")


@app.get("/")
def read_root() -> dict[str, str]:
	return {"service": "NeoMarket B2B", "status": "online", "documentation": "/docs"}
