import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from api.v1.routes import auth, health, internal, seller
from core.config import settings
from core.database import init_db
from core.middleware import VerifyTokenMiddleware

# Configure logging
logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
	logger.info("Starting up B2B service...")
	await init_db()
	logger.info("Database initialized")
	yield
	logger.info("Shutting down B2B service...")


app = FastAPI(
	title="B2B Service",
	description="Business-to-Business service for sellers",
	version="1.0.0",
	lifespan=lifespan,
)

# Add middleware
app.add_middleware(VerifyTokenMiddleware)

# Include routers
app.include_router(health.router, prefix=settings.API_V1_PREFIX)
app.include_router(internal.router, prefix=settings.API_V1_PREFIX)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(seller.router, prefix=settings.API_V1_PREFIX)

# Initialize Prometheus metrics
Instrumentator().instrument(app).expose(app)


@app.get("/")
async def root():
	return {
		"service": "B2B Service",
		"version": "1.0.0",
		"docs": "/docs",
		"health": f"{settings.API_V1_PREFIX}/health",
	}
