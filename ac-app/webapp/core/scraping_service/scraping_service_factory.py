from typing import Union

from core.models.manga_site_enum import MangaSiteEnum
from core.scraping_service.anime_site_scraping_service import (
    AnimeSiteScrapingService as ASSService,
)
from core.scraping_service.anime1_scraping_service import Anime1ScrapingService
from core.scraping_service.copymanga_scraping_service import CopyMangaScrapingService
from core.scraping_service.manga_site_scraping_service import (
    MangaSiteScrapingService as MSSService,
)

from core.scraping_service.manhuaren_scraping_service import ManhuarenScrapingService
from core.scraping_service.mangabat_scraping_service import MangaBatScrapingService


class ScrapingServiceFactory:
    def __init__(
        self,
        anime1: Anime1ScrapingService,
        copymanga: CopyMangaScrapingService,
        manhuaren: ManhuarenScrapingService,
        mangabat: MangaBatScrapingService,
    ):
        self.anime1 = anime1
        self.copymanga = copymanga
        self.manhuaren = manhuaren
        self.mangabat = mangabat

    def get(self, site: MangaSiteEnum) -> Union[MSSService, ASSService]:
        return getattr(self, site.value)
