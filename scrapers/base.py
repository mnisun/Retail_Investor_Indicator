"""스크래퍼 베이스 클래스"""
import time
import random
import requests
from bs4 import BeautifulSoup
from database import insert_post


class BaseScraper:
    """모든 스크래퍼의 기본 클래스"""

    SOURCE_NAME = "base"
    BASE_URL = ""
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    def fetch_page(self, url):
        """페이지 HTML을 가져온다."""
        try:
            response = requests.get(url, headers=self.HEADERS, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.text, "lxml")
        except requests.RequestException as e:
            print(f"[{self.SOURCE_NAME}] 페이지 요청 실패: {e}")
            return None

    def parse_posts(self, soup):
        """게시글 목록을 파싱한다. 하위 클래스에서 구현."""
        raise NotImplementedError

    def scrape(self, pages=1):
        """스크래핑을 실행하고 DB에 저장한다."""
        all_posts = []
        for page in range(1, pages + 1):
            url = self.get_page_url(page)
            print(f"[{self.SOURCE_NAME}] 스크래핑 중: {url}")
            soup = self.fetch_page(url)
            if soup is None:
                continue

            posts = self.parse_posts(soup)
            for post in posts:
                insert_post(
                    source=self.SOURCE_NAME,
                    title=post.get("title", ""),
                    body=post.get("body"),
                    comment_count=post.get("comment_count", 0),
                    published_at=post.get("published_at"),
                    url=post.get("url"),
                )
            all_posts.extend(posts)

            # 요청 간 딜레이
            if page < pages:
                time.sleep(random.uniform(1.5, 3.0))

        print(f"[{self.SOURCE_NAME}] 총 {len(all_posts)}개 게시글 수집 완료")
        return all_posts

    def get_page_url(self, page_num):
        """페이지 번호에 해당하는 URL을 반환한다. 하위 클래스에서 구현."""
        raise NotImplementedError
