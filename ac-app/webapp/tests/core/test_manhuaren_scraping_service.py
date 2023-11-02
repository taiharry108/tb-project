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
    return scraping_service_factory.get(MangaSiteEnum.ManHuaRen)


@pytest.fixture
def manga(m_data) -> Manga:
    return Manga(name=m_data["name"], url=m_data["url"])


@pytest.fixture
def chapter(c_data) -> Chapter:
    return Chapter(title=c_data["title"], page_url=c_data["page_url"])


@pytest.mark.parametrize(
    "search_txt,name,url_ending",
    [
        ("火影", "火影忍者", "manhua-huoyingrenzhe-naruto/"),
        ("stone", "Dr.STONE", "manhua-dr-stone/"),
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
    [{"name": "火影忍者", "url": "https://www.manhuaren.com/manhua-huoyingrenzhe-naruto/"}],
)
async def test_get_chapters(scraping_service: MangaSiteScrapingService, manga: Manga):
    chapters = await scraping_service.get_chapters(str(manga.url))
    assert len(chapters[MangaIndexTypeEnum.CHAPTER]) == 533
    assert len(chapters[MangaIndexTypeEnum.MISC]) == 20

    chap = chapters[MangaIndexTypeEnum.CHAPTER][0]
    assert str(chap.page_url).endswith("m5196/")
    assert chap.title == "第1卷"


@pytest.mark.parametrize(
    "m_data",
    [{"name": "火影忍者", "url": "https://www.manhuaren.com/manhua-huoyingrenzhe-naruto/"}],
)
async def test_get_meta(scraping_service: MangaSiteScrapingService, manga: Manga):
    meta_data = await scraping_service.get_meta(str(manga.url))

    assert meta_data.last_update == datetime(2016, 4, 23)
    assert meta_data.finished == True
    assert (
        str(meta_data.thum_img)
        == "https://mhfm6us.cdndm5.com/1/444/20181129142416_180x240_30.jpg"
    )
    assert meta_data.latest_chapter == Chapter(
        title="外传：20", page_url="https://www.manhuaren.com/m249654/"
    )


@pytest.mark.parametrize(
    "c_data", [{"title": "第187话", "page_url": "https://www.manhuaren.com/m1199828/"}]
)
async def test_get_page_urls(
    scraping_service: MangaSiteScrapingService, chapter: Chapter
):
    img_urls = await scraping_service.get_page_urls(str(chapter.page_url))
    assert len(img_urls) == 18

    for img_url in img_urls:
        assert img_url.startswith("https://manhua")
        assert ".jpg" in img_url
