"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RSI 이동평균 교차 매매 신호 트래커  v3.0
  Streamlit 웹앱 버전 (모바일 최적화)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  실행:  streamlit run app.py
  배포:  Streamlit Community Cloud (무료)
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go

# ══════════════════════════════════════════════════════════════
#  페이지 설정 (반드시 첫 번째)
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="RSI 신호 트래커",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════
#  모바일 최적화 CSS
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* 전체 폰트·여백 */
html, body, [class*="css"] { font-size: 14px; }
.block-container { padding: 0.8rem 0.8rem 2rem; max-width: 100%; }

/* 신호 카드 공통 */
.sig-card {
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 10px;
    border-left: 5px solid;
}
.card-buy     { background:#0d2b1a; border-color:#22c55e; }
.card-sell    { background:#2b0d0d; border-color:#ef4444; }
.card-watch-l { background:#1a1700; border-color:#eab308; }
.card-watch-h { background:#1a0e00; border-color:#f97316; }
.card-normal  { background:#1a1f2e; border-color:#334155; }

/* 카드 내 텍스트 */
.card-title   { font-size:15px; font-weight:700; margin-bottom:4px; }
.card-row     { font-size:12px; color:#94a3b8; margin-top:3px; }
.card-signal  { font-size:13px; font-weight:600; margin-top:6px; }
.card-action  { font-size:13px; font-weight:700; margin-top:4px; }
.badge {
    display:inline-block;
    padding:2px 8px;
    border-radius:20px;
    font-size:11px;
    font-weight:600;
    margin-right:4px;
}
.b-buy    { background:#166534; color:#bbf7d0; }
.b-sell   { background:#7f1d1d; color:#fecaca; }
.b-watch  { background:#713f12; color:#fef08a; }
.b-normal { background:#1e293b; color:#94a3b8; }

/* 탭 크게 */
button[data-baseweb="tab"] { font-size:13px !important; padding:10px 14px !important; }

/* 메트릭 숫자 크게 */
[data-testid="metric-container"] { text-align:center; }
[data-testid="stMetricValue"]    { font-size:22px !important; }
[data-testid="stMetricDelta"]    { font-size:13px !important; }

/* 사이드바 */
[data-testid="stSidebar"] { min-width: 220px; }

/* 구분선 */
hr { margin: 0.5rem 0; border-color: #334155; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  종목 리스트 (이름, 기준티커, 롱ETF, 인버스ETF, 카테고리)
# ══════════════════════════════════════════════════════════════
PAIRS = [
    # 지수
    ("S&P 500",        "SPY",  "UPRO", "SPXS", "지수"),
    ("나스닥 100",      "QQQ",  "TQQQ", "SQQQ", "지수"),
    ("다우존스",        "DIA",  "UDOW", "SDOW", "지수"),
    ("러셀 2000",      "IWM",  "TNA",  "TZA",  "지수"),
    ("S&P400 중형주",  "MDY",  "MIDU", "MIDZ", "지수"),
    # 기술/반도체
    ("기술주 XLK",     "XLK",  "TECL", "TECS", "섹터"),
    ("반도체 SOXX",    "SOXX", "SOXL", "SOXS", "섹터"),
    ("반도체 SMH",     "SMH",  "SOXL", "SOXS", "섹터"),
    # 금융
    ("금융 XLF",       "XLF",  "FAS",  "FAZ",  "섹터"),
    ("지역은행 KRE",   "KRE",  "DPST", "KBWR", "섹터"),
    # 에너지
    ("에너지 XLE",     "XLE",  "ERX",  "ERY",  "섹터"),
    ("오일가스 XOP",   "XOP",  "GUSH", "DRIP", "섹터"),
    # 헬스케어/바이오
    ("바이오테크 XBI", "XBI",  "LABU", "LABD", "섹터"),
    ("바이오테크 IBB", "IBB",  "BIB",  "BIS",  "섹터"),
    ("헬스케어 XLV",   "XLV",  "CURE", "RXD",  "섹터"),
    # 기타 섹터
    ("금광주 GDX",     "GDX",  "NUGT", "DUST", "섹터"),
    ("주니어금광 GDXJ","GDXJ", "JNUG", "JDST", "섹터"),
    ("주택건설 XHB",   "XHB",  "NAIL", "CLAW", "섹터"),
    ("유틸리티 XLU",   "XLU",  "UTSL", "SDP",  "섹터"),
    ("산업재 XLI",     "XLI",  "DUSL", "SIJ",  "섹터"),
    ("소재 XLB",       "XLB",  "UYM",  "SMN",  "섹터"),
    ("소비재 XLY",     "XLY",  "WANT", "SCC",  "섹터"),
    ("필수소비재 XLP", "XLP",  "FTLS", "SZK",  "섹터"),
    ("통신서비스 XLC", "XLC",  "TELE", "QCOM", "섹터"),
    ("리츠 IYR",       "IYR",  "DRN",  "DRV",  "섹터"),
    # 채권
    ("20년국채 TLT",   "TLT",  "TMF",  "TMV",  "채권"),
    ("7-10년국채 IEF", "IEF",  "UST",  "PST",  "채권"),
    # 원자재
    ("금 GLD",         "GLD",  "UGL",  "GLL",  "원자재"),
    ("은 SLV",         "SLV",  "AGQ",  "ZSL",  "원자재"),
    ("원유 USO",       "USO",  "UCO",  "SCO",  "원자재"),
    ("천연가스 UNG",   "UNG",  "BOIL", "KOLD", "원자재"),
    # 해외
    ("중국 FXI",       "FXI",  "YINN", "YANG", "해외"),
    ("신흥국 EEM",     "EEM",  "EDC",  "EDZ",  "해외"),
    ("일본 EWJ",       "EWJ",  "EZJ",  "EWV",  "해외"),
    ("브라질 EWZ",     "EWZ",  "BRZU", "BZQ",  "해외"),
    # 크립토
    ("비트코인 IBIT",  "IBIT", "BITX", "BITI", "크립토"),
    ("코인베이스 COIN","COIN", "CONL", "MSVX", "크립토"),
    ("MicroStrategy",  "MSTR", "MSTX", "MSTZ", "크립토"),
    # 개별주
    ("NVIDIA",         "NVDA", "NVDL", "NVDS", "개별주"),
    ("Tesla",          "TSLA", "TSLL", "TSLS", "개별주"),
    ("Apple",          "AAPL", "AAPU", "AAPD", "개별주"),
    ("Amazon",         "AMZN", "AMZU", "AMZD", "개별주"),
    ("Microsoft",      "MSFT", "MSFU", "MSFD", "개별주"),
    ("Meta",           "META", "METU", "METD", "개별주"),
    ("Alphabet",       "GOOGL","GGLL", "GGLS", "개별주"),
    ("AMD",            "AMD",  "AMDL", "AMDS", "개별주"),
    ("Netflix",        "NFLX", "NFLX", "NFLX", "개별주"),
    ("Palantir",       "PLTR", "PLTU", "PLTD", "개별주"),
    ("Broadcom",       "AVGO", "AVGU", "AVGD", "개별주"),
    ("Eli Lilly",      "LLY",  "LLYL", "LLYS", "개별주"),
]

# ══════════════════════════════════════════════════════════════
#  파라미터
# ══════════════════════════════════════════════════════════════
RSI_PERIOD      = 14
RSI_MA_PERIOD   = 5
OVERSOLD        = 30
OVERBOUGHT      = 70
LOOKBACK        = 10
WEEKLY_DAYS     = 7
DATA_PERIOD     = "120d"

# ══════════════════════════════════════════════════════════════
#  계산 함수
# ══════════════════════════════════════════════════════════════

def calc_rsi(close: pd.Series) -> pd.Series:
    delta    = close.diff()
    gain     = delta.clip(lower=0)
    loss     = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=RSI_PERIOD - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=RSI_PERIOD - 1, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).round(2)


def detect_signal(rsi: pd.Series):
    """
    반환: (tag, signal_text, action_type)
    tag: 'buy' | 'sell' | 'watch_low' | 'watch_high' | 'normal'
    """
    ma = rsi.rolling(RSI_MA_PERIOD).mean()
    if ma.isna().all() or len(rsi) < LOOKBACK + 2:
        return "normal", "-", None

    cur_r, prev_r = float(rsi.iloc[-1]), float(rsi.iloc[-2])
    cur_m, prev_m = float(ma.iloc[-1]),  float(ma.iloc[-2])
    if np.isnan(cur_m) or np.isnan(prev_m):
        return "normal", "-", None

    window = rsi.iloc[-(LOOKBACK + 1):-1]
    oversold   = bool((window < OVERSOLD).any())
    overbought = bool((window > OVERBOUGHT).any())

    # 매수: 과매도 후 RSI가 RSI-MA 상향 교차
    if oversold and prev_r < prev_m and cur_r >= cur_m:
        return "buy", "🟢 매수 신호", "LONG"

    # 인버스: 과매수 후 RSI가 RSI-MA 하향 교차
    if overbought and prev_r > prev_m and cur_r <= cur_m:
        return "sell", "🔴 인버스 신호", "INVERSE"

    if cur_r < OVERSOLD:
        cross = "▲MA" if cur_r >= cur_m else "▼MA 대기"
        return "watch_low", f"⚠️ 과매도 ({cur_r:.1f}) {cross}", None

    if cur_r > OVERBOUGHT:
        cross = "▼MA" if cur_r <= cur_m else "▲MA 대기"
        return "watch_high", f"⚠️ 과매수 ({cur_r:.1f}) {cross}", None

    return "normal", "-", None


def _extract_close(raw: pd.DataFrame, ticker: str) -> pd.Series:
    """
    yfinance 버전에 관계없이 종가 Series를 안전하게 추출.
    최신 yfinance(0.2.x)는 단일 티커도 MultiIndex로 반환함.
    """
    if raw is None or raw.empty:
        return pd.Series(dtype=float)

    # MultiIndex: columns = [("Close","TICKER"), ("Open","TICKER"), ...]
    if isinstance(raw.columns, pd.MultiIndex):
        if "Close" in raw.columns.get_level_values(0):
            close = raw["Close"]
            # Close 레벨 아래 컬럼이 하나면 바로 Series로
            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]
            return close.dropna()
        return pd.Series(dtype=float)

    # 일반 Index
    if "Close" in raw.columns:
        return raw["Close"].dropna()

    return pd.Series(dtype=float)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_all_data():
    """전체 종목 데이터 수집 (1시간 캐시)"""
    results = []
    errors  = []

    for name, base, long_etf, inv_etf, cat in PAIRS:
        r = dict(
            name=name, base=base, long=long_etf, inv=inv_etf, cat=cat,
            rsi=None, rsi_ma=None, delta=None,
            weekly=[], signal="-", tag="normal", action="-",
            ok=False, err_msg=""
        )
        try:
            # ★ silent=True 제거 — yfinance에 없는 파라미터
            raw = yf.download(
                base, period=DATA_PERIOD, interval="1d",
                auto_adjust=True, progress=False
            )
            close = _extract_close(raw, base)

            if close.empty:
                r["err_msg"] = "데이터 없음"
                errors.append(f"{base}: 데이터 없음")
                results.append(r)
                continue

            if len(close) < RSI_PERIOD + RSI_MA_PERIOD + 5:
                r["err_msg"] = "데이터 부족"
                errors.append(f"{base}: 데이터 부족 ({len(close)}일)")
                results.append(r)
                continue

            rsi = calc_rsi(close)
            ma  = rsi.rolling(RSI_MA_PERIOD).mean()

            cur_rsi  = round(float(rsi.iloc[-1]), 1)
            cur_ma   = round(float(ma.iloc[-1]),  1)
            delta    = round(cur_rsi - float(rsi.iloc[-2]), 1)
            weekly   = [round(float(v), 1)
                        for v in rsi.iloc[-WEEKLY_DAYS:] if not np.isnan(v)]

            tag, signal, act_type = detect_signal(rsi)

            if act_type == "LONG":
                action = f"▶ {long_etf} 매수"
            elif act_type == "INVERSE":
                action = f"▶ {inv_etf} 매수"
            else:
                action = "-"

            r.update(rsi=cur_rsi, rsi_ma=cur_ma, delta=delta,
                     weekly=weekly, signal=signal, tag=tag, action=action, ok=True)

        except Exception as e:
            r["err_msg"] = str(e)[:60]
            errors.append(f"{base}: {str(e)[:60]}")

        results.append(r)

    # 오류 목록을 결과에 첨부 (디버깅용)
    return results, errors

# ══════════════════════════════════════════════════════════════
#  RSI 스파크라인 (Plotly)
# ══════════════════════════════════════════════════════════════

def sparkline(weekly: list, tag: str) -> go.Figure:
    color_map = {"buy":"#22c55e","sell":"#ef4444",
                 "watch_low":"#eab308","watch_high":"#f97316","normal":"#64748b"}
    color = color_map.get(tag, "#64748b")

    fig = go.Figure()
    x = list(range(len(weekly)))

    # 과매도/과매수 영역
    fig.add_hrect(y0=0,  y1=30, fillcolor="#22c55e", opacity=0.06, line_width=0)
    fig.add_hrect(y0=70, y1=100,fillcolor="#ef4444", opacity=0.06, line_width=0)
    fig.add_hline(y=30, line_dash="dot", line_color="#22c55e", line_width=0.8, opacity=0.5)
    fig.add_hline(y=70, line_dash="dot", line_color="#ef4444", line_width=0.8, opacity=0.5)
    fig.add_hline(y=50, line_dash="dot", line_color="#475569", line_width=0.5, opacity=0.3)

    fig.add_trace(go.Scatter(
        x=x, y=weekly, mode="lines+markers",
        line=dict(color=color, width=2),
        marker=dict(color=color, size=4),
        hovertemplate="%{y:.1f}<extra></extra>",
    ))
    fig.update_layout(
        height=90, margin=dict(l=0,r=0,t=0,b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(range=[max(0, min(weekly)-10), min(100, max(weekly)+10)],
                   showgrid=False, zeroline=False,
                   tickfont=dict(size=9, color="#64748b"), tickvals=[30,70]),
        showlegend=False,
    )
    return fig

# ══════════════════════════════════════════════════════════════
#  카드 HTML 렌더
# ══════════════════════════════════════════════════════════════

def card_class(tag):
    return {"buy":"card-buy","sell":"card-sell",
            "watch_low":"card-watch-l","watch_high":"card-watch-h"}.get(tag,"card-normal")

def badge_class(tag):
    return {"buy":"b-buy","sell":"b-sell",
            "watch_low":"b-watch","watch_high":"b-watch"}.get(tag,"b-normal")

def render_card(r):
    cc = card_class(r["tag"])
    bc = badge_class(r["tag"])
    delta_str = (f"▲ {r['delta']:.1f}" if r["delta"] and r["delta"] > 0
                 else (f"▼ {abs(r['delta']):.1f}" if r["delta"] and r["delta"] < 0 else "─"))
    action_html = (
        f'<div class="card-action" style="color:#22c55e">{r["action"]}</div>'
        if r["action"] != "-" else ""
    )
    html = f"""
    <div class="sig-card {cc}">
      <div class="card-title">
        <span class="badge {bc}">{r['cat']}</span>
        {r['name']}
        <span style="font-size:11px;color:#64748b;font-weight:400;margin-left:6px">{r['base']}</span>
      </div>
      <div class="card-row">롱 ETF: <b style="color:#e2e8f0">{r['long']}</b>
        &nbsp;|&nbsp; 인버스: <b style="color:#e2e8f0">{r['inv']}</b></div>
      <div class="card-row">RSI: <b style="color:#e2e8f0;font-size:15px">{r['rsi'] if r['rsi'] else '-'}</b>
        &nbsp; RSI-MA({RSI_MA_PERIOD}): <b style="color:#94a3b8">{r['rsi_ma'] if r['rsi_ma'] else '-'}</b>
        &nbsp; 변화: <b style="color:#e2e8f0">{delta_str}</b></div>
      <div class="card-signal">{r['signal']}</div>
      {action_html}
    </div>"""
    return html

# ══════════════════════════════════════════════════════════════
#  메인 UI
# ══════════════════════════════════════════════════════════════

def main():
    # ── 헤더 ─────────────────────────────────────────────────
    st.markdown("## 📊 RSI 매매 신호 트래커")
    st.caption(
        f"RSI {RSI_PERIOD}일  ·  RSI-MA {RSI_MA_PERIOD}일  ·  "
        f"과매도 ≤{OVERSOLD}  ·  과매수 ≥{OVERBOUGHT}  ·  감지 {LOOKBACK}거래일"
    )

    # ── 사이드바 (필터) ──────────────────────────────────────
    with st.sidebar:
        st.markdown("### ⚙️ 필터")
        sel_cats = st.multiselect(
            "카테고리",
            options=sorted(set(p[4] for p in PAIRS)),
            default=[],
            placeholder="전체 (비우면 전체)"
        )
        show_spark = st.toggle("RSI 스파크라인 표시", value=True)
        st.divider()
        st.markdown("### 📐 파라미터 안내")
        st.markdown(f"""
- RSI 기간: **{RSI_PERIOD}일**
- RSI-MA 기간: **{RSI_MA_PERIOD}일**
- 과매도 기준: **RSI ≤ {OVERSOLD}**
- 과매수 기준: **RSI ≥ {OVERBOUGHT}**
- 신호 감지: **최근 {LOOKBACK} 거래일**
- 캐시 유효: **1시간**
        """)
        st.divider()
        st.caption("⚠️ 투자 참고용입니다. 실제 매매 전 반드시 직접 확인하세요.")

    # ── 데이터 로딩 ──────────────────────────────────────────
    col_btn, col_time = st.columns([1, 3])
    with col_btn:
        if st.button("🔄 데이터 새로고침", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    with st.spinner("📡 50개 종목 데이터 수집 중... (첫 로딩은 약 30~60초)"):
        results, errors = fetch_all_data()

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    ok_count  = sum(1 for r in results if r["ok"])
    err_count = len(results) - ok_count

    with col_time:
        st.caption(
            f"마지막 업데이트: {now}  (1시간 캐시)  ·  "
            f"성공 {ok_count}건 / 실패 {err_count}건"
        )

    # 실패 종목이 있으면 expander로 보여줌
    if errors:
        with st.expander(f"⚠️ 데이터 로드 실패 {err_count}건 (클릭하여 확인)", expanded=False):
            for e in errors:
                st.caption(f"• {e}")
            st.caption("→ 해당 티커가 Yahoo Finance에서 지원되지 않거나 일시적 오류일 수 있습니다.")

    # 카테고리 필터 적용
    if sel_cats:
        results = [r for r in results if r["cat"] in sel_cats]

    # 신호 분류
    buys      = [r for r in results if r["tag"] == "buy"]
    sells     = [r for r in results if r["tag"] == "sell"]
    watch_low = [r for r in results if r["tag"] == "watch_low"]
    watch_hi  = [r for r in results if r["tag"] == "watch_high"]
    normals   = [r for r in results if r["tag"] == "normal"]

    # ── 요약 메트릭 ──────────────────────────────────────────
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("🟢 매수 신호",   len(buys))
    m2.metric("🔴 인버스 신호", len(sells))
    m3.metric("⚠️ 과매도 대기", len(watch_low))
    m4.metric("🟠 과매수 대기", len(watch_hi))
    m5.metric("총 종목",        len(results))

    st.divider()

    # ── 탭 ───────────────────────────────────────────────────
    tab_labels = [
        f"🟢 매수 신호 ({len(buys)})",
        f"🔴 인버스 ({len(sells)})",
        f"⚠️ 과매도 대기 ({len(watch_low)})",
        f"🟠 과매수 대기 ({len(watch_hi)})",
        f"전체 ({len(results)})",
    ]
    tabs = st.tabs(tab_labels)

    def render_section(items, tab, empty_msg="해당 신호 없음"):
        with tab:
            if not items:
                st.info(f"ℹ️ {empty_msg}")
                return

            for r in sorted(items, key=lambda x: x["rsi"] or 50):
                with st.container():
                    # 카드 + 스파크라인 2열
                    if show_spark and r.get("weekly") and len(r["weekly"]) >= 2:
                        c1, c2 = st.columns([3, 2])
                        with c1:
                            st.markdown(render_card(r), unsafe_allow_html=True)
                        with c2:
                            st.plotly_chart(
                                sparkline(r["weekly"], r["tag"]),
                                use_container_width=True,
                                config={"displayModeBar": False},
                            )
                    else:
                        st.markdown(render_card(r), unsafe_allow_html=True)

    render_section(buys,      tabs[0], "현재 매수 신호 없음")
    render_section(sells,     tabs[1], "현재 인버스 신호 없음")
    render_section(watch_low, tabs[2], "과매도 대기 종목 없음")
    render_section(watch_hi,  tabs[3], "과매수 대기 종목 없음")

    # 전체 탭
    with tabs[4]:
        all_sorted = (buys + sells + watch_low + watch_hi +
                      sorted(normals, key=lambda x: x["rsi"] or 50))
        if not all_sorted:
            st.info("데이터 없음")
        else:
            # 테이블 뷰
            rows = []
            for r in all_sorted:
                rows.append({
                    "카테고리": r["cat"],
                    "종목명":   r["name"],
                    "기준":     r["base"],
                    "롱 ETF":   r["long"],
                    "인버스":   r["inv"],
                    "현재 RSI": r["rsi"] or "-",
                    "RSI-MA":   r["rsi_ma"] or "-",
                    "신호":     r["signal"],
                    "추천":     r["action"],
                })
            df = pd.DataFrame(rows)

            def highlight(row):
                tag_map = {
                    "🟢 매수 신호":  "background-color:#0d2b1a;color:#22c55e",
                    "🔴 인버스 신호":"background-color:#2b0d0d;color:#ef4444",
                }
                sig = row["신호"]
                style = tag_map.get(sig, "")
                return [style] * len(row)

            st.dataframe(
                df.style.apply(highlight, axis=1),
                use_container_width=True,
                hide_index=True,
                height=min(600, 35 * len(df) + 38),
            )

    # ── 하단 안내 ─────────────────────────────────────────────
    st.divider()
    with st.expander("📖 신호 조건 설명"):
        st.markdown(f"""
**🟢 매수 신호**
- 최근 {LOOKBACK}거래일 이내 RSI가 **{OVERSOLD} 이하**에 진입
- **AND** RSI가 RSI의 {RSI_MA_PERIOD}일 이동평균선을 **상향 돌파**
- → 롱 ETF 매수 고려

**🔴 인버스 신호**
- 최근 {LOOKBACK}거래일 이내 RSI가 **{OVERBOUGHT} 이상**에 진입
- **AND** RSI가 RSI의 {RSI_MA_PERIOD}일 이동평균선을 **하향 돌파**
- → 인버스 ETF 매수 (현 주식 매도) 고려

**⚠️ 대기**
- 과매도/과매수 구간에 진입했으나 아직 교차 미발생
- 스파크라인에서 RSI 방향을 확인하세요

**데이터 출처**: Yahoo Finance (yfinance)  
**캐시**: 1시간 (새로고침 버튼으로 즉시 갱신 가능)  
⚠️ 본 앱은 **투자 참고용**이며 실제 투자 손익에 책임지지 않습니다.
        """)


if __name__ == "__main__":
    main()
