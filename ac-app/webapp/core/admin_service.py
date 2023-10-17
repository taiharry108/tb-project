import asyncio
from dependency_injector.wiring import inject, Provider, Provide
from pathlib import Path
from sqlalchemy import select, Table, MetaData, case
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncConnection
from typing import Coroutine

from container import Container
from core.models.chapter import Chapter
from core.models.manga import MangaWithSite
from core.models.manga_index_type_enum import MangaIndexTypeEnum, m_types
from core.models.meta import Meta
from core.scraping_service.manga_site_scraping_service import MangaSiteScrapingService
from download_service import DownloadService


async def gather_with_concurrency(n: int, *coros: Coroutine):
    semaphore = asyncio.Semaphore(n)

    async def sem_coro(coro):
        async with semaphore:
            return await coro

    return await asyncio.gather(*(sem_coro(c) for c in coros))


async def get_table(table_name: str, conn: AsyncConnection) -> Table:
    metadata_obj = MetaData()
    table = await conn.run_sync(
        lambda sync_conn: Table(table_name, metadata_obj,
                                autoload_with=sync_conn)
    )
    return table


async def get_all_mangas_in_history(db_engine: AsyncEngine) -> list[MangaWithSite]:
    async with db_engine.begin() as conn:
        manga_table = await get_table("mangas", conn)
        history_table = await get_table("history", conn)
        manga_site_table = await get_table("manga_sites", conn)

        joined_table = history_table.outerjoin(
            manga_table, history_table.c.manga_id == manga_table.c.id
        ).outerjoin(
            manga_site_table,
            manga_table.c.manga_site_id == manga_site_table.c.id,
        )
        rows = await conn.execute(
            select(
                joined_table.c.mangas_url,
                joined_table.c.mangas_name.label("manga_name"),
                joined_table.c.manga_sites_name.label("manga_site_name"),
                joined_table.c.mangas_id.label("id"),
            ).select_from(joined_table)
        )
        return [MangaWithSite.model_validate(row) for row in rows]


async def get_meta_for_manga(
    manga_url: str,
    manga_name: str,
    scraping_service: MangaSiteScrapingService,
    download_service: DownloadService,
    download_path: str,
) -> Meta:
    meta = await scraping_service.get_meta(manga_url)

    download_path = Path(download_path) / \
        scraping_service.site.name / manga_name

    download_result = await download_service.download_img(
        url=str(meta.thum_img), download_path=download_path, filename="thum_img"
    )
    meta.thum_img = download_result["pic_path"]
    return meta


async def get_chapters_for_manga(
        manga_url: str,
        scraping_service: MangaSiteScrapingService
):
    return await scraping_service.get_chapters(manga_url)


async def get_meta_for_manga(
    manga_url: str,
    manga_name: str,
    scraping_service: MangaSiteScrapingService,
    download_service: DownloadService,
    download_path: str,
) -> Meta:
    meta = await scraping_service.get_meta(manga_url)

    download_path = Path(download_path) / \
        scraping_service.site.name / manga_name

    download_result = await download_service.download_img(
        url=str(meta.thum_img), download_path=download_path, filename="thum_img"
    )
    meta.thum_img = download_result["pic_path"]
    return meta


@inject
async def update_chapters(
    mangas: list[MangaWithSite],
    ss_factory=Provider[Container.scraping_service_factory],
    db_engine: AsyncEngine = Provide[Container.db_engine],
) -> dict[int, dict[MangaIndexTypeEnum, list[Chapter]]]:
    """"""
    tasks = [get_chapters_for_manga(str(manga.url), ss_factory(
        manga.manga_site_name)) for manga in mangas]

    chap_result: list[dict[MangaIndexTypeEnum, list[Chapter]]] = await gather_with_concurrency(5, *tasks)
    chapter_dict = {
        manga.id: chap
        for manga, chap in zip(mangas, chap_result)
    }
    chapter_list = []
    for manga_id, chapters in chapter_dict.items():
        for m_type, chap_list in chapters.items():
            for chap in chap_list:
                chapter_list.append(
                    {
                        "title": chap.title,
                        "page_url": str(chap.page_url),
                        "manga_id": manga_id,
                        "type": m_types.index(m_type),
                    }
                )

    async with db_engine.begin() as conn:
        chapter_table = await get_table("chapters", conn)
        stmt = insert(chapter_table).values(chapter_list).on_conflict_do_nothing(
            index_elements=["page_url"]).returning(chapter_table.c.page_url)
        await conn.execute(stmt)

    return chapter_dict


@inject
async def update_meta(
    mangas: list[MangaWithSite],
    ss_factory=Provider[Container.scraping_service_factory],
    download_service: DownloadService = Provide[Container.download_service],
    download_path: str = Provide[Container.config.api.download_path],
    db_engine: AsyncEngine = Provide[Container.db_engine],
) -> list[Meta]:
    tasks = [
        get_meta_for_manga(
            str(manga.url),
            manga.manga_name,
            ss_factory(manga.manga_site_name),
            download_service,
            download_path,
        )
        for manga in mangas
    ]

    result: list[Meta] = await gather_with_concurrency(5, *tasks)

    async with db_engine.begin() as conn:
        last_update_map = {
            manga.id: meta.last_update for manga, meta in zip(mangas, result)
        }
        thum_img_map = {manga.id: meta.thum_img for manga,
                        meta in zip(mangas, result)}
        finished_map = {manga.id: meta.finished for manga,
                        meta in zip(mangas, result)}
        manga_table = await get_table("mangas", conn)
        stmt = (
            manga_table.update()
            .values(
                last_update=case(last_update_map, value=manga_table.c.id),
                thum_img=case(thum_img_map, value=manga_table.c.id),
                finished=case(finished_map, value=manga_table.c.id),
            )
            .where(manga_table.c.id.in_([manga.id for manga in mangas]))
        )
        await conn.execute(stmt)

    return result