from datetime import datetime
from httpx import AsyncClient
from logging import getLogger
import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.anime import AnimeSimple
from core.models.manga import MangaSimple
from database.crud_service import CRUDService
from database.database_service import DatabaseService
from database.models import (
    MangaSite,
    Manga,
    Chapter,
    Page,
    History,
    User,
    Anime,
    Episode,
    AHistory,
)

from routers.auth import get_session_data
from session.session_verifier import SessionData


logger = getLogger(__name__)


@pytest.fixture(scope="module")
def history_path():
    return "/user/history"


@pytest.fixture(scope="module")
def a_history_path():
    return "/user/a_history"


@pytest.fixture(scope="module")
async def manga_name():
    return "test_manga"


@pytest.fixture(scope="module")
async def chapter_title():
    return "test_chap"


@pytest.fixture(scope="module")
async def chapter_url():
    return "https://test_chap.com"


@pytest.fixture(scope="module")
async def manga_url():
    return "https://test_manga.com"


@pytest.fixture(scope="module")
async def anime_name():
    return "test_anime"


@pytest.fixture(scope="module")
async def episode_title():
    return "test_episode"


@pytest.fixture(scope="module")
async def episode_key():
    return "key"


@pytest.fixture(scope="module")
async def anime_url():
    return "https://test_anime.com"


@pytest.fixture(scope="module")
async def username():
    return "test_user"


@pytest.fixture(scope="module")
async def password():
    return "123456"


@pytest.fixture(autouse=True, scope="module")
async def run_before_and_after_tests(
    database: DatabaseService,
    username: str,
    password: str,
    manga_name: str,
    manga_url: str,
    anime_name: str,
    anime_url: str,
):
    import main

    async def get_fake_session_data() -> SessionData:
        return SessionData(username=username)

    main.app.dependency_overrides[get_session_data] = get_fake_session_data

    async with database.session() as session:
        async with session.begin():
            await session.execute(delete(AHistory))
            await session.execute(delete(History))
            await session.execute(delete(Episode))
            await session.execute(delete(Anime))
            await session.execute(delete(Page))
            await session.execute(delete(Chapter))
            await session.execute(delete(Manga))
            await session.execute(delete(MangaSite))
            await session.execute(delete(User))
            session.add(Manga(name=manga_name, url=manga_url))
            session.add(
                Anime(
                    name=anime_name,
                    url=anime_url,
                    sub="test_sub",
                    year="test_year",
                    season="test_season",
                    eps="test_eps",
                )
            )
            session.add(User(email=username, hashed_password=password))
            await session.commit()
    yield
    main.app.dependency_overrides = {}


@pytest.fixture(scope="module")
async def manga_id(
    manga_url: str, crud_service: CRUDService, database: DatabaseService
) -> int:
    async with database.session() as session:
        async with session.begin():
            db_manga = await crud_service.get_item_by_attr(
                session, Manga, "url", manga_url
            )
            return db_manga.id


@pytest.fixture(scope="module")
async def anime_id(
    anime_url: str, crud_service: CRUDService, database: DatabaseService
) -> int:
    async with database.session() as session:
        async with session.begin():
            db_anime = await crud_service.get_item_by_attr(
                session, Anime, "url", anime_url
            )
            return db_anime.id


@pytest.fixture(scope="module")
async def user_id(
    username: str, crud_service: CRUDService, database: DatabaseService
) -> int:
    async with database.session() as session:
        async with session.begin():
            db_user = await crud_service.get_item_by_attr(
                session, User, "email", username
            )
            return db_user.id


@pytest.fixture(scope="module")
async def chapter_id(
    chapter_url: str,
    chapter_title: str,
    manga_id: int,
    crud_service: CRUDService,
    database: DatabaseService,
) -> int:
    async with database.session() as session:
        async with session.begin():
            session.add(
                Chapter(
                    title=chapter_title, page_url=chapter_url, manga_id=manga_id, type=0
                )
            )
            await session.commit()
    async with database.session() as session:
        async with session.begin():
            db_chapter = await crud_service.get_item_by_attr(
                session, Chapter, "page_url", chapter_url
            )
            return db_chapter.id


@pytest.fixture(scope="module")
async def episode_id(
    episode_key: str,
    episode_title: str,
    anime_id: int,
    crud_service: CRUDService,
    database: DatabaseService,
) -> int:
    async with database.session() as session:
        async with session.begin():
            session.add(
                Episode(
                    title=episode_title,
                    manual_key=episode_key,
                    data="test_data",
                    last_update=datetime.now(),
                    anime_id=anime_id,
                )
            )
            await session.commit()
    async with database.session() as session:
        async with session.begin():
            db_episode = await crud_service.get_item_by_attr(
                session, Episode, "manual_key", episode_key
            )
            return db_episode.id


async def test_get_empty_ahistory(a_history_path: str, client: AsyncClient):
    resp = await client.get(a_history_path)
    assert resp.json() == []


async def test_get_empty_history(history_path: str, client: AsyncClient):
    resp = await client.get(history_path)
    assert resp.json() == []


