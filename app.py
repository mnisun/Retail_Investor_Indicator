"""인간지표 추적기 - Streamlit 대시보드"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
import json

from database import init_db, get_connection, get_hourly_index_data, get_price_data
from analyzer import analyze_text, calculate_index, check_panic_alert
from price_fetcher import fetch_current_price, get_multiple_prices, fetch_hourly_candles

# 페이지 설정
st.set_page_config(
    page_title="인간지표 추적기",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# DB 초기화
init_db()

# --- 커스텀 CSS ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #1a1a2e, #16213e, #0f3460);
        color: white;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .fear-gauge { color: #3498db; font-weight: bold; }
    .greed-gauge { color: #e74c3c; font-weight: bold; }
    .neutral-gauge { color: #2ecc71; font-weight: bold; }
    .stMetric { text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- 헤더 ---
st.markdown('<div class="main-header">📊 인간지표 추적기<br><small style="font-size:0.4em">커뮤니티 여론으로 읽는 매매 타이밍</small></div>', unsafe_allow_html=True)

# --- 사이드바 ---
with st.sidebar:
    st.header("⚙️ 설정")

    analysis_period = st.selectbox(
        "분석 기간",
        options=[1, 3, 6, 12, 24],
        index=0,
        format_func=lambda x: f"최근 {x}시간",
    )

    selected_sources = st.multiselect(
        "데이터 소스",
        options=["전체", "dcinside_bitcoin", "dcinside_stock", "ppomppu", "blind"],
        default=["전체"],
    )

    chart_period = st.slider("차트 표시 기간 (일)", 1, 30, 7)

    st.divider()
    st.header("🔔 알림 상태")
    panic_alert = check_panic_alert()
    if panic_alert:
        st.error(f"🚨 패닉 감지! (평소 대비 {panic_alert['ratio']}배)")
    else:
        st.success("✅ 정상 범위")

    st.divider()
    st.header("📝 텍스트 분석기")
    test_text = st.text_area("텍스트를 입력하면 감성 분석 결과를 보여줍니다", height=100)
    if test_text:
        result = analyze_text(test_text)
        st.json(result)

    st.divider()
    st.caption("💡 데이터를 수집하려면 터미널에서 `python main.py scrape`를 실행하세요.")


# --- 메인 대시보드 ---

# 현재 지표 계산
source_filter = None if "전체" in selected_sources else selected_sources[0] if len(selected_sources) == 1 else None
current_index = calculate_index(hours=analysis_period, source=source_filter)

# 1행: 핵심 지표 카드
col1, col2, col3, col4 = st.columns(4)

with col1:
    index_val = current_index["index_value"]
    if index_val >= 60:
        delta_color = "inverse"
    elif index_val <= 40:
        delta_color = "normal"
    else:
        delta_color = "off"
    st.metric(
        label="🎯 인간지표 지수",
        value=f"{index_val:.1f}점",
        delta=current_index["signal"],
        delta_color=delta_color,
    )

with col2:
    st.metric(
        label="📝 분석 게시글",
        value=f"{current_index['total_posts']}개",
        delta=f"최근 {analysis_period}시간",
        delta_color="off",
    )

with col3:
    st.metric(
        label="🔴 탐욕 비율",
        value=f"{current_index['greed_ratio']:.1f}%",
    )

with col4:
    st.metric(
        label="🔵 공포 비율",
        value=f"{current_index['fear_ratio']:.1f}%",
    )

st.divider()

# 2행: 공포/탐욕 게이지 + 가격 정보
col_gauge, col_price = st.columns([1, 1])

with col_gauge:
    st.subheader("공포 & 탐욕 게이지")
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=current_index["index_value"],
        title={"text": "인간지표 지수", "font": {"size": 20}},
        delta={"reference": 50, "increasing": {"color": "#e74c3c"}, "decreasing": {"color": "#3498db"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": "#2c3e50"},
            "steps": [
                {"range": [0, 20], "color": "#3498db"},    # 극단적 공포
                {"range": [20, 40], "color": "#85c1e9"},   # 공포
                {"range": [40, 60], "color": "#2ecc71"},   # 중립
                {"range": [60, 80], "color": "#f39c12"},   # 탐욕
                {"range": [80, 100], "color": "#e74c3c"},  # 극단적 탐욕
            ],
            "threshold": {
                "line": {"color": "black", "width": 4},
                "thickness": 0.75,
                "value": current_index["index_value"],
            },
        },
    ))
    fig_gauge.update_layout(height=300, margin=dict(t=50, b=0, l=30, r=30))
    st.plotly_chart(fig_gauge, use_container_width=True)

with col_price:
    st.subheader("실시간 코인 가격")
    prices = get_multiple_prices()
    if prices:
        for symbol, data in prices.items():
            change = data["change_rate"]
            arrow = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            color = "red" if change > 0 else "blue" if change < 0 else "gray"
            st.markdown(
                f"**{arrow} {symbol}** &nbsp; "
                f"`{data['price']:,.0f}원` &nbsp; "
                f"<span style='color:{color}'>({change:+.2f}%)</span>",
                unsafe_allow_html=True,
            )
    else:
        st.info("가격 데이터를 불러오는 중...")
        # 데모 데이터 표시
        st.markdown("**BTC** `데이터 수집 필요` | **ETH** `데이터 수집 필요`")

st.divider()

# 3행: 시계열 차트 - 인간지표 vs 가격
st.subheader("📈 인간지표 지수 vs 코인 가격 추이")

# DB에서 데이터 로드
hourly_data = get_hourly_index_data(days=chart_period)
price_history = get_price_data(symbol="BTC", days=chart_period)

if hourly_data or price_history:
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=("인간지표 지수", "BTC 가격 (KRW)"),
        row_heights=[0.5, 0.5],
    )

    # 인간지표 지수
    if hourly_data:
        df_index = pd.DataFrame([dict(row) for row in hourly_data])
        fig.add_trace(
            go.Scatter(
                x=df_index["timestamp"],
                y=df_index["index_value"],
                mode="lines+markers",
                name="인간지표 지수",
                line=dict(color="#8e44ad", width=2),
                fill="tozeroy",
                fillcolor="rgba(142, 68, 173, 0.1)",
            ),
            row=1, col=1,
        )
        # 기준선
        fig.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="매도 검토", row=1, col=1)
        fig.add_hline(y=20, line_dash="dash", line_color="blue", annotation_text="매수 검토", row=1, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="gray", row=1, col=1)

    # BTC 가격
    if price_history:
        df_price = pd.DataFrame([dict(row) for row in price_history])
        fig.add_trace(
            go.Scatter(
                x=df_price["timestamp"],
                y=df_price["price"],
                mode="lines",
                name="BTC 가격",
                line=dict(color="#f39c12", width=2),
            ),
            row=2, col=1,
        )

    fig.update_layout(
        height=600,
        showlegend=True,
        template="plotly_dark",
        margin=dict(t=40, b=20),
    )
    fig.update_yaxes(title_text="지수 (0~100)", row=1, col=1)
    fig.update_yaxes(title_text="가격 (KRW)", row=2, col=1)

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info(
        "📌 아직 수집된 데이터가 없습니다.\n\n"
        "터미널에서 다음 명령어를 실행하여 데이터를 수집하세요:\n"
        "```\npython main.py scrape\n```"
    )

    # 데모 차트 표시
    st.subheader("🎮 데모 차트 (샘플 데이터)")
    demo_dates = pd.date_range(end=datetime.now(), periods=168, freq="h")
    import numpy as np
    np.random.seed(42)

    # 사인파 + 노이즈로 시뮬레이션
    demo_index = 50 + 30 * np.sin(np.linspace(0, 4 * np.pi, 168)) + np.random.normal(0, 5, 168)
    demo_index = np.clip(demo_index, 0, 100)
    demo_price = 130000000 + 5000000 * np.sin(np.linspace(0, 4 * np.pi, 168)) + np.cumsum(np.random.normal(0, 200000, 168))

    fig_demo = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=("인간지표 지수 (데모)", "BTC 가격 (데모)"),
        row_heights=[0.5, 0.5],
    )

    fig_demo.add_trace(
        go.Scatter(x=demo_dates, y=demo_index, mode="lines", name="인간지표 지수",
                   line=dict(color="#8e44ad", width=2), fill="tozeroy",
                   fillcolor="rgba(142, 68, 173, 0.1)"),
        row=1, col=1,
    )
    fig_demo.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="매도 검토", row=1, col=1)
    fig_demo.add_hline(y=20, line_dash="dash", line_color="blue", annotation_text="매수 검토", row=1, col=1)

    fig_demo.add_trace(
        go.Scatter(x=demo_dates, y=demo_price, mode="lines", name="BTC 가격",
                   line=dict(color="#f39c12", width=2)),
        row=2, col=1,
    )

    fig_demo.update_layout(height=600, showlegend=True, template="plotly_dark")
    st.plotly_chart(fig_demo, use_container_width=True)

st.divider()

# 4행: 커뮤니티별 글 리젠 속도 + 키워드 분포
col_regen, col_keywords = st.columns(2)

with col_regen:
    st.subheader("⚡ 커뮤니티별 게시글 리젠 속도")
    conn = get_connection()
    try:
        regen_data = conn.execute("""
            SELECT source,
                   COUNT(*) as post_count,
                   MIN(scraped_at) as first_post,
                   MAX(scraped_at) as last_post
            FROM posts
            WHERE scraped_at >= datetime('now', '-24 hours')
            GROUP BY source
            ORDER BY post_count DESC
        """).fetchall()
    finally:
        conn.close()

    if regen_data:
        df_regen = pd.DataFrame([dict(r) for r in regen_data])
        source_names = {
            "dcinside_bitcoin": "DC 비트코인",
            "dcinside_stock": "DC 주식",
            "ppomppu": "뽐뿌",
            "blind": "블라인드",
        }
        df_regen["display_name"] = df_regen["source"].map(source_names).fillna(df_regen["source"])

        fig_bar = px.bar(
            df_regen, x="display_name", y="post_count",
            color="post_count",
            color_continuous_scale="Viridis",
            labels={"display_name": "커뮤니티", "post_count": "게시글 수"},
        )
        fig_bar.update_layout(height=300, template="plotly_dark", showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("수집된 데이터가 없습니다.")

with col_keywords:
    st.subheader("🔤 최근 감지된 키워드 TOP 10")
    conn = get_connection()
    try:
        keyword_data = conn.execute("""
            SELECT matched_keywords FROM sentiment_scores
            WHERE analyzed_at >= datetime('now', '-24 hours')
            AND matched_keywords IS NOT NULL
            AND matched_keywords != '[]'
        """).fetchall()
    finally:
        conn.close()

    if keyword_data:
        keyword_counts = {}
        for row in keyword_data:
            try:
                keywords = json.loads(row["matched_keywords"])
                for kw in keywords:
                    # "+풀매수(2)" → "풀매수"
                    clean_kw = kw.split("(")[0].lstrip("+-")
                    keyword_counts[clean_kw] = keyword_counts.get(clean_kw, 0) + 1
            except (json.JSONDecodeError, TypeError):
                continue

        if keyword_counts:
            top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            df_kw = pd.DataFrame(top_keywords, columns=["키워드", "빈도"])
            fig_kw = px.bar(
                df_kw, x="빈도", y="키워드", orientation="h",
                color="빈도", color_continuous_scale="RdYlBu_r",
            )
            fig_kw.update_layout(height=300, template="plotly_dark", showlegend=False, yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_kw, use_container_width=True)
        else:
            st.info("감지된 키워드가 없습니다.")
    else:
        st.info("분석된 데이터가 없습니다.")

st.divider()

# 5행: 최근 게시글 테이블
st.subheader("📋 최근 수집된 게시글")
conn = get_connection()
try:
    recent_posts = conn.execute("""
        SELECT p.source, p.title, p.comment_count, p.published_at, p.url,
               s.score, s.matched_keywords
        FROM posts p
        LEFT JOIN sentiment_scores s ON p.id = s.post_id
        ORDER BY p.scraped_at DESC
        LIMIT 50
    """).fetchall()
finally:
    conn.close()

if recent_posts:
    df_posts = pd.DataFrame([dict(r) for r in recent_posts])
    source_names = {
        "dcinside_bitcoin": "DC 비트코인",
        "dcinside_stock": "DC 주식",
        "ppomppu": "뽐뿌",
        "blind": "블라인드",
    }
    df_posts["source"] = df_posts["source"].map(source_names).fillna(df_posts["source"])

    # 점수에 따른 색상 표시
    def score_emoji(score):
        if score is None:
            return "⚪"
        if score >= 70:
            return f"🔴 {score:.0f}"
        elif score >= 50:
            return f"🟡 {score:.0f}"
        else:
            return f"🔵 {score:.0f}"

    df_posts["감성점수"] = df_posts["score"].apply(score_emoji)
    display_cols = ["source", "title", "comment_count", "감성점수", "published_at"]
    df_display = df_posts[display_cols].rename(columns={
        "source": "출처", "title": "제목", "comment_count": "댓글",
        "published_at": "작성시간",
    })
    st.dataframe(df_display, use_container_width=True, height=400)
else:
    st.info("수집된 게시글이 없습니다. `python main.py scrape` 명령어로 데이터를 수집하세요.")

# 푸터
st.divider()
st.markdown(
    "<div style='text-align:center; color:gray; padding:1rem'>"
    "🔬 인간지표 추적기 v1.0 | "
    "커뮤니티 여론은 투자 판단의 참고 자료일 뿐, 투자 결정은 본인의 책임입니다."
    "</div>",
    unsafe_allow_html=True,
)
