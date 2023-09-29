from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Episode(BaseModel):
    id: Optional[int]
    title: str
    last_update: datetime
    data: str

    class Config:
        from_attributes = True
