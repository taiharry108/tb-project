from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional

from .episode import Episode


class Anime(BaseModel):
    id: Optional[int]
    name: str
    eps: str
    year: str
    season: str
    sub: str
    url: Optional[str]
    model_config = ConfigDict(from_attributes=True)


class AnimeBase(Anime):
    pass


class AnimeSimple(AnimeBase):
    latest_episode: Episode = None
    last_read_episode: Episode = None
    last_added: datetime = None
