from pydantic import BaseModel, ConfigDict


class ConsentState(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    consent_granted: bool = False
    external_allowed: bool = False
    external_last_notice_version: int = 0


class ConsentUpdate(BaseModel):
    consent_granted: bool | None = None
    external_allowed: bool | None = None
