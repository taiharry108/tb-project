from logging import getLogger
from typing import List, Protocol


from core.models.anime import Anime
from core.models.episode import Episode

from download_service.download_service import DownloadService


logger = getLogger(__name__)


class AnimeSiteScrapingService(Protocol):

    async def search_anime(self, keyword: str) -> List[Anime]:
        """Search manga with keyword, return a list of manga"""

    async def get_index_page(self, anime: Anime) -> List[Episode]:
        """Get index page of anime, return a list of episodes"""

    async def get_video_url(self, ep: Episode) -> str:
        """Get all the urls of a chaper, return a list of strings"""
    
    @property
    def download_service(self) -> DownloadService:
        return self._download_service
