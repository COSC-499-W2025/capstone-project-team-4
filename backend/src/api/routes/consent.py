from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.models.schemas.consent import ConsentState, ConsentUpdate
from src.repositories.config_repository import ConfigRepository

router = APIRouter(tags=["consent"])


def _as_bool(v: str | None, default: bool = False) -> bool:
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "y", "on")


@router.get("/consent", response_model=ConsentState)
def get_consent(db: Session = Depends(get_db)) -> ConsentState:
    repo = ConfigRepository(db)
    return ConsentState(
        consent_granted=_as_bool(repo.get("consent_granted"), False),
        external_allowed=_as_bool(repo.get("external_allowed"), False),
        external_last_notice_version=int(repo.get("external_last_notice_version") or 0),
    )


@router.put("/consent", response_model=ConsentState)
def update_consent(payload: ConsentUpdate, db: Session = Depends(get_db)) -> ConsentState:
    repo = ConfigRepository(db)

    before = ConsentState(
        consent_granted=_as_bool(repo.get("consent_granted"), False),
        external_allowed=_as_bool(repo.get("external_allowed"), False),
        external_last_notice_version=int(repo.get("external_last_notice_version") or 0),
    )

    changed = False

    if payload.consent_granted is not None and payload.consent_granted != before.consent_granted:
        repo.set("consent_granted", "true" if payload.consent_granted else "false")
        changed = True

    if payload.external_allowed is not None and payload.external_allowed != before.external_allowed:
        repo.set("external_allowed", "true" if payload.external_allowed else "false")
        changed = True

    if changed:
        repo.bump_notice_version()

    return get_consent(db)
