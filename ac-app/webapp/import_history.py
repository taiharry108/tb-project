from asyncio import run
from datetime import datetime
from kink import di
from sqlalchemy import MetaData, Table, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncConnection
from sqlalchemy.dialects.postgresql import insert
from typing import TypedDict

from boostrap import bootstrap_di

bootstrap_di()

KEYS = [
    "email",
    "manga_name",
    "manga_url",
    "chapter_title",
    "chapter_url",
    "chapter_type",
]


class History(TypedDict):
    email: str
    manga_name: str
    manga_url: str
    chapter_title: str
    chapter_url: str
    chpater_type: int
    manga_site_id: int


class HistoryImport(TypedDict):
    manga_id: int
    chapter_id: int
    user_id: int
    last_added: datetime


class Manga(TypedDict):
    name: str
    url: str
    manga_site_id: int


class Chapter(TypedDict):
    title: str
    page_url: str
    type: int
    manga_id: int


async def get_table(table_name: str, conn: AsyncConnection) -> Table:
    metadata_obj = MetaData()
    table = await conn.run_sync(
        lambda sync_conn: Table(table_name, metadata_obj, autoload_with=sync_conn)
    )
    return table


async def _select_rows(
    engine: AsyncEngine, items: list[any], table_name: str, unique_key: str
):
    async with engine.begin() as conn:
        table = await get_table(table_name, conn)
        unique_vals = [item[unique_key] for item in items]
        stmt = select(table.c.id, getattr(table.c, unique_key)).where(
            getattr(table.c, unique_key).in_(unique_vals)
        )
        return await conn.execute(stmt)


async def select_mangas(db_engine: AsyncEngine, mangas: list[Manga]):
    return await _select_rows(db_engine, mangas, "mangas", "url")


async def select_chapters(db_engine: AsyncEngine, chapters: list[Chapter]):
    return await _select_rows(db_engine, chapters, "chapters", "page_url")


async def insert_mangas(db_engine: AsyncEngine, mangas: list[Manga]) -> set[int]:
    return await _insert_rows(db_engine, mangas, "mangas", "url")


async def insert_chapters(db_engine: AsyncEngine, chapters: list[Chapter]) -> set[int]:
    return await _insert_rows(db_engine, chapters, "chapters", "page_url")


async def _insert_rows(
    db_engine: AsyncEngine, items: list[any], table_name: str, unique_key: str
) -> dict[str, int]:
    if not items:
        return set()

    async with db_engine.begin() as conn:
        table = await get_table(table_name, conn)
        stmt = (
            insert(table)
            .values(items)
            .on_conflict_do_nothing(index_elements=[unique_key])
            .returning(table.c.id, getattr(table.c, unique_key))
        )
        return {row[1]: row[0] for row in await conn.execute(stmt)}


async def work_mangas(
    db_engine: AsyncEngine, history_collection: list[History]
) -> dict[str, int]:
    mangas = [
        {
            "name": history["manga_name"],
            "url": history["manga_url"],
            "manga_site_id": history["manga_site_id"],
        }
        for history in history_collection
    ]
    existing_mangas = await select_mangas(db_engine, mangas)
    manga_dict = {manga_url: manga_id for manga_id, manga_url in existing_mangas}
    mangas_to_insert = [manga for manga in mangas if not manga["url"] in manga_dict]
    new_manga_dict = await insert_mangas(db_engine, mangas_to_insert)
    manga_dict.update(new_manga_dict)
    return manga_dict


async def work_chapters(
    db_engine: AsyncEngine,
    history_collection: list[History],
    manga_dict: dict[str, int],
):
    chapters: list[Chapter] = [
        {
            "title": history["chapter_title"],
            "page_url": history["chapter_url"],
            "type": history["chapter_type"],
            "manga_id": manga_dict.get(history["manga_url"]),
        }
        for history in history_collection
    ]

    existing_chapters = await select_chapters(db_engine, chapters)
    chap_dict = {chap_url: chap_id for chap_id, chap_url in existing_chapters}
    chaps_to_insert = [chap for chap in chapters if not chap["page_url"] in chap_dict]
    new_chap_dict = await insert_chapters(db_engine, chaps_to_insert)
    chap_dict.update(new_chap_dict)
    return chap_dict


async def insert_history(db_engine: AsyncEngine, hist_import_list: list[HistoryImport]):
    async with db_engine.begin() as conn:
        history_table = await get_table("history", conn)
        stmt = insert(history_table).values(hist_import_list)
        stmt = stmt.on_conflict_do_update(
            index_elements=("user_id", "manga_id"),
            set_=dict(chapter_id=stmt.excluded.chapter_id, last_added=datetime.now()),
        )
        await conn.execute(stmt)


async def main():
    history_collection: list[History] = []
    manga_dict = await work_mangas(di[AsyncEngine], history_collection)
    chap_dict = await work_chapters(di[AsyncEngine], history_collection, manga_dict)

    hist_import_list: list[HistoryImport] = [
        {
            "chapter_id": chap_dict[hist["chapter_url"]],
            "manga_id": manga_dict[hist["manga_url"]],
            "user_id": 1,
            "last_added": datetime.now(),
        }
        for hist in history_collection
    ]
    await insert_history(di[AsyncEngine], hist_import_list)


if __name__ == "__main__":
    run(main())
