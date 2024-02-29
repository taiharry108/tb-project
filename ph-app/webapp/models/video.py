from pydantic import BaseModel
from typing import Optional


class Video(BaseModel):
    vid_id: Optional[str] = None
    title: str
    thumbnail: str
    thumbnail_path: Optional[str] = None
    duration: str
    username: str
    upload_date: str

    class Config:
        from_attributes = True
