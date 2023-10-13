from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional


class History(BaseModel):
    user_id: int
    manga_id: int
    chapter_id: Optional[int]
    last_added: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
