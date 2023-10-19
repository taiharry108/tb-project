import json


from asyncio import run
from kink import di, inject
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
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
    "manga_site_id",
]


class History(TypedDict):
    email: str
    manga_name: str
    manga_url: str
    chapter_title: str
    chapter_url: str
    chpater_type: int
    manga_site_id: int


async def get_all_mangas_from_history(db_engine: AsyncEngine):
    query = """
        SELECT u.email,
            m.name as manga_name,
            m.url as manga_url,
            c.title as chapter_title,
            page_url as chapter_url,
            c.type as chapter_type,
            m.manga_site_id
        FROM history h
        LEFT JOIN mangas m ON h.manga_id = m.id
        LEFT JOIN users u ON h.user_id = u.id
        LEFT JOIN chapters c on h.chapter_id = c.id;
    """
    async with db_engine.begin() as conn:
        return await conn.execute(text(query))


async def main():
    result = await get_all_mangas_from_history(di[AsyncEngine])
    history_collection: list[History] = [
        {KEYS[idx]: item for idx, item in enumerate(row)} for row in result
    ]
    print(json.dumps(history_collection))


if __name__ == "__main__":
    run(main())
