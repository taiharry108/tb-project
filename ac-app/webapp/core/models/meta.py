from datetime import datetime
from .chapter import Chapter
from pathlib import Path
from pydantic import BaseModel, HttpUrl
from typing import Union, Optional


class Meta(BaseModel):
    manga_id: Optional[int] = None
    last_update: Optional[datetime] = None
    finished: Optional[bool] = None
    thum_img: Optional[Union[HttpUrl, Path]] = None
    latest_chapter: Optional[Chapter] = None
