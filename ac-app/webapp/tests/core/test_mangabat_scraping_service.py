from datetime import datetime
import pytest

from core.models.chapter import Chapter
from core.models.manga import Manga
from core.models.manga_site_enum import MangaSiteEnum
from core.models.manga_index_type_enum import MangaIndexTypeEnum
from core.scraping_service import ScrapingServiceFactory
from core.scraping_service.manga_site_scraping_service import MangaSiteScrapingService

from logging import getLogger

logger = getLogger(__name__)


@pytest.fixture
def scraping_service(scraping_service_factory: ScrapingServiceFactory):
    return scraping_service_factory.get(MangaSiteEnum.MangaBat)


@pytest.fixture
def manga(m_data) -> Manga:
    return Manga(name=m_data["name"], url=m_data["url"])


@pytest.fixture
def chapter(c_data) -> Chapter:
    return Chapter(title=c_data["title"], page_url=c_data["page_url"])


@pytest.mark.parametrize(
    "search_txt,name,url_ending",
    [
        ("mamayuyu", "Mamayuyu", "read-za403893"),
    ],
)
async def test_search_manga(
    scraping_service: MangaSiteScrapingService,
    search_txt: str,
    name: str,
    url_ending: str,
):
    manga_list = await scraping_service.search_manga(search_txt)
    assert len(manga_list) != 0

    filtered_list = list(filter(lambda manga: manga.name == name, manga_list))
    assert len(filtered_list) != 0

    for manga in manga_list:
        if manga.name == name:
            assert str(manga.url).endswith(url_ending)


@pytest.mark.parametrize(
    "m_data",
    [{"name": "Mamayuyu", "url": "https://readmangabat.com/read-za403893"}],
)
async def test_get_chapters(scraping_service: MangaSiteScrapingService, manga: Manga):
    chapters = await scraping_service.get_chapters(str(manga.url))
    assert len(chapters[MangaIndexTypeEnum.CHAPTER]) == 23

    chap = chapters[MangaIndexTypeEnum.CHAPTER][0]
    assert str(chap.page_url).endswith("read-za403893-chap-23")
    assert chap.title == "Chapter 23"


@pytest.mark.parametrize(
    "m_data",
    [{"name": "Naruto", "url": "https://readmangabat.com/read-sl358578"}],
)
async def test_get_meta(scraping_service: MangaSiteScrapingService, manga: Manga):
    meta_data = await scraping_service.get_meta(str(manga.url))

    assert meta_data.last_update == datetime(2022, 4, 26, 23, 58)
    assert meta_data.finished == True
    assert (
        str(meta_data.thum_img) == "https://avt.mkklcdnv6temp.com/48/g/1-1583465604.jpg"
    )
    assert meta_data.latest_chapter == Chapter(
        title="Chapter 700.5 : Uzumaki Naruto",
        page_url="https://readmangabat.com/read-sl358578-chap-700.5",
    )


@pytest.mark.parametrize(
    "c_data",
    [
        {
            "title": "Chapter 700.5 : Uzumaki Naruto",
            "page_url": "https://readmangabat.com/read-sl358578-chap-700.5",
        }
    ],
)
async def test_get_page_urls(
    scraping_service: MangaSiteScrapingService, chapter: Chapter
):
    img_urls = await scraping_service.get_page_urls(str(chapter.page_url))
    assert len(img_urls) == 18

    for img_url in img_urls:
        assert img_url.endswith("-o.jpg")
