from fastapi import FastAPI

from b2b.api.routes.auth import router as auth_router
from b2b.api.routes.sellers import router as sellers_router

app = FastAPI(title="B2B Service")

app.include_router(auth_router)
app.include_router(sellers_router)


@app.get("/")
async def root():
	return {"message": "Hello World"}


@app.get("/health")
async def health():
	return {"status": "ok"}
