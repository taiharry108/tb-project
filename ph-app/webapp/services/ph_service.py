from bs4 import BeautifulSoup
from dateutil.parser import parse
from dependency_injector.wiring import Provide
from fastapi import Depends
import json
from m3u8downloader.main import M3u8Downloader
from pathlib import Path
import re

from container import Container
from async_service.async_service import AsyncService
from download_service.download_service import DownloadService
from models.search_result import SearchResult
from models.video import Video
from models.vid_result import VidResult


def _get_videos_from_pc_vid_list(search_result_list: BeautifulSoup) -> list[Video]:
    def parse_search_result(result):
        a_tag = result.find("a", class_="linkVideoThumb")
        return Video(
            title=a_tag["title"],
            vid_id=result["data-video-vkey"],
            thumbnail=a_tag.find("img")["src"],
            duration=a_tag.find(
                "div", class_="marker-overlays").find("var", class_="duration").text.strip(),
            username=result.find(
                "div", class_="usernameWrap").text.strip(),
            upload_date=result.find("div", class_="videoDetailsBlock").find(
                "var", class_="added").text.strip()
        )
    return [parse_search_result(result) for result in search_result_list]


def download_video(filepath: Path, vid_url: str) -> None:
    tempdir = "/tmp"
    if filepath.exists():
        return
    downloader = M3u8Downloader(vid_url, filepath,
                                tempdir=tempdir,
                                poolsize=10)
    downloader.start()


async def search_ph(keyword: str,
                    page: int,
                    search_url: str = Depends(
                        Provide[Container.config.ph_service.search_url]),
                    download_service: DownloadService = Depends(
                        Provide[Container.download_service]),
                    async_service: AsyncService = Depends(
                        Provide[Container.async_service]),
                    download_path: str = Depends(
                        Provide[Container.config.api.download_path])
                    ) -> SearchResult:
    url = search_url.format(
        keyword.replace(" ", "+"), page)

    soup: BeautifulSoup = await download_service.get_soup(url)
    next_page = soup.find("li", class_="page_next").find('a')[
        'href'].split('=')[-1]

    search_result_list = soup.find("ul", id="videoSearchResult")
    search_result_list = search_result_list.find_all(
        "li", class_="pcVideoListItem")

    videos = _get_videos_from_pc_vid_list(search_result_list)

    async for result in download_thumbnails(videos, download_service, async_service, download_path + "/thumbnail"):
        videos[result['idx']].thumbnail_path = result['pic_path']

    search_result = SearchResult(vids=videos, next_page=next_page)
    return search_result


def download_thumbnails(videos: list[Video],
                        download_service: DownloadService,
                        async_service: AsyncService,
                        download_path: str
                        ):
    img_list = [{
        "url": video.thumbnail,
        "filename": video.vid_id,
        "idx": idx,
        "total": len(videos)
    } for idx, video in enumerate(videos)]
    return download_service.download_imgs(async_service=async_service,
                                          download_path=Path(
                                              download_path),
                                          img_list=img_list, headers={})


async def get_vid_result(vid_id: str,
                         vid_url: str = Depends(
                             Provide[Container.config.ph_service.vid_url]),
                         download_service: DownloadService = Depends(
                             Provide[Container.download_service]),
                         download_path: str = Depends(
                             Provide[Container.config.api.download_path]),
                         async_service: AsyncService = Depends(
                             Provide[Container.async_service]),) -> VidResult:
    def get_vid_meta(soup: BeautifulSoup) -> Video:
        meta_dict = json.loads(soup.find("script", type='application/ld+json').text)

        return Video(
            title=meta_dict['name'],
            upload_date=parse(meta_dict['uploadDate']).strftime("%Y-%m-%d"),
            thumbnail="",
            duration="",
            username=meta_dict['author']
        )

    def get_vid_url(soup: BeautifulSoup) -> str:        
        for script in soup.find_all('script'):
            script_text = script.text.strip()
            if script_text.startswith("var flashvars_"):
                break
        else:
            return ""
        pattern = re.compile("var flashvars_\d+ \= (\{.*\});")
        if not (match := pattern.search(script_text)):
            return ""
        json_obj = json.loads(match.group(1))
        media_def = json_obj['mediaDefinitions']
        media_def = list(
            filter(lambda x: isinstance(x['quality'], str), media_def))
        media_def.sort(key=lambda x: int(x['quality']), reverse=True)

        if not media_def:
            return ""

        return media_def[0]['videoUrl']

    def get_recommendation(soup: BeautifulSoup) -> list[Video]:
        recommended_vids_ul = soup.find("ul", id="recommendedVideos")
        search_result_list = recommended_vids_ul.find_all(
            "li", class_="pcVideoListItem")
        return _get_videos_from_pc_vid_list(search_result_list)
    url = vid_url.format(vid_id)
    soup: BeautifulSoup = await download_service.get_soup(url)
    vid_url = get_vid_url(soup)

    if not vid_url:
        return ""

    filepath = Path(download_path) / "vid" / f"{vid_id}.mp4"
    download_video(filepath, vid_url)

    videos = get_recommendation(soup)
    async for result in download_thumbnails(videos, download_service, async_service, download_path + "/thumbnail"):
        videos[result['idx']].thumbnail_path = result['pic_path']
    return VidResult(filepath=filepath, vids=videos, vid=get_vid_meta(soup))
