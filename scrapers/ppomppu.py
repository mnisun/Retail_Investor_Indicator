"""뽐뿌 재테크 포럼 스크래퍼"""
from datetime import datetime
from scrapers.base import BaseScraper


class PpomppuScraper(BaseScraper):
    """뽐뿌 재테크(주식) 게시판 스크래퍼"""

    SOURCE_NAME = "ppomppu"

    def get_page_url(self, page_num):
        return (
            f"https://www.ppomppu.co.kr/zboard/zboard.php"
            f"?id=stock&page={page_num}"
        )

    def parse_posts(self, soup):
        posts = []
        rows = soup.select("tr.baseList")

        for row in rows:
            try:
                title_el = row.select_one("a.baseList-title")
                if not title_el:
                    # 대체 셀렉터 시도
                    title_el = row.select_one("td.baseList-space a")
                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                url = title_el.get("href", "")
                if url and not url.startswith("http"):
                    url = "https://www.ppomppu.co.kr/zboard/" + url

                # 댓글 수
                comment_count = 0
                reply_el = row.select_one("span.baseList-c")
                if reply_el:
                    try:
                        comment_count = int(reply_el.get_text(strip=True).strip("[]"))
                    except ValueError:
                        pass

                # 작성 시간
                date_el = row.select_one("td.baseList-space time")
                if not date_el:
                    date_el = row.select_one("td.date")
                published_at = None
                if date_el:
                    date_str = date_el.get_text(strip=True)
                    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y.%m.%d", "%m/%d %H:%M"):
                        try:
                            published_at = datetime.strptime(date_str, fmt).isoformat()
                            break
                        except ValueError:
                            continue
                    if not published_at:
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
