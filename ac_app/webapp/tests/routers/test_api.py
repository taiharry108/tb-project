from dependency_injector.wiring import inject, Provider
from httpx import AsyncClient
from logging import getLogger
import pytest
from sqlalchemy import delete, select
from typing import Dict, List, Any

from container import Container
from core.models.manga_site_enum import MangaSiteEnum
from database.crud_service import CRUDService
from database.database_service import DatabaseService
from database.models import MangaSite, Manga, Chapter

from routers.api import _get_manga_site_id

logger = getLogger(__name__)


@pytest.fixture(scope="module")
def search_path(): return "/api/search"


@pytest.fixture(scope="module")
def chapters_path(): return "/api/chapters"


@pytest.fixture(scope="module")
def meta_path(): return "/api/meta"


@pytest.fixture(scope="module")
def manga_name():
    return "火影忍者"


@pytest.fixture(scope="module")
def manga_url():
    return "https://www.manhuaren.com/manhua-huoyingrenzhe-naruto/"


@pytest.fixture(scope="module")
def manga_site() -> MangaSiteEnum:
    return MangaSiteEnum.ManHuaRen


@pytest.fixture(autouse=True, scope="module")
async def run_before_and_after_tests(database: DatabaseService):
    import main

    async with database.session() as session:
        async with session.begin():
            await session.execute(delete(Chapter))
            await session.execute(delete(Manga))
            await session.execute(delete(MangaSite))
            session.add(MangaSite(name="manhuaren",
                        url="https://www.manhuaren.com/"))
            await session.commit()
    yield
    main.app.dependency_overrides = {}


@pytest.fixture(scope="module")
@inject
def scraping_service_factory(scraping_service_factory=Provider[Container.scraping_service_factory]):
    return scraping_service_factory


async def test_get_manga_site_id(manga_site: MangaSiteEnum, database: DatabaseService, crud_service: CRUDService):
    async with database.session() as session:
        async with session.begin():
            result = await session.execute(select(MangaSite).where(MangaSite.name == manga_site.value))
            db_manga_site: MangaSite = result.one()[0]

            site_id = await _get_manga_site_id(manga_site, session=session)
            assert db_manga_site.id == site_id


async def test_search_manga(manga_name: str, manga_url: str,
                            search_path: str, client: AsyncClient,
                            manga_site: MangaSiteEnum,
                            crud_service: CRUDService,
                            database: DatabaseService):
    resp = await client.get(search_path, params={
        "site": manga_site.value,
        "keyword": manga_name
    })
    for item in resp.json():
        if item['name'] == manga_name:
            break

    assert item["url"] == manga_url
    assert item['id'] is not None

    async with database.session() as session:
        async with session.begin():
            db_manga = await crud_service.get_item_by_attr(session, Manga, "url", manga_url)
            db_manga.id == item['id']


async def test_get_chapters_successful(manga_url: str, chapters_path: str,
                                       client: AsyncClient,
                                       crud_service: CRUDService,
                                       database: DatabaseService):
    async with database.session() as session:
        async with session.begin():
            manga_id = await crud_service.get_id_by_attr(session, Manga, "url", manga_url)

    resp = await client.get(chapters_path, params={
        "manga_id": manga_id
    })
    chapter_dict: Dict[str, List] = resp.json()
    for _, chapters in chapter_dict.items():
        for chapter in chapters:
            assert "id" in chapter
            assert chapter.get("id") is not None


async def test_get_chapters_manga_nonexistent(chapters_path: str,
                                              client: AsyncClient,):
    resp = await client.get(chapters_path, params={
        "manga_id": 12973
    })
    assert resp.status_code == 406


async def test_get_meta_data_successful(manga_site: MangaSite,
                                        manga_name: str,
                                        manga_url: str, meta_path: str,
                                        client: AsyncClient,
                                        crud_service: CRUDService,
                                        database: DatabaseService):
    async with database.session() as session:
        async with session.begin():
            manga_id = await crud_service.get_id_by_attr(session, Manga, "url", manga_url)
    resp = await client.get(meta_path, params={
        "manga_id": manga_id
    })

    meta_data: Dict[str, Any] = resp.json()
    assert 'last_update' in meta_data
    assert 'finished' in meta_data
    assert 'thum_img' in meta_data

    assert meta_data['last_update'] == '2016-04-23T00:00:00'
    assert meta_data['finished'] == True
    assert f"{manga_site}/{manga_name}/thum_img" in meta_data['thum_img']
