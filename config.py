"""프로젝트 설정"""
import os

# 데이터베이스
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "sentiment.db")

# 스크래핑 대상
SCRAPE_TARGETS = {
    "dcinside_bitcoin": {
        "name": "디시인사이드 비트코인 갤러리",
        "url": "https://gall.dcinside.com/board/lists/?id=bitcoins",
        "category": "crypto",
    },
    "dcinside_stock": {
        "name": "디시인사이드 주식 갤러리",
        "url": "https://gall.dcinside.com/board/lists/?id=stockus",
        "category": "stock",
    },
    "ppomppu": {
        "name": "뽐뿌 재테크 포럼",
        "url": "https://www.ppomppu.co.kr/zboard/zboard.php?id=stock",
        "category": "general",
    },
    "blind": {
        "name": "블라인드 재테크 게시판",
        "url": "https://www.teamblind.com/kr/topics/Finance",
        "category": "general",
    },
}

# 감성 분석 키워드 사전
GREED_KEYWORDS = {
    # 극단적 탐욕 (+3)
    "풀매수": 3, "올인": 3, "영끌": 3, "퇴사": 3, "펜트하우스": 3,
    "람보르기니": 3, "벤틀리": 3, "파이어족": 3,
    # 높은 탐욕 (+2)
    "가즈아": 2, "수익 인증": 2, "떡상": 2, "불장": 2, "대박": 2,
    "로또": 2, "횡재": 2, "존버 승리": 2, "익절": 2, "지금이라도": 2,
    "무조건 산다": 2, "안사면 바보": 2, "천만원 수익": 2, "억대 수익": 2,
    # 일반 탐욕 (+1)
    "매수": 1, "상승": 1, "오른다": 1, "반등": 1, "좋은 기회": 1,
    "저점": 1, "바겐세일": 1, "줍줍": 1, "존버": 1, "홀딩": 1,
    "수익": 1, "이득": 1, "벌었다": 1, "올랐다": 1, "급등": 1,
}

FEAR_KEYWORDS = {
    # 극단적 공포 (-3)
    "자살": -3, "한강": -3, "살려줘": -3, "전재산": -3, "파산": -3,
    "빚": -3, "대출 갚": -3, "인생 끝": -3,
    # 높은 공포 (-2)
    "손절": -2, "끝났다": -2, "사기": -2, "설거지": -2, "폭락": -2,
    "쪽박": -2, "물렸다": -2, "반토막": -2, "깡통": -2, "탈출": -2,
    "떡락": -2, "폭망": -2, "망했다": -2, "거품": -2, "버블": -2,
    # 일반 공포 (-1)
    "매도": -1, "하락": -1, "떨어진다": -1, "위험": -1, "조심": -1,
    "불안": -1, "걱정": -1, "빠진다": -1, "약세": -1, "베어": -1,
    "손실": -1, "잃었다": -1, "내렸다": -1, "급락": -1, "조정": -1,
}

# 인간지표 점수 기준
EXTREME_GREED_THRESHOLD = 80  # 극단적 탐욕 → 매도 검토
GREED_THRESHOLD = 60
NEUTRAL_LOW = 40
EXTREME_FEAR_THRESHOLD = 20   # 극단적 공포 → 매수 검토

# 패닉 알림 설정
PANIC_KEYWORDS = ["한강", "자살", "살려줘", "파산", "인생 끝"]
PANIC_MULTIPLIER = 3  # 평소 대비 N배 이상이면 알림

# 텔레그램 설정 (환경변수로 관리)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# 스크래핑 간격 (분)
SCRAPE_INTERVAL_MINUTES = 30
