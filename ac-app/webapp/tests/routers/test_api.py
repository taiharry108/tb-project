import json
import pytest

from httpx import AsyncClient
from logging import getLogger
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Any

from core.models.manga_site_enum import MangaSiteEnum
from core.models.manga import MangaSimple
from database import CRUDService
from database import DatabaseService
from database.models import MangaSite, Manga, Chapter, Page, Episode, Anime

from routers.api import save_pages
from routers.db_utils import get_manga_site_id

logger = getLogger(__name__)


@pytest.fixture(scope="module")
def search_path():
    return "/api/search"


@pytest.fixture(scope="module")
def chapters_path():
    return "/api/chapters"


@pytest.fixture(scope="module")
def episodes_path():
    return "/api/episodes"


@pytest.fixture(scope="module")
def episode_path():
    return "/api/episode"


@pytest.fixture(scope="module")
def manga_path():
    return "/api/manga"


@pytest.fixture(scope="module")
def meta_path():
    return "/api/meta"


@pytest.fixture(scope="module")
def pages_path():
    return "/api/pages"


@pytest.fixture(scope="module")
def manga_name():
    return "火影忍者"


@pytest.fixture(scope="module")
def anime_name():
    return "朋友遊戲"


@pytest.fixture(scope="module")
def pic_path():
    return "test.png"


@pytest.fixture(scope="module")
def manga_url():
    return "https://www.manhuaren.com/manhua-huoyingrenzhe-naruto/"


@pytest.fixture(scope="module")
def anime_url():
    return "?cat=1029"


@pytest.fixture(scope="module")
def chapter_url():
    return "https://www.manhuaren.com/m208255/"


@pytest.fixture(scope="module")
def manga_site() -> MangaSiteEnum:
    return MangaSiteEnum.ManHuaRen


@pytest.fixture(scope="module")
def anime_site() -> MangaSiteEnum:
    return MangaSiteEnum.Anime1


@pytest.fixture(autouse=True, scope="module")
async def run_before_and_after_tests(database: DatabaseService):
    import main

    async with database.session() as session:
        async with session.begin():
            await session.execute(delete(Episode))
            await session.execute(delete(Anime))
            await session.execute(delete(Page))
            await session.execute(delete(Chapter))
            await session.execute(delete(Manga))
            await session.execute(delete(MangaSite))
            session.add(MangaSite(name="manhuaren", url="https://www.manhuaren.com/"))
            session.add(MangaSite(name="anime1", url="https://anime1.me/"))
            await session.commit()
    yield
    main.app.dependency_overrides = {}


async def test_get_manga_site_id(
    manga_site: MangaSiteEnum, db_session: AsyncSession, crud_service: CRUDService
):
    result = await db_session.execute(
        select(MangaSite).where(MangaSite.name == manga_site.value)
    )
    db_manga_site: MangaSite = result.one()[0]

    site_id = await get_manga_site_id(
        manga_site, session=db_session, crud_service=crud_service
    )
    assert db_manga_site.id == site_id


async def test_search_anime(
    search_path: str,
    client: AsyncClient,
    anime_name: str,
    anime_url: str,
    anime_site: MangaSiteEnum,
    crud_service: CRUDService,
    db_session: AsyncSession,
):
    resp = await client.get(
        search_path, params={"site": anime_site.value, "keyword": anime_name}
    )
    for item in resp.json():
        if item["name"] == anime_name:
            break

    assert item["url"] == anime_url
    assert item["id"] is not None

    db_anime = await crud_service.get_item_by_attr(db_session, Anime, "url", anime_url)
    db_anime.id == item["id"]


async def test_search_manga(
    manga_name: str,
    manga_url: str,
    search_path: str,
    client: AsyncClient,
    manga_site: MangaSiteEnum,
    crud_service: CRUDService,
    db_session: AsyncSession,
):
    resp = await client.get(
        search_path, params={"site": manga_site.value, "keyword": manga_name}
    )
    for item in resp.json():
        if item["name"] == manga_name:
            break

    assert item["url"] == manga_url
    assert item["id"] is not None

    db_manga = await crud_service.get_item_by_attr(db_session, Manga, "url", manga_url)
    db_manga.id == item["id"]


async def test_get_chapters_successful(
    manga_url: str,
    chapters_path: str,
    client: AsyncClient,
    crud_service: CRUDService,
    db_session: AsyncSession,
):
    manga_id = await crud_service.get_id_by_attr(db_session, Manga, "url", manga_url)

    resp = await client.get(chapters_path, params={"manga_id": manga_id})
    chapter_dict: Dict[str, List] = resp.json()
    for _, chapters in chapter_dict.items():
        for chapter in chapters:
            assert "id" in chapter
            assert chapter.get("id") is not None


async def test_get_episodes(
    anime_url: str,
    episodes_path: str,
    client: AsyncClient,
    crud_service: CRUDService,
    db_session: AsyncSession,
):
    anime_id = await crud_service.get_id_by_attr(db_session, Anime, "url", anime_url)
    resp = await client.get(episodes_path, params={"anime_id": anime_id})
    episodes: List[Episode] = resp.json()
    assert len(episodes) == 12


