"""블라인드 재테크 게시판 스크래퍼"""
import json
from datetime import datetime
from scrapers.base import BaseScraper


class BlindScraper(BaseScraper):
    """블라인드 재테크 게시판 스크래퍼

    블라인드는 SPA 구조라 API 엔드포인트를 직접 호출한다.
    """

    SOURCE_NAME = "blind"
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Accept-Language": "ko-KR,ko;q=0.9",
    }

    def get_page_url(self, page_num):
        return (
            f"https://www.teamblind.com/kr/topics/Finance"
            f"?page={page_num}"
        )

    def parse_posts(self, soup):
        """블라인드는 HTML 파싱 방식으로 게시글을 추출한다."""
        posts = []

        # 게시글 목록 추출
        items = soup.select("ul.topic_list li a, article a, div.post-list a")

        for item in items:
            try:
                title = item.get_text(strip=True)
                if not title or len(title) < 2:
                    continue

                url = item.get("href", "")
                if url and not url.startswith("http"):
                    url = "https://www.teamblind.com" + url

                posts.append({
                    "title": title,
                    "body": None,
                    "comment_count": 0,
                    "published_at": datetime.now().isoformat(),
                    "url": url,
                })
            except Exception as e:
                print(f"[{self.SOURCE_NAME}] 파싱 오류: {e}")
                continue

        return posts
