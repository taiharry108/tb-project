from typing import Optional
from pydantic import BaseModel


class Anime(BaseModel):
    id: Optional[int]
    name: str
    eps: str
    year: str
    season: str
    sub: str
    url: Optional[str]

    class Config:
        orm_mode = True

class AnimeBase(Anime):
    pass
