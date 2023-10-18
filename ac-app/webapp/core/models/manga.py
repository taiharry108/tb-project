from datetime import datetime
from pydantic import BaseModel, HttpUrl, ConfigDict
from typing import Dict, List, Optional

from .chapter import Chapter
from .manga_index_type_enum import MangaIndexTypeEnum


class MangaBase(BaseModel):
    id: Optional[int] = None
    name: str
    url: HttpUrl
    model_config = ConfigDict(from_attributes=True)


class MangaWithMeta(MangaBase):
    last_update: Optional[datetime] = None
    finished: Optional[bool] = None
    thum_img: Optional[str] = None
    idx_retrieved: Optional[bool] = False
    model_config = ConfigDict(from_attributes=True)

    def retreived_idx_page(self):
        self.idx_retrieved = True

    def set_meta_data(self, meta_data: dict, create_last_update=True):
        self.last_update = (
            datetime.now() if create_last_update else meta_data.get("last_update")
        )
        self.finished = meta_data.get("finished")
        self.thum_img = meta_data.get("thum_img")
        if self.thum_img is not None:
            self.thum_img = self.thum_img.replace("static/", "")


class Manga(MangaWithMeta):
    chapters: Dict[MangaIndexTypeEnum, List[Chapter]] = {
        m_type: [] for m_type in list(MangaIndexTypeEnum)
    }

    def add_chapter(self, m_type: MangaIndexTypeEnum, title: str, page_url: str):
        self.chapters[m_type].append(Chapter(title=title, page_url=page_url))

    def get_chapter(self, m_type: MangaIndexTypeEnum, idx: int) -> Chapter:
        return self.chapters[m_type][idx]


class MangaSimple(MangaWithMeta):
    latest_chapter: Optional[Chapter] = None
    last_read_chapter: Chapter = None
    last_added: datetime = None
    is_fav: bool = False


class MangaWithSite(BaseModel):
    id: int
    url: HttpUrl
    manga_site_name: str
    manga_name: str

    model_config = ConfigDict(from_attributes=True)
