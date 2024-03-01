import re
import string

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from collections import defaultdict
from logging import getLogger
from typing import List, Dict

from core.models.chapter import Chapter
from core.models.manga import Manga
from core.models.manga_index_type_enum import MangaIndexTypeEnum
from core.models.meta import Meta
from core.models.site import Site
from core.scraping_service.manga_site_scraping_service import MangaSiteScrapingService
from core.scraping_service.utils import convert_url

from download_service import DownloadService

logger = getLogger(__name__)


digs = string.digits + string.ascii_letters


def int2base(x, base):
    if x < 0:
        sign = -1
    elif x == 0:
        return digs[0]
    else:
        sign = 1

    x *= sign
    digits = []

    while x:
        digits.append(digs[int(x % base)])
        x = int(x / base)

    if sign < 0:
        digits.append("-")

    digits.reverse()

    return "".join(digits)


def decode(p, a: int, c: int, k, d):
    def e(c: int) -> str:
        first = "" if c < a else e(int(c / a))
        c = c % a
        if c > 35:
            second = chr(c + 29)
        else:
            second = int2base(c, 36)
        return first + second

    while c != 0:
        c -= 1
        d[e(c)] = k[c] if k[c] != "" else e(c)
    k = [lambda x: d[x]]

    def e2():
        return "\\w+"

    c = 1
    while c != 0:
        c -= 1
        p = re.sub(f"\\b{e2()}\\b", lambda x: k[c](x.group()), p)
    return p


class MangaBatScrapingService(MangaSiteScrapingService):
    def __init__(self, download_service: DownloadService):
        self.site: Site = Site(id=3, name="mangabat", url="https://readmangabat.com/")
        self.download_service = download_service
        self._index_page_cache = {}

    async def search_manga(self, keyword: str) -> List[Manga]:
        """Search manga with keyword, return a list of manga"""

        def handle_div(div) -> Manga:
            url = div.find("a", class_="item-img").get("href")

            return Manga(name=div.find("a", class_="item-title").text, url=url)

        search_url = f"https://h.mangabat.com/search/manga/{keyword}"
        soup = await self.download_service.get_soup(search_url)
        list_div = soup.find("div", class_="panel-list-story")
        item_divs = list_div.find_all("div", class_="list-story-item")
        result = [handle_div(d) for d in item_divs]
        return result

    @property
    def url(self):
        return str(self.site.url)

    def _parse_datetime(self, dt_str) -> datetime:
        return datetime.strptime(dt_str, "%b %d,%Y - %H:%M %p")

    async def extract_meta_from_soup(self, soup: BeautifulSoup, manga_url: str) -> Meta:
        div = soup.find("div", class_="story-info-right")
        table_info_div = div.find("table", class_="variations-tableInfo")
        for tr in table_info_div.find_all("tr"):
            if "Status" in tr.find("td", class_="table-label").text:
                finished = tr.find("td", class_="table-value").text == "Completed"

        for right_extent_div in div.find(
            "div", class_="story-info-right-extent"
        ).find_all("p"):
            if "Updated" in right_extent_div.find("span", class_="stre-label").text:
                last_update = right_extent_div.find("span", class_="stre-value").text
            if "Latest Chap" in right_extent_div.text:
                chap_a_tag = right_extent_div.find("a")
                chapter_title = chap_a_tag.text
                chapter_url = chap_a_tag.get("href")

        thum_img = (
            soup.find("div", class_="story-info-left")
            .find("span", class_="info-image")
            .find("img")
            .get("src")
        )

        try:
            last_update = self._parse_datetime(last_update)
        except Exception as ex:
            logger.error(f"{ex=}, {manga_url=}")
            last_update = None

        return Meta(
            last_update=last_update,
            finished=finished,
            thum_img=thum_img,
            latest_chapter=Chapter(title=chapter_title, page_url=chapter_url),
        )

    async def get_chapters(
        self, manga_url: str
    ) -> Dict[MangaIndexTypeEnum, List[Chapter]]:
        """Get index page of manga, return a manga with chapters"""

        soup = await self._get_index_page(manga_url)

        div = soup.find("div", class_="panel-story-chapter-list")
        chapters = defaultdict(list)

        for li_tag in div.find("ul", class_="row-content-chapter").find_all("li"):
            a_tag = li_tag.find("a")
            title = a_tag.text
            url = a_tag.get("href")
            chapter = Chapter(title=title, page_url=url)
            chapters[MangaIndexTypeEnum.CHAPTER].append(chapter)
        return chapters

    async def get_page_urls(self, chapter_url: str) -> List[str]:
        """Get all the urls of a chaper, return a list of strings"""
        soup = await self.download_service.get_soup(chapter_url)

        return [
            img_tag.get("src") for img_tag in soup.find_all("img", class_="img-content")
        ]
