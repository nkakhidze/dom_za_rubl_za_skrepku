from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routers import (
    admin_deals,
    admin_items,
    admin_offers,
    admin_users,
    auth,
    deals,
    files,
    health,
    internal_telegram,
    legal,
    offers,
    public,
    items,
    users,
)
from app.core.config import settings

app = FastAPI(
    title="Paperclip House API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/uploads",
    StaticFiles(directory=settings.upload_dir),
    name="uploads",
)

app.include_router(health.router, prefix="/api")
app.include_router(internal_telegram.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(offers.router, prefix="/api")
app.include_router(items.router, prefix="/api")
app.include_router(deals.router, prefix="/api")
app.include_router(public.router, prefix="/api")
app.include_router(legal.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(admin_offers.router, prefix="/api")
app.include_router(admin_users.router, prefix="/api")
app.include_router(admin_items.router, prefix="/api")
app.include_router(admin_deals.router, prefix="/api")
app.include_router(files.router, prefix="/api")
