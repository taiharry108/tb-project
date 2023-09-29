from typing import List, Protocol, Dict, List

from bs4 import BeautifulSoup
from core.models.chapter import Chapter
from core.models.manga import Manga
from core.models.meta import Meta
from core.models.manga_index_type_enum import MangaIndexTypeEnum


class MangaSiteScrapingService(Protocol):
    async def search_manga(self, keyword: str) -> List[Manga]:
        """Search manga with keyword, return a list of manga"""

    async def get_chapters(
        self, manga_url: str
    ) -> Dict[MangaIndexTypeEnum, List[Chapter]]:
        """Get index page of manga, return a manga with chapters"""

    async def get_page_urls(self, chapter_url: str) -> List[str]:
        """Get all the urls of a chaper, return a list of strings"""

    async def extract_meta_from_soup(self, soup: BeautifulSoup) -> Meta:
        """Get meta data for manga"""

    async def _get_index_page(self, manga_url: str):
        assert isinstance(self._index_page_cache, dict)
        if manga_url not in self._index_page_cache:
            soup = await self.download_service.get_soup(manga_url)
            self._index_page_cache[manga_url] = soup
            return soup
        else:
            return self._index_page_cache.pop(manga_url)

    async def get_meta(self, manga_url: str) -> Meta:
        """Get meta data for manga"""
        soup = await self._get_index_page(manga_url)
        return await self.extract_meta_from_soup(soup, manga_url)
