from datetime import datetime

from pydantic import BaseModel, HttpUrl

from typing import Optional


class URLCreate(BaseModel):
    url: HttpUrl


class HealthCheckResponse(BaseModel):
    id: int
    status_code: Optional[int] = None
    response_time_ms: Optional[int] = None
    is_up: bool
    checked_at: datetime

    model_config = {"from_attributes": True}


class URLResponse(BaseModel):
    id: int
    url: str
    created_at: datetime

    is_up: Optional[bool] = None
    status_code: Optional[int] = None
    response_time_ms: Optional[int] = None
    last_checked_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
