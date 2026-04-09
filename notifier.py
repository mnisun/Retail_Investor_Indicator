"""텔레그램 알림 모듈"""
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_telegram_message(message):
    """텔레그램 메시지를 전송한다.

    사전 설정:
    1. @BotFather에서 봇 생성 후 토큰 발급
    2. 봇에 /start 메시지 보낸 후 chat_id 확인
    3. 환경변수 설정:
       export TELEGRAM_BOT_TOKEN="your_token"
       export TELEGRAM_CHAT_ID="your_chat_id"
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[알림] 텔레그램 설정이 없습니다. 환경변수를 확인하세요.")
        print(f"  메시지 내용: {message}")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("[알림] 텔레그램 메시지 전송 완료")
        return True
    except requests.RequestException as e:
        print(f"[알림] 텔레그램 전송 실패: {e}")
        return False


def format_panic_alert(alert_data):
    """패닉 알림 메시지를 포맷한다."""
    return (
        "🚨 <b>인간지표 패닉 알림!</b>\n\n"
        f"현재 패닉 키워드 수: <b>{alert_data['current_panic']}회</b>\n"
        f"평균 대비: <b>{alert_data['ratio']}배</b> 급증\n"
        f"인간지표 지수: <b>{alert_data['index_value']}점</b>\n"
        f"시그널: {alert_data['signal']}\n\n"
        "⚡ 커뮤니티에서 극단적 공포가 감지되었습니다.\n"
        "역사적으로 이 시점이 '찐 바닥'인 경우가 많습니다."
    )


def format_daily_report(index_data, price_data=None):
    """일일 리포트 메시지를 포맷한다."""
    msg = (
        "📊 <b>인간지표 일일 리포트</b>\n\n"
        f"지수: <b>{index_data['index_value']}점</b>\n"
        f"시그널: {index_data['signal']}\n"
        f"분석 게시글: {index_data['total_posts']}개\n"
        f"탐욕 비율: {index_data['greed_ratio']}%\n"
        f"공포 비율: {index_data['fear_ratio']}%\n"
        f"패닉 키워드: {index_data['panic_count']}회\n"
    )

    if price_data:
        msg += "\n💰 <b>현재 가격</b>\n"
        for symbol, data in price_data.items():
            arrow = "📈" if data["change_rate"] > 0 else "📉"
            msg += f"  {arrow} {symbol}: {data['price']:,.0f}원 ({data['change_rate']:+.2f}%)\n"

    return msg
