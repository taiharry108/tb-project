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


class ManhuarenScrapingService(MangaSiteScrapingService):
    def __init__(self, download_service: DownloadService):
        self.site: Site = Site(id=0, name="manhuaren", url="https://www.manhuaren.com/")
        self.download_service = download_service
        self._index_page_cache = {}

    async def search_manga(self, keyword: str) -> List[Manga]:
        """Search manga with keyword, return a list of manga"""

        def handle_div(div) -> Manga:
            name = div.find("p", class_="book-list-info-title").text
            url = div.find("a").get("href")
            url = convert_url(url, self.url)

            return Manga(name=name, url=url)

        search_url = f"{self.site.url}search?title={keyword}&language=1"
        soup = await self.download_service.get_soup(search_url)
        result = [
            handle_div(d)
            for d in soup.find("ul", class_="book-list").find_all(
                "div", class_="book-list-info"
            )
        ]
        return result

    @property
    def url(self):
        return str(self.site.url)

    def _parse_datetime(self, dt_str) -> datetime:
        if "月" in dt_str:
            dt = datetime.strptime(f"{datetime.now().year}年{dt_str}", "%Y年%m月%d号")
        elif "前天" in dt_str:
            dt = datetime.now() - timedelta(days=2)
        elif "昨天" in dt_str:
            dt = datetime.now() - timedelta(days=1)
        elif "今天" in dt_str:
            dt = datetime.now()
        else:
            dt = datetime.strptime(dt_str, "%Y-%m-%d")
        dt = datetime(dt.year, dt.month, dt.day)
        return dt

    async def extract_meta_from_soup(self, soup: BeautifulSoup, manga_url: str) -> Meta:
        div = soup.find("div", {"id": "tempc"}).find("div", class_="detail-list-title")
        last_update = div.find("span", class_="detail-list-title-3").text.strip()
        finished = div.find("span", class_="detail-list-title-1").text == "已完结"
        thum_img = soup.find("img", class_="detail-main-bg").get("src")

        latest_chap_tag = div.find("a", class_="detail-list-title-2")
        chapter_title = latest_chap_tag.text.strip()
        chapter_url = convert_url(latest_chap_tag.get("href"), self.url)

        last_update = self._parse_datetime(last_update)

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

        def get_type(idx_type):
            if idx_type == "连载":
                type_ = MangaIndexTypeEnum.CHAPTER
            elif idx_type == "单行本":
                type_ = MangaIndexTypeEnum.VOLUME
            else:
                type_ = MangaIndexTypeEnum.MISC
            return type_

        soup = await self._get_index_page(manga_url)

        div = soup.find("div", class_="detail-selector")

        id_dict = {}

        chapters = defaultdict(list)

        for a in div.find_all("a", "detail-selector-item"):
            onclick = a.get("onclick")
            if "titleSelect" in onclick:
                id_dict[a.text] = onclick.split("'")[3]
        for idx_type, id_v in id_dict.items():
            ul = soup.find("ul", {"id": id_v})
            m_type = get_type(idx_type)
            for a in reversed(ul.find_all("a")):
                url = a.get("href")
                url = convert_url(url, self.url)
                title = a.text
                chapters[m_type].append(Chapter(title=title, page_url=url))
        return chapters

    async def get_page_urls(self, chapter_url: str) -> List[str]:
        """Get all the urls of a chaper, return a list of strings"""
        soup = await self.download_service.get_soup(chapter_url)

        match = None
        for script in soup.find_all("script"):
            if len(script.contents) == 0:
                continue
            if script.contents[0].startswith("eval"):
                match = re.search(r"return p;}(.*\))\)", script.contents[0])
                break
        if match:
            tuple_str = match.group(1)
            p, a, c, k, e, d = eval(tuple_str)
            p = decode(p, a, c, k, d)

            match2 = re.search(r"var newImgs=(.*);", p)
            if match2:
                pages = eval(match2.group(1))
                return pages
        return []
