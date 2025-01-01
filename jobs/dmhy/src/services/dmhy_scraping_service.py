from bs4 import Tag, BeautifulSoup
from logging import getLogger

from core.dmhy_search_result import DMHYSearchResult
from core.dmhy_team_enum import DMHYTeamEnum
from download_service import DownloadService

logger = getLogger(__name__)


class DMHYScapingService:
    def __init__(self, download_service: DownloadService):
        self.download_service = download_service

    async def search_anime(
        self, keyword: str, team: DMHYTeamEnum | None, idx: int
    ) -> tuple[list[DMHYSearchResult], int]:
        """Search manga with keyword, return a list of manga"""
        if team:
            url = f"https://share.dmhy.org/topics/list?keyword={keyword}&sort_id=0&team_id={team.value}&order=date-desc"
        else:
            url = f"https://share.dmhy.org/topics/list?keyword={keyword}&sort_id=0&order=date-desc"
        soup: BeautifulSoup = await self.download_service.get_soup(url)
        try:
            trs = soup.find("tbody").find_all("tr")
        except AttributeError:
            return [], int

        def parse_tag(tr: Tag) -> DMHYSearchResult:
            d = {}
            if team:
                d["team"] = getattr(
                    DMHYTeamEnum,
                    tr.find("td", class_="title").find("span", class_="tag").text.strip().split("-")[0],
                )
            else:
                d["team"] = None
            d["name"] = tr.find("td", class_="title").find_all("a")[-1].text.strip()
            d["post_datetime"] = (
                tr.find_all("td")[0].find("span").text.strip().replace("/", "-")
            )
            d["url"] = tr.find("a", title="磁力下載").get("href")
            return DMHYSearchResult.model_validate(d)

        return [parse_tag(tr) for tr in trs], idx
