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
def scraping_service(
    scraping_service_factory: ScrapingServiceFactory,
) -> MangaSiteScrapingService:
    return scraping_service_factory.get(MangaSiteEnum.CopyManga)


@pytest.fixture
def manga(m_data) -> Manga:
    return Manga(name=m_data["name"], url=m_data["url"])


@pytest.fixture
def chapter(c_data) -> Chapter:
    return Chapter(title=c_data["title"], page_url=c_data["page_url"])


@pytest.mark.parametrize(
    "search_txt,name,url_ending",
    [
        ("火影", "火影忍者", "huoyingrenzhe"),
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
    "m_data", [{"name": "火影忍者", "url": "https://copymanga.tv/comic/huoyingrenzhe"}]
)
async def test_get_chapters(scraping_service: MangaSiteScrapingService, manga: Manga):
    chapters = await scraping_service.get_chapters(str(manga.url))
    assert len(chapters[MangaIndexTypeEnum.CHAPTER]) == 11
    assert len(chapters[MangaIndexTypeEnum.VOLUME]) == 72

    chap = chapters[MangaIndexTypeEnum.CHAPTER][0]
    assert str(chap.page_url).endswith("1089aa80-c955-11e8-88c0-024352452ce0")
    assert chap.title == "第701话"


@pytest.mark.parametrize(
    "m_data", [{"name": "火影忍者", "url": "https://copymanga.tv/comic/huoyingrenzhe"}]
)
async def test_get_meta(scraping_service: MangaSiteScrapingService, manga: Manga):
    meta_data = await scraping_service.get_meta(str(manga.url))

    assert meta_data.last_update == datetime(2018, 10, 6)
    assert meta_data.finished == True
    assert str(meta_data.thum_img).endswith(
        "/huoyingrenzhe/cover/1651423126.jpg.328x422.jpg"
    )
    assert meta_data.latest_chapter == Chapter(
        title="外传：满月照耀下的路",
        page_url="https://copymanga.tv/comic/huoyingrenzhe/chapter/7d915f53-c94d-11e8-88b8-024352452ce0",
    )


@pytest.mark.parametrize(
    "c_data",
    [
        # {
        #     "title": "第701话",
        #     "page_url": "https://copymanga.tv/comic/huoyingrenzhe/chapter/1089aa80-c955-11e8-88c0-024352452ce0",
        # },
        {
            "title": "第246话",
            "page_url": "https://copymanga.tv/comic/yiquanchaoren/chapter/85e4ad20-c634-11ee-b4fd-55b00c27fb36",
        }
    ],
)
async def test_get_page_urls(
    scraping_service: MangaSiteScrapingService, chapter: Chapter
):
    img_urls = await scraping_service.get_page_urls(str(chapter.page_url))
    assert len(img_urls) == 25

    for img_url in img_urls:
        assert ".jpg" in img_url


# @pytest.mark.parametrize("m_data,c_data", [
#     ({"name": "火影忍者", "url": "https://copymanga.tv/comic/huoyingrenzhe"},
#      {"title": "第701话", "page_url": 'https://copymanga.tv/comic/huoyingrenzhe/chapter/1089aa80-c955-11e8-88c0-024352452ce0'})
# ])
# async def test_download_chapter(scraping_service: MangaSiteScrapingService, manga: Manga, chapter: Chapter):
#     items = []
#     async for item in scraping_service.download_chapter(manga, chapter):
#         items.append(item)
#         assert "pic_path" in item
#         assert "idx" in item
