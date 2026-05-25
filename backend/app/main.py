from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routers import admin_deals, admin_items, admin_offers, health, offers, public, files
from app.core.config import settings

app = FastAPI(
    title="Paperclip House API",
    version="0.1.0",
)

app.mount(
    "/uploads",
    StaticFiles(directory=settings.upload_dir),
    name="uploads",
)

app.include_router(health.router, prefix="/api")
app.include_router(offers.router, prefix="/api")
app.include_router(public.router, prefix="/api")
app.include_router(admin_offers.router, prefix="/api")
app.include_router(admin_items.router, prefix="/api")
app.include_router(admin_deals.router, prefix="/api")
app.include_router(files.router, prefix="/api")