async def test_get_episode(
    anime_url: str,
    episode_path: str,
    client: AsyncClient,
    crud_service: CRUDService,
    db_session: AsyncSession,
):
    anime_id = await crud_service.get_id_by_attr(db_session, Anime, "url", anime_url)
    db_episodes = await crud_service.get_items_by_same_attr(
        db_session, Episode, "anime_id", anime_id
    )
    resp = await client.get(episode_path, params={"episode_id": db_episodes[0].id})
    assert "vid_path" in resp.json()


async def test_get_chapters_manga_nonexistent(
    chapters_path: str,
    client: AsyncClient,
):
    resp = await client.get(chapters_path, params={"manga_id": 12973})
    assert resp.status_code == 406


async def test_get_meta_data_successful(
    manga_site: MangaSite,
    manga_name: str,
    manga_url: str,
    meta_path: str,
    client: AsyncClient,
    crud_service: CRUDService,
    db_session: AsyncSession,
):
    manga_id = await crud_service.get_id_by_attr(db_session, Manga, "url", manga_url)
    resp = await client.get(meta_path, params={"manga_id": manga_id})

    meta_data: Dict[str, Any] = resp.json()
    assert "last_update" in meta_data
    assert "finished" in meta_data
    assert "thum_img" in meta_data

    assert meta_data["last_update"] == "2016-04-23T00:00:00"
    assert meta_data["finished"] == True
    assert f"{manga_site.value}/{manga_name}/thum_img" in meta_data["thum_img"]

    db_manga = await crud_service.get_item_by_id(db_session, Manga, manga_id)

    assert db_manga.thum_img == meta_data["thum_img"]
    assert db_manga.finished == meta_data["finished"]


async def test_get_pages_with_wrong_chapter_id(
    pages_path: str,
    client: AsyncClient,
):
    async with client.stream("GET", pages_path, params={"chapter_id": 999999}) as r:
        assert r.status_code == 406


async def test_get_pages_successful(
    manga_site: MangaSite,
    manga_name: str,
    chapter_url: str,
    pages_path: str,
    client: AsyncClient,
    crud_service: CRUDService,
    db_session: AsyncSession,
):
    chapter_id = await crud_service.get_id_by_attr(
        db_session, Chapter, "page_url", chapter_url
    )
    assert chapter_id
    pic_dict = {}
    async with client.stream("GET", pages_path, params={"chapter_id": chapter_id}) as r:
        async for line in r.aiter_lines():
            if line.startswith("data"):
                result = json.loads(line.replace("data: ", ""))
                if not result:
                    continue
                assert "pic_path" in result
                assert "idx" in result
                assert "total" in result
                assert f"{manga_site.value}/{manga_name}" in result["pic_path"]

                pic_dict[result["idx"]] = result

    pages = await crud_service.get_items_by_same_attr(
        db_session, Page, "chapter_id", chapter_id
    )
    assert pages
    for page in pages:
        idx = page.idx
        assert page.pic_path == pic_dict[idx]["pic_path"]


async def test_save_pages(
    db_session: AsyncSession,
    crud_service: CRUDService,
    chapter_url: str,
    database: DatabaseService,
    pic_path: str,
):
    chapter_id = await crud_service.get_id_by_attr(
        db_session, Chapter, "page_url", chapter_url
    )
    pages = [{"pic_path": pic_path, "idx": 0, "total": 1, "chapter_id": chapter_id}]
    await save_pages(pages, chapter_id, db_session, crud_service)
    async with database.new_session() as session:
        async with session.begin():
            db_page = await crud_service.get_item_by_attr(
                session, Page, "pic_path", "test.png"
            )
            assert db_page
            assert db_page.chapter_id == chapter_id
            assert db_page.total == 1
            await session.execute(delete(Page).where(Page.id == db_page.id))
            await session.commit()


async def test_get_pages_from_db(
    chapter_url: str,
    pages_path: str,
    client: AsyncClient,
    crud_service: CRUDService,
    db_session: AsyncSession,
):
    chapter_id = await crud_service.get_id_by_attr(
        db_session, Chapter, "page_url", chapter_url
    )
    assert chapter_id
    pages = await crud_service.get_items_by_same_attr(
        db_session, Page, "chapter_id", chapter_id
    )
    assert pages
    pages = {page.idx: page for page in pages}
    async with client.stream("GET", pages_path, params={"chapter_id": chapter_id}) as r:
        assert r.headers["crawled"] == "false"
        async for line in r.aiter_lines():
            if line.startswith("data"):
                result = json.loads(line.replace("data: ", ""))
                if not result:
                    continue
                assert "pic_path" in result
                assert result["pic_path"] == pages[result["idx"]].pic_path


async def test_get_manga_successful(
    manga_url: str,
    manga_path: str,
    db_session: AsyncSession,
    crud_service: CRUDService,
    client: AsyncClient,
):
    manga_id = await crud_service.get_id_by_attr(db_session, Manga, "url", manga_url)
    resp = await client.get(manga_path, params={"manga_id": manga_id})
    assert resp.json()
    manga_simple = MangaSimple(**resp.json())
    assert manga_simple.id == manga_id
    assert str(manga_simple.url) == manga_url


async def test_get_manga_failed(manga_path: str, client: AsyncClient):
    resp = await client.get(manga_path, params={"manga_id": -1})
    assert resp.status_code == 406
