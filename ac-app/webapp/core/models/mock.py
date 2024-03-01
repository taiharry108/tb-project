from core.models.chapter import Chapter
from core.models.manga import Manga
from core.models.meta import Meta
from datetime import datetime


MOCK_MANGA = Manga(id=1, name="Test Manga", url="https://example.com")
MOCK_META = Meta(
    last_update=datetime.now(),
    finished=True,
    thum_img="https://www.test-thum-img.com",
    latest_chapter=Chapter(
        title="Test Chapter", page_url="https://www.test-chapter.com"
    ),
)

MOCK_CHAPTER = Chapter(title="Test Chapter", page_url="https://www.test-chapter.com")
MOCK_PAGES = ["https://www.test-page-1.com", "https://www.test-page-2.com"]