async def test_add_history(
    history_path: str,
    client: AsyncClient,
    manga_id: int,
    user_id: int,
    crud_service: CRUDService,
    db_session: AsyncSession,
):
    resp = await client.post(history_path, data={"manga_id": manga_id})
    assert resp.json() == {"user_id": user_id, "manga_id": manga_id}
    history_mangas = await crud_service.get_items_of_obj(
        db_session, User, user_id, "history_mangas"
    )
    assert len(history_mangas) == 1
    assert history_mangas[0].manga_id == manga_id
    assert history_mangas[0].user_id == user_id


async def test_add_a_history(
    a_history_path: str,
    client: AsyncClient,
    anime_id: int,
    user_id: int,
    crud_service: CRUDService,
    db_session: AsyncSession,
):
    resp = await client.post(a_history_path, data={"anime_id": anime_id})
    assert resp.json() == {"user_id": user_id, "anime_id": anime_id}
    history_animes = await crud_service.get_items_of_obj(
        db_session, User, user_id, "history_animes"
    )
    assert len(history_animes) == 1
    assert history_animes[0].anime_id == anime_id
    assert history_animes[0].user_id == user_id


async def test_update_history(
    history_path: str,
    client: AsyncClient,
    manga_id: int,
    user_id: int,
    chapter_id: int,
    crud_service: CRUDService,
    db_session: AsyncSession,
):
    data = {"manga_id": manga_id, "chapter_id": chapter_id}
    resp = await client.put(history_path, data=data)
    assert resp.json() == {
        "user_id": user_id,
        "manga_id": manga_id,
        "chapter_id": chapter_id,
    }
    history_mangas = await crud_service.get_items_of_obj(
        db_session, User, user_id, "history_mangas"
    )
    assert len(history_mangas) == 1
    assert history_mangas[0].manga_id == manga_id
    assert history_mangas[0].user_id == user_id
    assert history_mangas[0].chapter_id == chapter_id


async def test_update_a_history(
    a_history_path: str,
    client: AsyncClient,
    anime_id: int,
    user_id: int,
    episode_id: int,
    crud_service: CRUDService,
    db_session: AsyncSession,
):
    data = {"anime_id": anime_id, "episode_id": episode_id}
    resp = await client.put(a_history_path, data=data)
    assert resp.json() == {
        "user_id": user_id,
        "anime_id": anime_id,
        "episode_id": episode_id,
    }
    history_animes = await crud_service.get_items_of_obj(
        db_session, User, user_id, "history_animes"
    )
    assert len(history_animes) == 1
    assert history_animes[0].anime_id == anime_id
    assert history_animes[0].user_id == user_id
    assert history_animes[0].episode_id == episode_id


async def test_update_a_history_fail(
    a_history_path: str,
    client: AsyncClient,
    anime_id: int,
    episode_id: int,
):
    data = {"anime_id": anime_id, "episode_id": episode_id + 1}
    resp = await client.put(a_history_path, data=data)
    assert resp.status_code == 406


async def test_get_a_history(
    a_history_path: str,
    client: AsyncClient,
    anime_name: str,
    anime_url: str,
    episode_title: str,
):
    resp = await client.get(a_history_path)
    anime = AnimeSimple(**resp.json()[0])
    assert anime.name == anime_name
    assert anime.url == anime_url
    assert anime.last_read_episode.title == episode_title


async def test_get_history(
    history_path: str,
    client: AsyncClient,
    manga_name: str,
    manga_url: str,
    chapter_title: str,
    chapter_url: str,
):
    resp = await client.get(history_path)
    manga = MangaSimple(**resp.json()[0])
    assert manga.name == manga_name
    assert manga.url == manga_url
    assert manga.last_read_chapter.title == chapter_title
    assert manga.last_read_chapter.page_url == chapter_url


async def test_add_history_fail(
    history_path: str,
    client: AsyncClient,
    manga_id: int,
):
    resp = await client.post(history_path, data={"manga_id": manga_id + 1})
    assert resp.status_code == 406


async def test_del_a_history(
    a_history_path: str,
    client: AsyncClient,
    anime_id: int,
    user_id: int,
    crud_service: CRUDService,
    db_session: AsyncSession,
):
    history_animes = await crud_service.get_items_of_obj(
        db_session, User, user_id, "history_animes"
    )
    assert len(history_animes) == 1
    assert history_animes[0].anime_id == anime_id
    assert history_animes[0].user_id == user_id
    resp = await client.delete(a_history_path, params={"anime_id": anime_id})
    assert resp.json() == {"success": True}

    history_animes = await crud_service.get_items_of_obj(
        db_session, User, user_id, "history_animes"
    )
    assert len(history_animes) == 0


async def test_del_history(
    history_path: str,
    client: AsyncClient,
    manga_id: int,
    user_id: int,
    crud_service: CRUDService,
    db_session: AsyncSession,
):
    history_mangas = await crud_service.get_items_of_obj(
        db_session, User, user_id, "history_mangas"
    )
    assert len(history_mangas) == 1
    assert history_mangas[0].manga_id == manga_id
    assert history_mangas[0].user_id == user_id
    resp = await client.delete(history_path, params={"manga_id": manga_id})
    assert resp.json() == {"success": True}

    history_mangas = await crud_service.get_items_of_obj(
        db_session, User, user_id, "history_mangas"
    )
    assert len(history_mangas) == 0
