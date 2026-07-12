from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.integrations.n8n import trigger_n8n
from app.services import log_activity
from app.vault import list_notes, read_note, write_inbox_note

router = APIRouter(prefix="/vault", tags=["vault"])


class VaultNoteCreate(BaseModel):
    title: str
    body: str
    source: str = "api"


class VaultNoteOut(BaseModel):
    filename: str
    folder: str
    path: str
    size_bytes: int
    modified_at: str


@router.post("/notes")
async def create_note(
    body: VaultNoteCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
) -> dict:
    path = write_inbox_note(body.title, body.body, source=body.source)
    await log_activity(
        db,
        "vault_note_created",
        f"Vault note: {body.title}",
        {"path": str(path.name), "folder": "inbox"},
    )
    return {"ok": True, "path": str(path.name), "folder": "inbox"}


@router.get("/notes", response_model=list[VaultNoteOut])
async def get_notes(
    folder: str = "inbox",
    limit: int = 50,
    _: str = Depends(get_current_user),
) -> list[dict]:
    allowed = {"inbox", "tasks", "research", "decisions", "projects"}
    if folder not in allowed:
        raise HTTPException(status_code=400, detail=f"Folder must be one of: {allowed}")
    return list_notes(folder, limit)


@router.get("/notes/{folder}/{filename}")
async def get_note(
    folder: str,
    filename: str,
    _: str = Depends(get_current_user),
) -> dict:
    content = read_note(folder, filename)
    if content is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"folder": folder, "filename": filename, "content": content}
