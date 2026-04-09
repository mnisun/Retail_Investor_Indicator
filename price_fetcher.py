"""Upbit API를 통한 코인 가격 데이터 수집"""
import requests
from datetime import datetime
from database import insert_price, get_connection


UPBIT_TICKER_URL = "https://api.upbit.com/v1/ticker"
UPBIT_CANDLES_URL = "https://api.upbit.com/v1/candles/minutes/60"


def fetch_current_price(market="KRW-BTC"):
    """현재 가격을 조회한다."""
    try:
        response = requests.get(
            UPBIT_TICKER_URL,
            params={"markets": market},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
        if data:
            item = data[0]
            symbol = market.split("-")[1]
            price = item["trade_price"]
            volume = item.get("acc_trade_volume_24h", 0)
            timestamp = datetime.now().isoformat()

            insert_price(symbol, price, volume, timestamp)
            return {
                "symbol": symbol,
                "price": price,
                "volume": volume,
                "timestamp": timestamp,
                "change_rate": item.get("signed_change_rate", 0) * 100,
            }
    except requests.RequestException as e:
        print(f"[Upbit] 가격 조회 실패: {e}")
    return None


def fetch_hourly_candles(market="KRW-BTC", count=168):
    """시간봉 데이터를 가져온다 (기본 7일 = 168시간)."""
    try:
        response = requests.get(
            UPBIT_CANDLES_URL,
            params={"market": market, "count": min(count, 200)},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        symbol = market.split("-")[1]
        for candle in data:
            timestamp = candle["candle_date_time_kst"]
            price = candle["trade_price"]
            volume = candle.get("candle_acc_trade_volume", 0)
            insert_price(symbol, price, volume, timestamp)

        return data
    except requests.RequestException as e:
        print(f"[Upbit] 시간봉 조회 실패: {e}")
        return []


def get_multiple_prices(markets=None):
    """여러 코인 가격을 한번에 조회한다."""
    if markets is None:
        markets = ["KRW-BTC", "KRW-ETH", "KRW-XRP"]

    results = {}
    try:
        response = requests.get(
            UPBIT_TICKER_URL,
            params={"markets": ",".join(markets)},
            timeout=5,
        )
        response.raise_for_status()
        for item in response.json():
            symbol = item["market"].split("-")[1]
            results[symbol] = {
                "price": item["trade_price"],
                "change_rate": round(item.get("signed_change_rate", 0) * 100, 2),
                "volume": item.get("acc_trade_volume_24h", 0),
            }
    except requests.RequestException as e:
        print(f"[Upbit] 다중 가격 조회 실패: {e}")
    return results
