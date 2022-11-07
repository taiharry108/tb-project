import hashlib

from core.models.chapter import Chapter
from core.models.manga import Manga
from core.models.site import Site

def create_img_name(site: Site, manga: Manga, chapter: Chapter = None, idx: int = None) -> str:
    name = site.name + manga.name
    if chapter:
        name += chapter.title
    if idx is not None:
        name += str(idx)

    hash_object = hashlib.md5(name.encode())
    return hash_object.hexdigest()


def convert_url(url: str, domain: str):
    if url.startswith("//"):
        result = "https:" + url
    elif not url.startswith("http"):
        result = domain + url.lstrip("/")
    else:
        result = url
    return result
