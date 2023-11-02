import os
import pytest

from datetime import datetime
from logging import getLogger
from pathlib import Path

from core.models.anime import Anime
from core.models.episode import Episode
from core.models.manga_site_enum import MangaSiteEnum

from core.scraping_service import Anime1ScrapingService, ScrapingServiceFactory
from core.scraping_service.anime_site_scraping_service import AnimeSiteScrapingService


logger = getLogger(__name__)


@pytest.fixture
def scraping_service(
    scraping_service_factory: ScrapingServiceFactory,
) -> AnimeSiteScrapingService:
    return scraping_service_factory.get(MangaSiteEnum.Anime1)


@pytest.mark.parametrize(
    "search_text,name,url_ending", [("東方", "ORIENT 東方少年", "cat=978")]
)
async def test_search_anime(
    scraping_service: Anime1ScrapingService,
    search_text: str,
    name: str,
    url_ending: str,
):
    anime_list = await scraping_service.search_anime(search_text)
    assert len(anime_list) != 0

    filtered_list = list(filter(lambda anime: anime.name == name, anime_list))

    assert len(filtered_list) != 0

    for anime in anime_list:
        if anime.name == name:
            assert anime.url.endswith(url_ending)


async def test_get_index_page(scraping_service: Anime1ScrapingService):
    anime = Anime(name="", eps="", year="", season="", sub="", url="?cat=975")
    eps = await scraping_service.get_index_page(anime)
    assert len(eps) >= 19
    logger.info(eps)


async def test_get_video_url(scraping_service: Anime1ScrapingService):
    data = "%7B%22c%22%3A%221125%22%2C%22e%22%3A%226b%22%2C%22t%22%3A1668107495%2C%22p%22%3A0%2C%22s%22%3A%2234cef61dea41e751e22101db8ae87edf%22%7D"
    episode = Episode(title="", last_update=datetime.now(), data=data)
    video_url = await scraping_service.get_video_url(episode)
    assert video_url.endswith("mp4")
    assert video_url.startswith("https://")


async def test_download_episode(
    scraping_service: Anime1ScrapingService,
    tmp_path: Path
):
    anime = Anime(name="", eps="", year="", season="", sub="", url="?cat=975")
    eps = await scraping_service.get_index_page(anime)
    video_url = await scraping_service.get_video_url(eps[0])
    result = await scraping_service.download_service.download_vid(
        url=video_url, download_path=tmp_path
    )
    assert os.path.exists(result["vid_path"])
