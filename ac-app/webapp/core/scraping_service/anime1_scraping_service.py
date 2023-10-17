from datetime import datetime
from logging import getLogger
from time import time
from typing import List, Optional
from urllib.parse import unquote, urljoin

from bs4.element import Tag
from core.models.site import Site
from core.models.anime import Anime
from core.models.episode import Episode
from core.scraping_service.anime_site_scraping_service import AnimeSiteScrapingService

from download_service import DownloadService

logger = getLogger(__name__)
ANIME1_SEARCH_RESULT_KEYS = ["name", "eps", "year", "season", "sub"]


class Anime1ScrapingService(AnimeSiteScrapingService):
    def __init__(self, download_service: DownloadService):
        self.site = Site(id=2, name="anime1", url="https://anime1.me/")
        self._download_service = download_service

    async def search_anime(self, keyword: str) -> List[Anime]:
        """Search manga with keyword, return a list of manga"""

        def process_item(item) -> Anime:
            item_dict = {key: i for key, i in zip(ANIME1_SEARCH_RESULT_KEYS, item[1:])}
            item_dict["url"] = f"?cat={item[0]}"
            return Anime(**item_dict)

        url = f"https://d1zquzjgwo9yb.cloudfront.net/?_={int(time() * 1000)}"
        data = await self.download_service.get_json(url)
        anime_list = [process_item(item) for item in data]

        return [anime for anime in anime_list if keyword in anime.name]

    async def get_index_page(self, anime: Anime) -> List[Episode]:
        """Get index page of anime, return a manga with chapters"""

        def process_ep(article: Tag):
            title = article.find("h2", {"class": "entry-title"}).get_text()
            last_update = article.find("time", {"class": "updated"}).get_text()
            data = (
                article.find("div", {"class": "vjscontainer"})
                .find("video")
                .get("data-apireq")
            )
            last_update = datetime.strptime(last_update, "%Y-%m-%d")

            return Episode(**{"title": title, "last_update": last_update, "data": data})

        eps = []
        url = urljoin(self.site.url, anime.url)

        while True:
            logger.info(f"going to donwload from {url}")
            soup = await self.download_service.get_soup(url, follow_redirects=True)
            eps += [process_ep(article) for article in soup.find_all("article")]

            div = soup.find("div", {"class": "nav-previous"})
            if div:
                url = div.find("a").get("href")
            else:
                break
        return eps

    async def get_video_url(self, ep: Episode) -> Optional[str]:
        """Get all the urls of a chaper, return a list of strings"""
        data = {"d": unquote(ep.data)}
        logger.debug(f"{data=}")
        json_result = await self.download_service.post_json(
            "https://v.anime1.me/api", data=data
        )
        logger.debug(f"{json_result=}")
        if json_result:
            return "https:" + json_result["s"][0]["src"]

        return None
