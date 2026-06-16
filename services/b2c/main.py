import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api import (
	product,
	breadcrumbs,
	cart,
	catalog,
	favorite,
	subscriptions,
	auth,
	orders,
	event,
)
from core.config import settings
from core.db import get_db
from core.inbox import run_inbox_messages_handling
from core.messaging import run_consumer_forever
from exceptions.category import CategoryNotFoundError
from services import category_service
from middlewares.token_verification import verify_token
from middlewares.x_servive_key_verification import service_key_verification

logger = logging.getLogger(__name__)
# Configure logging
if settings.DEBUG:
	logging.basicConfig(
		level=logging.DEBUG,
		format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
	)
	logging.getLogger("uvicorn").setLevel(logging.DEBUG)
	logging.getLogger("uvicorn.access").setLevel(logging.DEBUG)
	# logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

background_tasks = []


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa
	# Startup: warm up categories tree cache
	try:
		logger.info("Generating categories tree cache")
		db_gen = get_db()
		db = await db_gen.__anext__()
		await category_service.get_categories_tree(db)

	except CategoryNotFoundError as e:
		logger.warning(f"Error generating categories tree cache: {e}")
	except Exception as e:  # noqa
		logger.error(f"Error generating categories tree cache: {e}")

	try:
		# Starting inbox messages handling
		task = asyncio.create_task(run_inbox_messages_handling())
		background_tasks.append(task)
		logger.info("Successfuly started inbox message handling")

	except Exception as e:  # noqa
		logger.error(f"Error while starting message queue: {e}")

	try:
		if settings.RABBITMQ_URL != "None" and settings.RABBITMQ_EXCHANGE != "None":
			task = asyncio.create_task(run_consumer_forever())
			background_tasks.append(task)
			logger.info("Succesfully starter consumer")
	except Exception as e:  # Noqa
		logger.error(f"Error while starting comsumer: {e}")

	yield

	for task in background_tasks:
		task.cancel()
	await asyncio.gather(*background_tasks, return_exceptions=True)

	# Shutdown: cleanup if needed


app = FastAPI(debug=settings.DEBUG, lifespan=lifespan)


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


# Configure CORS
app.add_middleware(
	CORSMiddleware,
	allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Frontend URLs
	allow_credentials=True,
	allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, OPTIONS, etc.)
	allow_headers=["*"],  # Allow all headers
)

app.middleware("http")(verify_token)
app.middleware("http")(service_key_verification)

app.include_router(product.router)
app.include_router(breadcrumbs.router)
app.include_router(cart.router)
app.include_router(favorite.router)
app.include_router(catalog.router)
app.include_router(auth.router)
app.include_router(subscriptions.router)
app.include_router(orders.router)
app.include_router(event.router)
