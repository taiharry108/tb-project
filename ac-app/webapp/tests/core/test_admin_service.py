# from dependency_injector.wiring import inject, Provide
from kink import di
import pytest

from sqlalchemy import (
    delete,
    insert,
    MetaData,
    Table,
    select,
    func,
)
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncConnection

from core.admin_service import update_meta, update_chapters, get_all_mangas_in_history
from core.models.manga_index_type_enum import MangaIndexTypeEnum
from core.models.manga import MangaWithSite
from core.scraping_service import ScrapingServiceFactory
from database.database_service import DatabaseService
from database.models import (
    MangaSite,
    Manga,
    Chapter,
    Page,
    History,
    User,
    Episode,
)
from download_service import DownloadService


@pytest.fixture(scope="module")
async def manga_names() -> list[str]:
    # return ["naruto", "我的英雄"]
    return ["我的英雄"]


@pytest.fixture(scope="module")
async def manga_urls() -> list[str]:
    return [
        # "https://www.manhuaren.com/manhua-huoyingrenzhe-naruto/",
        "https://www.manhuaren.com/manhua-wodeyingxiong/",
    ]


@pytest.fixture(scope="module")
async def usernames():
    return [f"test_user{idx}" for idx in range(5)]


@pytest.fixture(scope="module")
async def password():
    return "123456"


@pytest.fixture(autouse=True, scope="module")
def download_path(
    download_path=di["api"]["download_path"],
) -> str:
    return f"{download_path}/test"


@pytest.fixture(autouse=True, scope="module")
async def run_before_and_after_tests(
    database: DatabaseService,
    usernames: list[str],
    password: str,
    manga_names: list[str],
    manga_urls: list[str],
    db_engine: AsyncEngine,
):
    # import main

    async with database.session() as session:
        async with session.begin():
            await session.execute(delete(History))
            await session.execute(delete(Episode))
            await session.execute(delete(Page))
            await session.execute(delete(Chapter))
            await session.execute(delete(Manga))
            await session.execute(delete(MangaSite))
            await session.execute(delete(User))
            session.add(
                MangaSite(name="manhuaren", url="https://www.manhuaren.com/", id=1)
            )
            for idx, (manga_name, manga_url) in enumerate(zip(manga_names, manga_urls)):
                session.add(
                    Manga(
                        name=manga_name,
                        url=manga_url,
                        id=idx + 1,
                        manga_site_id=1,
                        finished=False,
                    )
                )

            for idx, username in enumerate(usernames):
                session.add(User(email=username, hashed_password=password, id=idx + 1))
            await session.commit()

    async with db_engine.begin() as conn:
        await conn.execute(
            insert(await get_table("history", conn)).values(
                [
                    {"manga_id": 1, "user_id": 1},
                    {"manga_id": 1, "user_id": 2},
                    {"manga_id": 1, "user_id": 3},
                    # {"manga_id": 2, "user_id": 2},
                ]
            )
        )

    yield


async def get_table(table_name: str, conn: AsyncConnection) -> Table:
    metadata_obj = MetaData()
    table = await conn.run_sync(
        lambda sync_conn: Table(table_name, metadata_obj, autoload_with=sync_conn)
    )
    return table


async def test_get_all_mangas_in_history(db_engine: AsyncEngine, manga_urls: list[str]):
    async with db_engine.begin() as conn:
        all_mangas = await get_all_mangas_in_history(db_engine)
        print(all_mangas)
        assert len(all_mangas) == 1
        assert str(all_mangas[0].url) == manga_urls[0]


async def test_update_chapters(
    db_engine: AsyncEngine,
    manga_names: list[str],
    manga_urls: list[str],
    scraping_service_factory: ScrapingServiceFactory,
):
    mangas = [
        MangaWithSite(
            url=manga_url,
            manga_site_name="manhuaren",
            manga_name=manga_name,
            id=idx + 1,
        )
        for idx, (manga_name, manga_url) in enumerate(zip(manga_names, manga_urls))
    ]
    chapters = await update_chapters(mangas, scraping_service_factory, db_engine)
    assert len(chapters[1][MangaIndexTypeEnum.CHAPTER]) == 8

    async with db_engine.begin() as conn:
        chapter_table = await get_table("chapters", conn)
        stmt = (
            select(func.count())
            .select_from(chapter_table)
            .where(chapter_table.c.manga_id == 1)
        )

        assert (await conn.execute(stmt)).scalar() == 8


async def test_update_meta(
    download_path: str,
    db_engine: AsyncEngine,
    manga_names: list[str],
    manga_urls: list[str],
    scraping_service_factory: ScrapingServiceFactory,
    download_service: DownloadService,
):
    mangas = [
        MangaWithSite(
            url=manga_url,
            manga_site_name="manhuaren",
            manga_name=manga_name,
            id=idx + 1,
        )
        for idx, (manga_name, manga_url) in enumerate(zip(manga_names, manga_urls))
    ]
    metas = await update_meta(
        mangas,
        ss_factory=scraping_service_factory,
        download_service=download_service,
        download_path=download_path,
        db_engine=db_engine,
    )
    for meta, manga in zip(metas, mangas):
        assert (
            f"downloaded/test/{manga.manga_site_name}/{manga.manga_name}/thum_img"
            in meta.thum_img
        )
    async with db_engine.begin() as conn:
        manga_table = await get_table("mangas", conn)
        stmt = select(
            manga_table.c.name,
            manga_table.c.finished,
            manga_table.c.thum_img,
            manga_table.c.last_update,
        ).where(manga_table.c.name.in_([manga.manga_name for manga in mangas]))
        result = await conn.execute(stmt)
        for meta, row in zip(metas, result):
            db_meta = row._asdict()
            assert meta.finished == db_meta["finished"]
            assert meta.thum_img == db_meta["thum_img"]
            assert meta.last_update == db_meta["last_update"]
