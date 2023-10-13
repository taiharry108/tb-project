from pydantic import BaseModel, HttpUrl, ConfigDict

from typing import Optional


class ChapterIn(BaseModel):
    id: Optional[int] = None
    page_url: Optional[HttpUrl]
    model_config = ConfigDict(from_attributes=True)


class Chapter(ChapterIn):
    title: Optional[str]

    model_config = ConfigDict(from_attributes=True)
