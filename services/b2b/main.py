import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.auth import router as auth_router
from api.categories import router as category_router
from api.images import router as image_router
from api.invoice import router as invoice_router
from api.products import router as product_router
from api.sku import router as sku_router
from core.config import settings
from middlewares.token_verification import verify_token
from services import outbox_worker

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa
	worker_task: asyncio.Task | None = None
	if settings.OUTBOX_WORKER_ENABLED:
		worker_task = asyncio.create_task(outbox_worker.run_forever())
		logger.info("Outbox worker task scheduled")
	yield
	if worker_task is not None:
		worker_task.cancel()
		try:
			await worker_task
		except asyncio.CancelledError:
			pass


app = FastAPI(
	title="NeoMarket B2B API",
	description="API для кабинета продавца: управление товарами и складом",
	version="1.0.0",
	lifespan=lifespan,
)

app.middleware("http")(verify_token)
app.include_router(product_router, prefix="/api/v1")
app.include_router(category_router, prefix="/api/v1")
app.include_router(sku_router, prefix="/api/v1")
app.include_router(invoice_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(image_router, prefix="/api/v1")


@app.get("/")
def read_root() -> dict[str, str]:
	return {"service": "NeoMarket B2B", "status": "online", "documentation": "/docs"}
