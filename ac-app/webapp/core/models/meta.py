from datetime import datetime
from .chapter import Chapter
from pathlib import Path
from pydantic import BaseModel, HttpUrl
from typing import Union


class Meta(BaseModel):
    last_update: datetime
    finished: bool
    thum_img: Union[HttpUrl, Path]
    latest_chapter: Chapter
