from fastapi import APIRouter, Depends
from sqlmodel import Session
from db.database import get_session
from core.memory import get_full_profile, upsert_profile, PROFILE_KEYS
from pydantic import BaseModel

router = APIRouter(prefix="/api/profile", tags=["profile"])


class ProfileUpdate(BaseModel):
    key: str
    value: str


@router.get("")
def get_profile(session: Session = Depends(get_session)):
    profile = get_full_profile(session)
    # Return all keys, empty string if not set
    return {k: profile.get(k, "") for k in PROFILE_KEYS}


@router.post("")
def update_profile(body: ProfileUpdate, session: Session = Depends(get_session)):
    if body.key not in PROFILE_KEYS:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Unknown profile key: {body.key}")
    upsert_profile(session, body.key, body.value)
    return {"status": "ok", "key": body.key}


@router.post("/bulk")
def bulk_update_profile(body: dict[str, str], session: Session = Depends(get_session)):
    for key, value in body.items():
        if key in PROFILE_KEYS:
            upsert_profile(session, key, value)
    return {"status": "ok"}
