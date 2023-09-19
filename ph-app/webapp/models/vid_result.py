from pathlib import Path
from pydantic import BaseModel
from typing import List

from models.video import Video


class VidResult(BaseModel):
    vids: List[Video]
    filepath: Path
    vid: Video
