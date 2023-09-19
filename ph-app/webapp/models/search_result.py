from pydantic import BaseModel
from typing import List

from models.video import Video


class SearchResult(BaseModel):
    vids: List[Video]
    next_page: int
