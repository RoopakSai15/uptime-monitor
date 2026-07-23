from datetime import datetime

from pydantic import BaseModel, HttpUrl


class URLCreate(BaseModel):
    url: HttpUrl


class URLResponse(BaseModel):
    id: int
    url: str
    created_at: datetime

    model_config = {"from_attributes": True}
