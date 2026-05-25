from fastapi import FastAPI

from app.api.routers import health, offers, public

app = FastAPI(
    title="Paperclip House API",
    version="0.1.0",
)

app.include_router(health.router, prefix="/api")
app.include_router(offers.router, prefix="/api")
app.include_router(public.router, prefix="/api")