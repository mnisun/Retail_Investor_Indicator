"""인간지표 추적기 - 메인 실행 스크립트

사용법:
    python main.py scrape          # 데이터 수집
    python main.py analyze         # 감성 분석 실행
    python main.py report          # 현재 지표 리포트
    python main.py run             # 수집 + 분석 + 알림 (전체 파이프라인)
    streamlit run app.py           # 웹 대시보드 실행
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime
from database import init_db
from analyzer import calculate_index, analyze_recent_posts, check_panic_alert
from price_fetcher import fetch_current_price, fetch_hourly_candles, get_multiple_prices
from notifier import send_telegram_message, format_panic_alert, format_daily_report


def scrape():
    """모든 소스에서 데이터를 수집한다."""
    print("=" * 50)
    print(f"[{datetime.now()}] 데이터 수집 시작")
    print("=" * 50)

    from scrapers import DcInsideScraper, PpomppuScraper, BlindScraper

    scrapers = [
        DcInsideScraper(gallery="bitcoin"),
        DcInsideScraper(gallery="stock"),
        PpomppuScraper(),
        BlindScraper(),
    ]

    total = 0
    for scraper in scrapers:
        try:
            posts = scraper.scrape(pages=2)
            total += len(posts)
        except Exception as e:
            print(f"[오류] {scraper.SOURCE_NAME}: {e}")

    print(f"\n총 {total}개 게시글 수집 완료")
    return total


def analyze():
    """수집된 데이터를 분석한다."""
    print("=" * 50)
    print(f"[{datetime.now()}] 감성 분석 시작")
    print("=" * 50)

    results = analyze_recent_posts(hours=1)
    print(f"분석 완료: {len(results)}개 게시글")

    index = calculate_index(hours=1)
    print(f"\n--- 인간지표 현황 ---")
    print(f"지수: {index['index_value']}점")
    print(f"시그널: {index['signal']}")
    print(f"총 게시글: {index['total_posts']}개")
    print(f"탐욕 비율: {index['greed_ratio']}%")
    print(f"공포 비율: {index['fear_ratio']}%")
    print(f"패닉 키워드: {index['panic_count']}회")

    return index


def report():
    """현재 인간지표 리포트를 출력한다."""
    print("=" * 50)
    print("  📊 인간지표 추적기 리포트")
    print("=" * 50)

    index = calculate_index(hours=1)
    print(f"\n🎯 인간지표 지수: {index['index_value']}점")
    print(f"📡 시그널: {index['signal']}")
    print(f"📝 분석 게시글: {index['total_posts']}개")
    print(f"🔴 탐욕 비율: {index['greed_ratio']}%")
    print(f"🔵 공포 비율: {index['fear_ratio']}%")
    print(f"⚠️ 패닉 키워드: {index['panic_count']}회")

    print("\n💰 코인 가격:")
    prices = get_multiple_prices()
    for symbol, data in prices.items():
        arrow = "📈" if data["change_rate"] > 0 else "📉"
        print(f"  {arrow} {symbol}: {data['price']:,.0f}원 ({data['change_rate']:+.2f}%)")


def run():
    """전체 파이프라인을 실행한다."""
    init_db()

    # 1. 데이터 수집
    scrape()

    # 2. 가격 데이터 수집
    print("\n[가격] BTC 가격 데이터 수집 중...")
    fetch_current_price("KRW-BTC")
    fetch_hourly_candles("KRW-BTC", count=24)

    # 3. 감성 분석
    index = analyze()

    # 4. 패닉 알림 체크
    alert = check_panic_alert()
    if alert:
        msg = format_panic_alert(alert)
        print(f"\n🚨 패닉 알림 발생!\n{msg}")
        send_telegram_message(msg)

    # 5. 리포트
    prices = get_multiple_prices()
    daily_msg = format_daily_report(index, prices)
    print(f"\n{daily_msg}")

    print("\n✅ 파이프라인 실행 완료")


def main():
    init_db()

    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1].lower()
    commands = {
        "scrape": scrape,
        "analyze": analyze,
        "report": report,
        "run": run,
    }

    if command in commands:
        commands[command]()
    else:
        print(f"알 수 없는 명령어: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
