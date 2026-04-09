"""디시인사이드 갤러리 스크래퍼"""
from datetime import datetime
from scrapers.base import BaseScraper


class DcInsideScraper(BaseScraper):
    """디시인사이드 비트코인/주식 갤러리 스크래퍼"""

    SOURCE_NAME = "dcinside"
    GALLERY_IDS = {
        "bitcoin": "bitcoins",
        "stock": "stockus",
    }

    def __init__(self, gallery="bitcoin"):
        self.gallery_id = self.GALLERY_IDS.get(gallery, "bitcoins")
        self.SOURCE_NAME = f"dcinside_{gallery}"

    def get_page_url(self, page_num):
        return (
            f"https://gall.dcinside.com/board/lists/"
            f"?id={self.gallery_id}&page={page_num}"
        )

    def parse_posts(self, soup):
        posts = []
        rows = soup.select("tr.ub-content.us-post")

        for row in rows:
            try:
                # 공지사항 제외
                if row.select_one(".icon_notice"):
                    continue

                title_el = row.select_one("td.gall_tit a")
                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                url = title_el.get("href", "")
                if url and not url.startswith("http"):
                    url = "https://gall.dcinside.com" + url

                # 댓글 수
                reply_el = row.select_one("td.gall_tit a.reply_numbox span")
                comment_count = 0
                if reply_el:
                    try:
                        comment_count = int(reply_el.get_text(strip=True))
                    except ValueError:
                        pass

                # 작성 시간
                date_el = row.select_one("td.gall_date")
                published_at = None
                if date_el:
                    date_str = date_el.get("title", date_el.get_text(strip=True))
                    try:
                        published_at = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").isoformat()
                    except ValueError:
                        published_at = datetime.now().isoformat()

                posts.append({
                    "title": title,
                    "body": None,
                    "comment_count": comment_count,
                    "published_at": published_at,
                    "url": url,
                })
            except Exception as e:
                print(f"[{self.SOURCE_NAME}] 파싱 오류: {e}")
                continue

        return posts
