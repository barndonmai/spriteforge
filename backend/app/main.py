from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
from app.db.session import init_db
from app.services.storage import ensure_storage_root

settings = get_settings()
ensure_storage_root()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    ensure_storage_root()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/storage", StaticFiles(directory=settings.storage_root_path), name="storage")
app.include_router(api_router, prefix=settings.api_v1_prefix)
