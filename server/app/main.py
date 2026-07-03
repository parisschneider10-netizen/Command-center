from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import router as auth_router
from app.config import settings
from app.database import init_db
from app.routes.portal import router as portal_router
from app.routes.vapi import router as vapi_router
from app.routes.voice import router as voice_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Voice OS + Command Center for one-man empire operations",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(portal_router)
app.include_router(voice_router)
app.include_router(vapi_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "command-center"}
