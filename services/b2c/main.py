import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import category, product, breadcrumbs, cart
from config import settings

# Configure logging
if settings.debug:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logging.getLogger("uvicorn").setLevel(logging.DEBUG)
    logging.getLogger("uvicorn.access").setLevel(logging.DEBUG)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

app = FastAPI(debug=settings.debug)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
)

app.include_router(category.router)
app.include_router(product.router)
app.include_router(breadcrumbs.router)
app.include_router(cart.router)
app.include_router(cart.validate_router)
