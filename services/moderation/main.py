import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api.b2b_events import router as b2b_events_router
from api.queue import router as queue_router
from api.tickets import router as tickets_router
from core.messaging import run_catalog_consumer_forever, run_outbox_worker_forever
from middlewares.service_key_verification import verify_service_key
from middlewares.token_verification import verify_token


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa
	consumer_task = asyncio.create_task(run_catalog_consumer_forever())
	outbox_task = asyncio.create_task(run_outbox_worker_forever())
	yield
	for task in (consumer_task, outbox_task):
		task.cancel()
		try:
			await task
		except asyncio.CancelledError:
			pass


app = FastAPI(
	title="NeoMarket Moderation API",
	description="Сервис модерации товаров NeoMarket",
	version="1.0.0",
	lifespan=lifespan,
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
	detail = exc.detail
	if isinstance(detail, dict) and "code" in detail and "message" in detail:
		return JSONResponse(
			status_code=exc.status_code,
			content={
				"code": detail["code"],
				"message": detail["message"],
				"details": detail.get("details", []),
			},
			headers=exc.headers,
		)
	return JSONResponse(
		status_code=exc.status_code,
		content={"detail": detail},
		headers=exc.headers,
	)


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
	_request: Request, exc: RequestValidationError
) -> JSONResponse:
	return JSONResponse(
		status_code=422,
		content={
			"code": "VALIDATION_ERROR",
			"message": "Request validation failed",
			"details": exc.errors(),
		},
	)


app.middleware("http")(verify_service_key)
app.middleware("http")(verify_token)
app.include_router(b2b_events_router, prefix="/api/v1")
app.include_router(queue_router, prefix="/api/v1")
app.include_router(tickets_router, prefix="/api/v1")


@app.get("/")
def read_root() -> dict[str, str]:
	return {
		"service": "NeoMarket Moderation",
		"status": "online",
		"documentation": "/docs",
	}
