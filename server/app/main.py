from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import router as auth_router
from app.config import settings
from app.database import init_db
from app.routes.a2a import router as a2a_router
from app.routes.agents import router as agents_router
from app.routes.comms import router as comms_router
from app.routes.escalations import router as escalations_router
from app.routes.bridge import router as bridge_router
from app.routes.treasury import router as treasury_router
from app.routes.integrations import router as integrations_router
from app.routes.portal import router as portal_router
from app.routes.vapi import router as vapi_router
from app.routes.vault import router as vault_router
from app.routes.ground_force import router as ground_force_router
from app.routes.laundry import router as laundry_router
from app.routes.value_node import router as value_node_router
from app.routes.voice import router as voice_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    from app.database import SessionLocal
    from app.treasury.acquisitions import seed_default_acquisitions, sync_manifest_to_vault

    async with SessionLocal() as db:
        await seed_default_acquisitions(db)
        await sync_manifest_to_vault(db)
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
app.include_router(vault_router)
app.include_router(integrations_router)
app.include_router(escalations_router)
app.include_router(agents_router)
app.include_router(comms_router)
app.include_router(treasury_router)
app.include_router(bridge_router)
app.include_router(a2a_router)
app.include_router(value_node_router)
app.include_router(laundry_router)
app.include_router(ground_force_router)


@app.get("/health")
async def health() -> dict:
    from pathlib import Path

    vault_ok = Path(settings.vault_path).exists()
    return {
        "status": "ok",
        "service": "command-center",
        "layers": {
            "voice_os": True,
            "vault": vault_ok,
            "n8n_configured": bool(settings.n8n_webhook_base_url),
            "comms_configured": bool(settings.comms_imap_host),
            "agent_first": True,
            "expansion_dry_run": settings.expansion_dry_run,
        },
    }
