import string

from bs4 import BeautifulSoup
from datetime import datetime
from logging import getLogger
from typing import List, Dict

from core.models.chapter import Chapter
from core.models.manga import Manga
from core.models.manga_index_type_enum import MangaIndexTypeEnum
from core.models.meta import Meta
from core.models.mock import MOCK_CHAPTER, MOCK_MANGA, MOCK_META, MOCK_PAGES
from core.models.site import Site
from core.scraping_service.manga_site_scraping_service import MangaSiteScrapingService

logger = getLogger(__name__)


digs = string.digits + string.ascii_letters


class MockMangaScrapingService(MangaSiteScrapingService):
    def __init__(self):
        self.site: Site = Site(
            id=-1, name="test_manga_site", url="https://www.test-manga-site.com/"
        )
        self._index_page_cache = {}

    async def search_manga(self, keyword: str) -> List[Manga]:
        """Search manga with keyword, return a list of manga"""

        return [MOCK_MANGA]

    @property
    def url(self):
        return str(self.site.url)

    async def extract_meta_from_soup(self, soup: BeautifulSoup, manga_url: str) -> Meta:
        return MOCK_META

    async def get_chapters(
        self, manga_url: str
    ) -> Dict[MangaIndexTypeEnum, List[Chapter]]:
        """Get index page of manga, return a manga with chapters"""

        return {MangaIndexTypeEnum.CHAPTER: [MOCK_CHAPTER]}

    async def get_page_urls(self, chapter_url: str) -> List[str]:
        """Get all the urls of a chaper, return a list of strings"""
        return MOCK_PAGES

    async def _get_index_page(self, manga_url: str) -> BeautifulSoup:
        return None
