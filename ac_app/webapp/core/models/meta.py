from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, HttpUrl
from typing import Union


class Meta(BaseModel):
    last_update: datetime
    finished: bool
    thum_img: Union[HttpUrl, Path]
