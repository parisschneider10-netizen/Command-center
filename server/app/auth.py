from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()
ALGORITHM = "HS256"


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    return jwt.encode(
        {"sub": username, "exp": expire},
        settings.secret_key,
        algorithm=ALGORITHM,
    )


def verify_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    return verify_token(credentials.credentials)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    username = body.username.strip().lower()
    expected = settings.portal_username.strip().lower()
    if username != expected or body.password != settings.portal_password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token(expected))
