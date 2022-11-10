import binascii
from bs4 import BeautifulSoup
from collections import defaultdict
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from datetime import datetime
import json
from logging import getLogger
import re
from typing import List, Dict

from core.models.chapter import Chapter
from core.models.manga import Manga
from core.models.manga_index_type_enum import MangaIndexTypeEnum
from core.models.meta import Meta
from core.models.site import Site
from core.scraping_service.manga_site_scraping_service import MangaSiteScrapingService

from download_service.download_service import DownloadService


logger = getLogger(__name__)


def decrypt(encrypted, passphrase, iv) -> str:
    encrypted = binascii.unhexlify(encrypted)
    encrypted = pad(encrypted, block_size=AES.block_size)
    aes = AES.new(passphrase.encode('utf-8'),
                  AES.MODE_CBC, iv.encode('utf-8'))

    decrypted = aes.decrypt(encrypted)

    end_idx = decrypted.rfind(b'}')
    end_idx = max(end_idx, decrypted.rfind(b']'))
    decrypted = decrypted[:end_idx + 1]
    try:
        decrypted = decrypted.decode('utf-8').strip()
    except:
        pass

    return decrypted


class CopyMangaScrapingService(MangaSiteScrapingService):
    def __init__(self, download_service: DownloadService):
        self.site: Site = Site(
            id=1, name="copymanga", url="https://copymanga.net/")
        self.download_service = download_service
        self._index_page_cache = {}

    async def search_manga(self, keyword: str) -> List[Manga]:
        """Search manga with keyword, return a list of manga"""

        def construct_url(path_word: str):
            return f'{self.url}comic/{path_word}'

        search_url = f'{self.url}api/kb/web/searchs/comics?offset=0&platform=2&limit=12&q={keyword}&q_type='

        result = await self.download_service.get_json(search_url)
        result = result['results']['list']
        result = [Manga(url=construct_url(item['path_word']),
                        name=item['name']) for item in result]
        return result

    @property
    def url(self):
        return self.site.url

    async def extract_meta_from_soup(self, soup: BeautifulSoup, manga_url: str) -> Dict[str, any]:
        manga_name = manga_url.split('/')[-1]
        json_data = await self.get_json_data_from_soup(soup, manga_name)

        last_chap_dict = json_data['groups']['default']['last_chapter']

        chapter_title = last_chap_dict['name']
        comic_path_word = last_chap_dict['comic_path_word']
        chapter_uuid = last_chap_dict['uuid']

        chapter_url = f"{self.url}comic/{comic_path_word}/chapter/{chapter_uuid}"

        span = soup.find('span', class_='comicParticulars-sigezi')
        last_update = span.findNext('span').text.strip()
        span = span.parent.findNext('li').select('span:nth-of-type(2)')
        finished = span[0].text == '已完結'
        thum_img = soup.find('img', class_='lazyload').get('data-src')

        return Meta(
            last_update=datetime.strptime(last_update, "%Y-%m-%d"),
            finished=finished,
            thum_img=thum_img,
            latest_chapter=Chapter(title=chapter_title, page_url=chapter_url)
        )

    def get_passphrase(self, var_name: str, soup: BeautifulSoup):
        pattern = re.compile(f"var {var_name}'(.*)';")
        for script_tag in soup.find_all('script'):
            match = pattern.search(script_tag.text)
            if match:
                return match.group(1)

    async def get_json_data_from_soup(self, soup: BeautifulSoup, manga_name: str):        
        url = f'{self.url}comicdetail/{manga_name}/chapters'

        passphrase = self.get_passphrase('dio = ', soup)

        data = await self.download_service.get_json(url)
        if data['code'] != 200:
            return {}
        encrypted = data['results']
        decrypted = decrypt(encrypted[16:], passphrase, encrypted[:16])
        json_data = json.loads(decrypted)
        return json_data

    async def get_chapters(self, manga_url: str) -> Dict[MangaIndexTypeEnum, List[Chapter]]:
        """Get index page of manga, return a manga with chapters"""
        def get_type(idx_type):
            if idx_type == '話':
                type_ = MangaIndexTypeEnum.CHAPTER
            elif idx_type == '卷':
                type_ = MangaIndexTypeEnum.VOLUME
            else:
                type_ = MangaIndexTypeEnum.MISC
            return type_

        manga_name = manga_url.split('/')[-1]

        soup = await self._get_index_page(manga_url)
        json_data = await self.get_json_data_from_soup(soup, manga_name)
        if not json_data:
            return {}

        type_dict = {t_dict['id']: t_dict['name']
                     for t_dict in json_data['build']['type']}

        chapters = defaultdict(list)

        for chapter in json_data['groups']['default']['chapters']:
            m_type = get_type(type_dict[chapter['type']])
            title = chapter['name']
            url = f"{self.url}comic/{manga_name}/chapter/{chapter['id']}"
            chapters[m_type].append(Chapter(title=title, page_url=url))

        return chapters

    async def get_page_urls(self, chapter_url: str) -> List[str]:
        """Get all the urls of a chaper, return a list of strings"""
        soup = await self.download_service.get_soup(chapter_url)
        passphrase = self.get_passphrase('jojo = ', soup)
        encrypted = soup.find('div', class_="imageData").get('contentkey')
        json_data = json.loads(
            decrypt(encrypted[16:], passphrase, encrypted[:16]))
        return [item['url'] for item in json_data]
