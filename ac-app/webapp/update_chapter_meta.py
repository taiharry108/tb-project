from asyncio import run
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from container import Container
from core.models.manga_site_enum import MangaSiteEnum
from database.models import Manga
from routers.api import get_chapters, get_meta
from routers.db_utils import get_scraping_service_from_site
from routers.utils import get_db_session


async def get_all_mangas_from_history(container: Container):
    query = """
    SELECT m.url, m.id, m.manga_site_id, m.name as manga_name, 
            ms.name as site_name FROM mangas as m
        RIGHT JOIN (
            SELECT DISTINCT manga_id  FROM history
        )  as h ON m.id = h.manga_id
        JOIN manga_sites as ms ON m.manga_site_id = ms.id
            
        
    """
    async with container.db_engine().begin() as conn:
        return await conn.execute(text(query))


async def main():
    container = Container()

    result = await get_all_mangas_from_history(container)
    for row in result:
        print(row)
        db_manga = Manga(id=row.id, url=row.url, name=row.manga_name)
        scraping_service = get_scraping_service_from_site(MangaSiteEnum(row.site_name))

        async for session in get_db_session(container.db_service()):
            await get_chapters(
                session=session, db_manga=db_manga, scraping_service=scraping_service
            )

        async for session in get_db_session(container.db_service()):
            meta = await get_meta(
                db_manga=db_manga, scraping_service=scraping_service, db_session=session
            )


if __name__ == "__main__":
    run(main())
