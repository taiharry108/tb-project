import asyncio
import json
import sys

from kink import di
from pydantic import BaseModel
from bootstrap import bootstrap_di

from async_service import AsyncService
from core.dmhy_team_enum import DMHYTeamEnum
from services import DMHYScapingService, DelugeService


bootstrap_di()


class Anime(BaseModel):
    name: str
    team: DMHYTeamEnum | None
    ep: int
    download_path: str


class AnimeList(BaseModel):
    animes: list[Anime]


async def main(
    dmhy_scraping_service: DMHYScapingService = di[DMHYScapingService],
    async_service: AsyncService = di[AsyncService],
    deluge_service: DelugeService = di[DelugeService],
    password: str = di["deluge_service"]["password"],
    data_file: str = di["data_file"],
):
    if not await deluge_service.auth(password):
        print("authentication failed")
        sys.exit(1)

    with open(data_file) as f:
        anime_list = AnimeList.model_validate(json.load(f))

    search_args = [
        {"keyword": f"{anime.name} {anime.ep:02}", "team": anime.team, "idx": idx}
        for idx, anime in enumerate(anime_list.animes)
    ]
    async for result, idx in async_service.work(
        search_args, dmhy_scraping_service.search_anime
    ):
        if not result:
            continue
        result.sort(key=lambda x: x.post_datetime, reverse=True)

        torrent_id = await deluge_service.add_torrent_magnet(
            result[0].url, download_path=anime_list.animes[idx].download_path
        )

        anime_list.animes[idx].ep += 1

    with open(data_file, "w") as f:
        f.write(anime_list.model_dump_json(indent=4))


if __name__ == "__main__":
    asyncio.run(main())
