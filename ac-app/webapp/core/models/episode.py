from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional


class Episode(BaseModel):
    id: Optional[int] = None
    title: str
    last_update: datetime
    data: str
    model_config = ConfigDict(from_attributes=True)
