import pytest

from logging import getLogger

from core.dmhy_team_enum import DMHYTeamEnum
from download_service import DownloadService
from services import DMHYScapingService


logger = getLogger(__name__)


@pytest.fixture
def scraping_service(
    download_service: DownloadService,
) -> DMHYScapingService:
    return DMHYScapingService(download_service)


@pytest.fixture
def search_text() -> str:
    return "spy"


@pytest.fixture
def team() -> DMHYTeamEnum:
    return DMHYTeamEnum.ANi


async def test_search_anime(
    scraping_service: DMHYScapingService,
    search_text: str,
    team: DMHYTeamEnum,
):
    dmhy_results = await scraping_service.search_anime(search_text, team)

    assert len(dmhy_results) > 50
    for result in dmhy_results:
        assert result.team == team
        assert "[MP4]" in result.name
