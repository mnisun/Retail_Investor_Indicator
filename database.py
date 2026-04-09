"""SQLite 데이터베이스 모델 및 초기화"""
import sqlite3
import os
from datetime import datetime
from config import DB_PATH


def get_connection():
    """DB 연결을 반환한다."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """테이블을 생성한다."""
    conn = get_connection()
    cursor = conn.cursor()

    # 게시글 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            body TEXT,
            comment_count INTEGER DEFAULT 0,
            published_at TIMESTAMP,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            url TEXT,
            UNIQUE(source, title, published_at)
        )
    """)

    # 감성 분석 결과 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sentiment_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            score REAL NOT NULL,
            greed_count INTEGER DEFAULT 0,
            fear_count INTEGER DEFAULT 0,
            matched_keywords TEXT,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(id)
        )
    """)

    # 시간별 집계 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hourly_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP NOT NULL UNIQUE,
            source TEXT,
            total_posts INTEGER DEFAULT 0,
            avg_score REAL DEFAULT 50.0,
            greed_ratio REAL DEFAULT 0.0,
            fear_ratio REAL DEFAULT 0.0,
            panic_keyword_count INTEGER DEFAULT 0,
            index_value REAL DEFAULT 50.0
        )
    """)

    # 가격 데이터 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            price REAL NOT NULL,
            volume REAL,
            timestamp TIMESTAMP NOT NULL,
            UNIQUE(symbol, timestamp)
        )
    """)

    conn.commit()
    conn.close()


def insert_post(source, title, body=None, comment_count=0, published_at=None, url=None):
    """게시글을 저장한다."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT OR IGNORE INTO posts (source, title, body, comment_count, published_at, url)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (source, title, body, comment_count, published_at, url),
        )
        conn.commit()
    finally:
        conn.close()


def insert_sentiment(post_id, score, greed_count, fear_count, matched_keywords):
    """감성 분석 결과를 저장한다."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO sentiment_scores (post_id, score, greed_count, fear_count, matched_keywords)
               VALUES (?, ?, ?, ?, ?)""",
            (post_id, score, greed_count, fear_count, matched_keywords),
        )
        conn.commit()
    finally:
        conn.close()


def insert_hourly_index(timestamp, source, total_posts, avg_score, greed_ratio, fear_ratio, panic_count, index_value):
    """시간별 지표를 저장한다."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT OR REPLACE INTO hourly_index
               (timestamp, source, total_posts, avg_score, greed_ratio, fear_ratio, panic_keyword_count, index_value)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (timestamp, source, total_posts, avg_score, greed_ratio, fear_ratio, panic_count, index_value),
        )
        conn.commit()
    finally:
        conn.close()


def insert_price(symbol, price, volume, timestamp):
    """가격 데이터를 저장한다."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT OR IGNORE INTO price_data (symbol, price, volume, timestamp)
               VALUES (?, ?, ?, ?)""",
            (symbol, price, volume, timestamp),
        )
        conn.commit()
    finally:
        conn.close()


def get_recent_posts(hours=1, source=None):
    """최근 N시간 이내 게시글을 조회한다."""
    conn = get_connection()
    try:
        query = """
            SELECT * FROM posts
            WHERE scraped_at >= datetime('now', ?)
        """
        params = [f"-{hours} hours"]
        if source:
            query += " AND source = ?"
            params.append(source)
        query += " ORDER BY scraped_at DESC"
        return conn.execute(query, params).fetchall()
    finally:
        conn.close()


def get_hourly_index_data(days=7, source=None):
    """최근 N일간 시간별 지표 데이터를 조회한다."""
    conn = get_connection()
    try:
        query = """
            SELECT * FROM hourly_index
            WHERE timestamp >= datetime('now', ?)
        """
        params = [f"-{days} days"]
        if source:
            query += " AND source = ?"
            params.append(source)
        query += " ORDER BY timestamp ASC"
        return conn.execute(query, params).fetchall()
    finally:
        conn.close()


def get_price_data(symbol="BTC", days=7):
    """최근 N일간 가격 데이터를 조회한다."""
    conn = get_connection()
    try:
        return conn.execute(
            """SELECT * FROM price_data
               WHERE symbol = ? AND timestamp >= datetime('now', ?)
               ORDER BY timestamp ASC""",
            (symbol, f"-{days} days"),
        ).fetchall()
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print(f"데이터베이스 초기화 완료: {DB_PATH}")
