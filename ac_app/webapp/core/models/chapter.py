from typing import Optional
from pydantic import BaseModel, HttpUrl


class ChapterIn(BaseModel):
    id: Optional[int]
    page_url: Optional[HttpUrl]


class Chapter(ChapterIn):
    title: Optional[str]

    class Config:
        orm_mode = True
