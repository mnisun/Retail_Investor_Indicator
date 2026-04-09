"""감성 분석 엔진 - 키워드 사전 기반"""
import json
from datetime import datetime, timedelta
from config import (
    GREED_KEYWORDS, FEAR_KEYWORDS, PANIC_KEYWORDS, PANIC_MULTIPLIER,
    EXTREME_GREED_THRESHOLD, EXTREME_FEAR_THRESHOLD,
)
from database import (
    get_connection, insert_sentiment, insert_hourly_index, get_recent_posts,
)


def analyze_text(text):
    """텍스트에서 탐욕/공포 점수를 계산한다.

    Returns:
        dict: score(0~100), greed_count, fear_count, matched_keywords
    """
    if not text:
        return {"score": 50, "greed_count": 0, "fear_count": 0, "matched_keywords": []}

    text_lower = text.lower()
    greed_total = 0
    fear_total = 0
    greed_count = 0
    fear_count = 0
    matched = []

    for keyword, weight in GREED_KEYWORDS.items():
        count = text_lower.count(keyword)
        if count > 0:
            greed_total += weight * count
            greed_count += count
            matched.append(f"+{keyword}({count})")

    for keyword, weight in FEAR_KEYWORDS.items():
        count = text_lower.count(keyword)
        if count > 0:
            fear_total += abs(weight) * count
            fear_count += count
            matched.append(f"-{keyword}({count})")

    # 0~100 점수로 변환 (50이 중립)
    total = greed_total + fear_total
    if total == 0:
        score = 50.0
    else:
        # 탐욕 비율을 0~100으로 매핑
        score = (greed_total / total) * 100

    return {
        "score": round(score, 2),
        "greed_count": greed_count,
        "fear_count": fear_count,
        "matched_keywords": matched,
    }


def analyze_recent_posts(hours=1, source=None):
    """최근 게시글들을 분석하고 DB에 저장한다."""
    posts = get_recent_posts(hours=hours, source=source)
    results = []

    for post in posts:
        text = (post["title"] or "") + " " + (post["body"] or "")
        analysis = analyze_text(text)

        insert_sentiment(
            post_id=post["id"],
            score=analysis["score"],
            greed_count=analysis["greed_count"],
            fear_count=analysis["fear_count"],
            matched_keywords=json.dumps(analysis["matched_keywords"], ensure_ascii=False),
        )
        results.append(analysis)

    return results


def calculate_index(hours=1, source=None):
    """시간별 인간지표 지수를 계산한다.

    Returns:
        dict: index_value(0~100), total_posts, greed_ratio, fear_ratio,
              panic_count, signal
    """
    posts = get_recent_posts(hours=hours, source=source)
    if not posts:
        return {
            "index_value": 50.0,
            "total_posts": 0,
            "greed_ratio": 0.0,
            "fear_ratio": 0.0,
            "panic_count": 0,
            "signal": "데이터 없음",
        }

    scores = []
    total_greed = 0
    total_fear = 0
    panic_count = 0

    for post in posts:
        text = (post["title"] or "") + " " + (post["body"] or "")
        analysis = analyze_text(text)
        scores.append(analysis["score"])
        total_greed += analysis["greed_count"]
        total_fear += analysis["fear_count"]

        # 패닉 키워드 카운트
        for kw in PANIC_KEYWORDS:
            if kw in text:
                panic_count += text.count(kw)

    total_posts = len(posts)
    avg_score = sum(scores) / len(scores) if scores else 50.0
    total_keywords = total_greed + total_fear
    greed_ratio = (total_greed / total_keywords * 100) if total_keywords > 0 else 50.0
    fear_ratio = (total_fear / total_keywords * 100) if total_keywords > 0 else 50.0

    # 인간지표 지수 계산 (가중 평균)
    index_value = avg_score

    # 시그널 결정
    if index_value >= EXTREME_GREED_THRESHOLD:
        signal = "🔴 극단적 탐욕 - 매도 검토"
    elif index_value >= 60:
        signal = "🟠 탐욕 - 주의"
    elif index_value >= 40:
        signal = "🟢 중립"
    elif index_value >= EXTREME_FEAR_THRESHOLD:
        signal = "🟡 공포 - 관심"
    else:
        signal = "🔵 극단적 공포 - 매수 검토"

    return {
        "index_value": round(index_value, 2),
        "total_posts": total_posts,
        "greed_ratio": round(greed_ratio, 2),
        "fear_ratio": round(fear_ratio, 2),
        "panic_count": panic_count,
        "signal": signal,
    }


def check_panic_alert(hours=1):
    """패닉 키워드 급증 여부를 확인한다.

    Returns:
        dict or None: 알림이 필요한 경우 정보를 반환
    """
    # 현재 시간대 패닉 키워드 수
    current = calculate_index(hours=1)
    # 최근 24시간 평균 대비 비교
    daily = calculate_index(hours=24)

    if daily["total_posts"] == 0 or daily["panic_count"] == 0:
        return None

    hourly_avg_panic = daily["panic_count"] / 24
    if hourly_avg_panic == 0:
        return None

    ratio = current["panic_count"] / hourly_avg_panic

    if ratio >= PANIC_MULTIPLIER:
        return {
            "current_panic": current["panic_count"],
            "avg_panic": round(hourly_avg_panic, 2),
            "ratio": round(ratio, 2),
            "index_value": current["index_value"],
            "signal": current["signal"],
        }

    return None
