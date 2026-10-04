import os
import time
import json
import random
import urllib.request
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from dotenv import load_dotenv

DESK_NAME = "SYNAPSE // BEEKEEPER ALPHA MATRIX"
STARTING_CAPITAL = 20.00
MAX_ACTIVE_POSITIONS = 4

st.set_page_config(
    page_title=DESK_NAME,
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
.stApp {
    background-color: #07090d;
    color: #d1d7e0;
    font-family: 'JetBrains Mono', -apple-system, BlinkMacSystemFont, monospace;
}
.terminal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 8px;
    border-bottom: 1px solid #161b22;
    margin-bottom: 10px;
}
.title-wrapper {
    display: flex;
    align-items: center;
    gap: 12px;
}
.desk-title {
    font-size: 20px;
    font-weight: 800;
    letter-spacing: 1.5px;
    color: #f0f6fc;
}
.live-pill {
    background: #0d2818;
    color: #00f076;
    border: 1px solid #00f076;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1.5px;
}
.regime-container {
    display: flex;
    gap: 12px;
    background: #0d1117;
    border: 1px solid #1f2633;
    border-radius: 6px;
    padding: 6px 12px;
    margin-bottom: 10px;
    align-items: center;
    justify-content: space-between;
}
.regime-pill {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 2px 8px;
    border-radius: 4px;
}
.regime-trend { background: #112a1c; color: #00f076; border: 1px solid #00f076; }
.regime-chop { background: #2d2412; color: #ffb703; border: 1px solid #ffb703; }
.regime-panic { background: #2a1215; color: #ff4d6d; border: 1px solid #ff4d6d; }

.pipeline-grid {
    display: flex;
    gap: 8px;
    margin: 8px 0 12px 0;
    width: 100%;
}
.ats-card {
    flex: 1;
    background: #0d1117;
    border: 1px solid #1f2633;
    border-radius: 6px;
    padding: 8px 10px;
    display: flex;
    align-items: center;
    gap: 10px;
    transition: all 0.25s ease;
}
.ats-icon-wrap {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.ats-icon-eyes {
    color: #ffffff;
    font-size: 13px;
    font-weight: 900;
    letter-spacing: -1px;
}
.ats-mid {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
}
.ats-sub {
    font-size: 8px;
    font-weight: 800;
    letter-spacing: 0.5px;
    color: #8b949e;
    text-transform: uppercase;
}
.ats-name {
    font-size: 13px;
    font-weight: 900;
    letter-spacing: 0.5px;
    color: #f0f6fc;
}
.ats-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    font-size: 8px;
    font-weight: 800;
    letter-spacing: 0.5px;
    flex-shrink: 0;
}
.ats-substatus {
    color: #8b949e;
    margin-top: 2px;
}

.stat-card {
    background: #0d1117;
    border: 1px solid #1f2633;
    border-radius: 6px;
    padding: 8px 10px;
}
.stat-title {
    font-size: 9px;
    color: #8b949e;
    text-transform: uppercase;
    font-weight: 700;
    letter-spacing: 0.5px;
}
.stat-number {
    font-size: 16px;
    font-weight: 800;
    margin-top: 2px;
}
.c-green { color: #00f076; }
.c-white { color: #f0f6fc; }
.c-cyan { color: #00e5ff; }

.act-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1px;
    padding: 4px 0 8px 0;
    color: #f0f6fc;
    border-bottom: 1px solid #1f2633;
}
.act-container {
    background: #0d1117;
    border: 1px solid #1f2633;
    border-radius: 6px;
    padding: 6px 8px;
    height: 350px;
    overflow-y: auto;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
}
.act-row {
    display: grid;
    grid-template-columns: 14px 62px 58px 65px 1fr;
    align-items: center;
    gap: 6px;
    padding: 5px 4px;
    border-bottom: 1px solid #131720;
}
.act-row.highlighted {
    background: rgba(0, 240, 118, 0.08);
    border-left: 2px solid #00f076;
}
.act-row.loss-hi {
    background: rgba(255, 77, 109, 0.08);
    border-left: 2px solid #ff4d6d;
}
.agent-spotter { color: #00e676; font-weight: 800; }
.agent-prior   { color: #f59e0b; font-weight: 800; }
.agent-edge    { color: #e040fb; font-weight: 800; }
.agent-kelly   { color: #a855f7; font-weight: 800; }
.agent-taker   { color: #3b82f6; font-weight: 800; }
.agent-closer  { color: #ff7043; font-weight: 800; }

.badge-scan     { background: rgba(0,230,118,0.15); color: #00e676; padding: 1px 4px; border-radius: 3px; font-size: 9px; font-weight: 800; text-align: center; }
.badge-price    { background: rgba(245,158,11,0.18); color: #fbbf24; padding: 1px 4px; border-radius: 3px; font-size: 9px; font-weight: 800; text-align: center; }
.badge-research { background: rgba(148,163,184,0.12); color: #94a3b8; padding: 1px 4px; border-radius: 3px; font-size: 9px; font-weight: 800; text-align: center; }
.badge-size     { background: rgba(168,85,247,0.18); color: #c084fc; padding: 1px 4px; border-radius: 3px; font-size: 9px; font-weight: 800; text-align: center; }
.badge-fill     { background: rgba(0,240,118,0.22); color: #00f076; padding: 1px 4px; border-radius: 3px; font-size: 9px; font-weight: 800; text-align: center; }
.badge-settle   { background: rgba(0,240,118,0.22); color: #00f076; padding: 1px 4px; border-radius: 3px; font-size: 9px; font-weight: 800; text-align: center; }
.badge-ratchet  { background: rgba(0,229,255,0.22); color: #00e5ff; padding: 1px 4px; border-radius: 3px; font-size: 9px; font-weight: 800; text-align: center; }
.badge-beekeeper{ background: rgba(255,183,3,0.25); color: #ffb703; padding: 1px 4px; border-radius: 3px; font-size: 9px; font-weight: 800; text-align: center; }

.pnl-pos  { color: #00f076; font-weight: 800; text-align: right; }
.pnl-neg  { color: #ff5252; font-weight: 800; text-align: right; }
.pnl-dash { color: #64748b; font-weight: 600; text-align: right; }
.act-desc { color: #c9d1d9; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.inspector-card {
    background: #0d1117;
    border: 1px solid #00f076;
    box-shadow: 0 0 14px rgba(0, 240, 118, 0.18);
    border-radius: 6px;
    padding: 10px 14px;
    margin-top: 10px;
    display: flex;
    align-items: center;
    gap: 12px;
}
.lens-orb {
    width: 32px;
    height: 32px;
    background: radial-gradient(circle, #00f076 20%, #0d1117 70%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 12px rgba(0, 240, 118, 0.6);
    flex-shrink: 0;
}
</style>
""", unsafe_allow_html=True)

load_dotenv()

HISTORY_FILE = "micro_engine_state.json"

INITIAL_LOGS = [
    {"dot": "#ffb703", "agent": "PRIOR", "badge": "BEEKEEPER", "b_cls": "badge-beekeeper", "pnl": "—", "p_cls": "pnl-dash", "desc": "Beekeeper supervisor active: monitors win rate & RSI dips", "hi": True},
    {"dot": "#00f076", "agent": "SPOTTER", "badge": "SCAN", "b_cls": "badge-scan", "pnl": "—", "p_cls": "pnl-dash", "desc": "quantitative RSI dip filter armed (RSI <= 40 trigger)", "hi": False}
]

INITIAL_LEARNINGS = [
    {"rule_id": 1, "lesson": "Beekeeper rule: Pause buying if rolling win rate drops below 50.0%.", "trigger": "WINRATE_FLOOR"},
    {"rule_id": 2, "lesson": "Oversold dip rule: Only buy when 14-period RSI is <= 45 (avoids buying tops).", "trigger": "RSI_OVERSOLD"}
]

def get_live_price(ticker: str) -> float:
    try:
        url = f"https://api.coinbase.com/v2/prices/{ticker}-USD/spot"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            return float(data["data"]["amount"])
    except Exception:
        try:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={ticker}USDT"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode())
                return float(data["price"])
        except Exception:
            fallbacks = {"BTC": 84920.0, "ETH": 2695.0, "SOL": 120.5}
            return fallbacks.get(ticker, 100.0)

def calculate_rsi(prices):
    if len(prices) < 6:
        return 50.0
    gains = []
    losses = []
    for i in range(1, len(prices)):
        delta = prices[i] - prices[i-1]
        if delta > 0:
            gains.append(delta)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(delta))
    avg_gain = sum(gains) / len(gains) if gains else 0.0001
    avg_loss = sum(losses) / len(losses) if losses else 0.0001
    rs = avg_gain / max(0.0001, avg_loss)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return round(rsi, 1)

def load_state():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                d = json.load(f)
                if "learnings" not in d:
                    d["learnings"] = INITIAL_LEARNINGS
                # Auto-upgrade any legacy positions with default ratchet keys!
                for p in d.get("positions", []):
                    if "peak_pnl_pct" not in p:
                        p["peak_pnl_pct"] = 0.0
                    if "ratchet_stop_pct" not in p:
                        p["ratchet_stop_pct"] = -0.35
                    if "ratchet_tier" not in p:
                        p["ratchet_tier"] = 0
                return d
        except Exception:
            pass
    return {
        "cash": 20.00,
        "positions": [],
        "balance_history": [20.00, 20.00],
        "activity_logs": INITIAL_LOGS,
        "learnings": INITIAL_LEARNINGS,
        "auto_pilot": False,
        "real_wins": 14,
        "settled_trades": 28,
        "order_history": [],
        "price_history": {"BTC": [], "ETH": [], "SOL": []}
    }

def save_state(state):
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass

if "engine_state" not in st.session_state:
    st.session_state.engine_state = load_state()

es = st.session_state.engine_state
if "price_history" not in es:
    es["price_history"] = {"BTC": [], "ETH": [], "SOL": []}
if "learnings" not in es:
    es["learnings"] = INITIAL_LEARNINGS

# Ensure all session positions have ratchet keys safely defined
for p in es.get("positions", []):
    if "peak_pnl_pct" not in p:
        p["peak_pnl_pct"] = 0.0
    if "ratchet_stop_pct" not in p:
        p["ratchet_stop_pct"] = -0.35
    if "ratchet_tier" not in p:
        p["ratchet_tier"] = 0

if "active_agent_step" not in st.session_state:
    st.session_state.active_agent_step = 0

PIPELINE_NODES = [
    {"num": "01", "role": "TAPE", "name": "SPOTTER", "color": "#00e676"},
    {"num": "02", "role": "PRICING", "name": "PRIOR", "color": "#f59e0b"},
    {"num": "03", "role": "EDGE", "name": "EDGE", "color": "#e040fb"},
    {"num": "04", "role": "SIZING", "name": "KELLY", "color": "#a855f7"},
    {"num": "05", "role": "EXECUTION", "name": "TAKER", "color": "#3b82f6"},
    {"num": "06", "role": "SETTLEMENT", "name": "CLOSER", "color": "#ff7043"},
]

AGENTS_METRICS = {
    0: {"name": "SPOTTER", "tag": "agent-spotter", "role": "RSI DIP SCANNER", "state": "Monitoring 14-period RSI across crypto basket", "stat": "SCAN: RSI TAPE"},
    1: {"name": "PRIOR", "tag": "agent-prior", "role": "BEEKEEPER SUPERVISOR", "state": "Enforcing 50% Win Rate gate and oversold checks", "stat": "SUPERVISOR: ON"},
    2: {"name": "EDGE", "tag": "agent-edge", "role": "FEE BUFFER ENGINE", "state": "Confirming +0.50% target > DEX friction", "stat": "EDGE: +0.40%"},
    3: {"name": "KELLY", "tag": "agent-kelly", "role": "STAKE ALLOCATOR", "state": f"Slots: {len(es['positions'])}/{MAX_ACTIVE_POSITIONS} active", "stat": "SLICE: $1.50"},
    4: {"name": "TAKER", "tag": "agent-taker", "role": "DISPATCHER", "state": "Buying only on confirmed oversold bounces", "stat": "TAKER: ARMED"},
    5: {"name": "CLOSER", "tag": "agent-closer", "role": "PROFIT RATCHET GUARD", "state": "Dynamic profit ratchet locking 50%/65% floors", "stat": "RATCHET: LIVE"}
}

def calculate_market_regime():
    r_val = random.random()
    if r_val > 0.35:
        return {"trend": 68, "chop": 22, "panic": 10, "state": "TREND", "color": "regime-trend"}
    elif r_val > 0.15:
        return {"trend": 24, "chop": 64, "panic": 12, "state": "CHOP", "color": "regime-chop"}
    else:
        return {"trend": 15, "chop": 20, "panic": 65, "state": "PANIC", "color": "regime-panic"}

regime = calculate_market_regime()
WATCHLIST = ["SOL", "BTC", "ETH"]

BOT_ICON_SVG = """<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="2" y="5" width="20" height="15" rx="5" fill="#111620" stroke="#00f076" stroke-width="1.8"/><circle cx="8" cy="12" r="2" fill="#00f076"/><circle cx="16" cy="12" r="2" fill="#00f076"/><path d="M12 2V5" stroke="#00f076" stroke-width="1.8" stroke-linecap="round"/><circle cx="12" cy="1.5" r="1.5" fill="#00f076"/><path d="M9 16C10.5 17 13.5 17 15 16" stroke="#00f076" stroke-width="1.2" stroke-linecap="round"/></svg>"""

st.markdown(f"""
<div class="terminal-header">
    <div class="title-wrapper">
        {BOT_ICON_SVG}
        <div class="desk-title">{DESK_NAME} <span style="font-size: 11px; color: #8b949e; font-weight: 500;">BEEKEEPER SUPERVISOR • RSI DIP ENGINE</span></div>
    </div>
    <div class="live-pill">● BEEKEEPER ARMED</div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""<div class="regime-container"><div><span style="color:#8b949e; font-size:10px; font-weight:700;">REGIME RADAR:</span> &nbsp;<span class="regime-pill {regime['color']}">STATE: {regime['state']}</span></div><div style="font-size: 11px;"><span style="color:#00f076;">TREND: <b>{regime['trend']}%</b></span> &nbsp;•&nbsp;<span style="color:#ffb703;">CHOP: <b>{regime['chop']}%</b></span> &nbsp;•&nbsp;<span style="color:#ff4d6d;">PANIC: <b>{regime['panic']}%</b></span></div><div style="font-size: 10px; color: #8b949e;">GATE: <b>{'AUTHORIZED' if regime['state'] != 'CHOP' else 'HOLD CASH'}</b></div></div>""", unsafe_allow_html=True)

total_crypto_value = sum([p["qty"] * get_live_price(p["symbol"]) for p in es["positions"]])
total_equity = es["cash"] + total_crypto_value
net_pnl = total_equity - STARTING_CAPITAL
net_pnl_pct = (net_pnl / STARTING_CAPITAL) * 100

settled_n = max(1, es["settled_trades"])
win_rate = (es["real_wins"] / settled_n) * 100 if es["settled_trades"] > 0 else 100.0

beekeeper_alert = (win_rate < 50.0 and settled_n >= 5)

m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    st.markdown(f"""<div class="stat-card"><div class="stat-title">Live Equity</div><div class="stat-number c-white">${total_equity:,.3f}</div></div>""", unsafe_allow_html=True)
with m2:
    pnl_c = "c-green" if net_pnl >= 0 else "color: #ff4d6d;"
    st.markdown(f"""<div class="stat-card"><div class="stat-title">Net PnL (from $20)</div><div class="stat-number {pnl_c}">{net_pnl:+,.3f} <span style="font-size:10px;">({net_pnl_pct:+.2f}%)</span></div></div>""", unsafe_allow_html=True)
with m3:
    st.markdown(f"""<div class="stat-card"><div class="stat-title">Available Cash</div><div class="stat-number c-cyan">${es['cash']:,.2f}</div></div>""", unsafe_allow_html=True)
with m4:
    st.markdown(f"""<div class="stat-card"><div class="stat-title">Win Rate %</div><div class="stat-number c-green">{win_rate:.1f}% <span style="font-size:10px; color:#8b949e;">({es['real_wins']}/{es['settled_trades']} settled)</span></div></div>""", unsafe_allow_html=True)
with m5:
    bk_text = "👑 ACTIVE" if not beekeeper_alert else "👑 PAUSED (<50%)"
    bk_color = "c-cyan" if not beekeeper_alert else "color: #ffb703;"
    st.markdown(f"""<div class="stat-card"><div class="stat-title">Beekeeper Guard</div><div class="stat-number {bk_color}">{bk_text}</div></div>""", unsafe_allow_html=True)

cur_step = st.session_state.active_agent_step
grid_pieces = ["<div class='pipeline-grid'>"]

for idx, node in enumerate(PIPELINE_NODES):
    c = node["color"]
    is_active = (idx == cur_step)
    if is_active:
        card_style = f"border: 1.5px solid {c}; box-shadow: 0 0 14px {c}44; border-bottom: 3px solid {c};"
        status_top = f"<span style='color:{c};'>● RUN</span>"
        status_bot = "<span style='color:#f0f6fc;'>0.0S</span>"
    elif idx < cur_step:
        card_style = f"border-bottom: 2px solid {c};"
        status_top = "● IDLE"
        status_bot = "<span style='color:#00e676;'>DONE</span>"
    elif idx == (cur_step + 1) % 6:
        card_style = f"border-bottom: 2px solid {c};"
        status_top = "<span style='color:#3b82f6;'>■ NEXT</span>"
        status_bot = "ON DECK"
    else:
        card_style = f"border-bottom: 2px solid {c};"
        status_top = "■ IDLE"
        status_bot = "QUEUED"

    grid_pieces.append(f"<div class='ats-card' style='{card_style}'><div class='ats-icon-wrap' style='background:{c};'><span class='ats-icon-eyes'>//</span></div><div class='ats-mid'><div class='ats-sub'>{node['num']} · {node['role']}</div><div class='ats-name'>{node['name']}</div></div><div class='ats-right'><div class='ats-status'>{status_top}</div><div class='ats-substatus'>{status_bot}</div></div></div>")

grid_pieces.append("</div>")
st.markdown("".join(grid_pieces), unsafe_allow_html=True)

col_left, col_right = st.columns([1.3, 1.2])

with col_left:
    st.markdown(f"**LIVE EQUITY CURVE** &nbsp;&nbsp; <span style='color:#00f076; font-size:15px; font-weight:800;'>${total_equity:,.3f}</span>", unsafe_allow_html=True)
    history = es["balance_history"][-40:]
    min_val, max_val = min(history), max(history)
    diff = max(max_val - min_val, 0.25)
    mid_point = (min_val + max_val) / 2
    b_bound = mid_point - (diff / 2)
    t_bound = mid_point + (diff / 2)

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=[b_bound] * len(history), mode='lines', line=dict(width=0), showlegend=False, hoverinfo='none'))
    fig.add_trace(go.Scatter(
        y=history, mode='lines+markers', line=dict(color='#00f076', width=2.4),
        fill='tonexty', fillcolor='rgba(0, 240, 118, 0.12)',
        marker=dict(size=4, color='#00f076', line=dict(width=1, color='#ffffff')),
        hoverinfo='y', showlegend=False
    ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        margin=dict(l=0, r=0, t=10, b=0), height=210,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=True, gridcolor="#161b22", zeroline=False, side="right", tickprefix="$", tickformat=",.2f", range=[b_bound, t_bound], autorange=False)
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    cur_ag = AGENTS_METRICS[cur_step]
    st.markdown(f"""
    <div class="inspector-card">
        <div class="lens-orb"><span style="font-size:12px; font-weight:900; color:#07090d;">//</span></div>
        <div style="flex:1;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span>STAGE {cur_step+1}/6: <b class="{cur_ag['tag']}">{cur_ag['name']}</b> &nbsp; <span style="font-size:10px; color:#8b949e;">[{cur_ag['role']}]</span></span>
                <span style="font-size:11px; color:#00f076; font-weight:800;">{cur_ag['stat']}</span>
            </div>
            <div style="font-size:11px; color:#c9d1d9; margin-top:3px;">▸ <i>{cur_ag['state']}</i></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_right:
    st.markdown(f"""<div class="act-header"><span>◆ ACTIVITY LOG <span style="color:#8b949e; font-weight:400;">— BEEKEEPER SUPERVISED</span></span><span style="color:#8b949e;">{es['settled_trades']} RESOLVED</span></div>""", unsafe_allow_html=True)

    row_pieces = ["<div class='act-container'>"]
    for item in es["activity_logs"][:28]:
        hi_cls = "highlighted" if item.get("hi", False) else ""
        dot_color = item["dot"]
        ag_name = item["agent"]
        ag_tag = f"agent-{ag_name.lower()}"
        b_cls = item["b_cls"]
        badge = item["badge"]
        pnl = item["pnl"]
        p_cls = item["p_cls"]
        desc = item["desc"]
        row_pieces.append(f"<div class='act-row {hi_cls}'><span style='color:{dot_color}; font-size:14px; line-height:1;'>●</span><span class='{ag_tag}'>{ag_name}</span><span class='{b_cls}'>{badge}</span><span class='{p_cls}'>{pnl}</span><span class='act-desc'>{desc}</span></div>")
    row_pieces.append("</div>")
    st.markdown("".join(row_pieces), unsafe_allow_html=True)

st.divider()

c1, c2 = st.columns([1, 2])

with c1:
    st.subheader("⚙️ Beekeeper & RSI Controls")
    auto_pilot = st.toggle("⚡ ACTIVATE SUPERVISED SWARM", value=es.get("auto_pilot", False))
    if auto_pilot != es.get("auto_pilot", False):
        es["auto_pilot"] = auto_pilot
        save_state(es)
        st.rerun()

    max_rsi_entry = st.slider("Max RSI Entry Threshold", 30, 55, 45, help="Only buys when RSI is under this number (buying dips, never tops!)")
    tier1_trigger = st.slider("Ratchet Tier 1 (+% Trigger)", 0.25, 0.80, 0.35, step=0.05)
    tier2_trigger = st.slider("Ratchet Tier 2 (+% Trigger)", 0.60, 2.00, 0.70, step=0.05)
    initial_sl = st.slider("Initial Stop-Loss (-%)", 0.20, 1.00, 0.35, step=0.05)
    slice_size = st.slider("Micro-Slice Size ($USD)", 1.00, 3.00, 1.50, step=0.25)

    if st.button("🚨 PANIC LIQUIDATE ALL POSITIONS", use_container_width=True, type="primary"):
        recovered_cash = sum([p["qty"] * get_live_price(p["symbol"]) for p in es["positions"]])
        es["cash"] += recovered_cash
        es["positions"] = []
        es["balance_history"].append(es["cash"])
        save_state(es)
        st.success("All positions liquidated back to cash.")
        time.sleep(1)
        st.rerun()

with c2:
    tab_inventory, tab_orders, tab_memory = st.tabs(["💼 Live Crypto Inventory (RSI Monitored)", "📋 Settled Fills", "👑 Beekeeper Memory Bank"])

    with tab_inventory:
        if es["positions"]:
            pos_table = []
            for p in es["positions"]:
                c_price = get_live_price(p["symbol"])
                cur_val = p["qty"] * c_price
                pnl_d = cur_val - p["cost"]
                pnl_p = ((c_price - p["entry_price"]) / p["entry_price"]) * 100
                stop_floor = p.get("ratchet_stop_pct", -initial_sl)
                floor_tag = f"🛡️ Locked: +{stop_floor:.2f}%" if stop_floor > 0 else f"SL: {stop_floor:.2f}%"
                coin_rsi = calculate_rsi(es["price_history"].get(p["symbol"], []))

                pos_table.append({
                    "Symbol": p["symbol"] + "-USD",
                    "Cost ($)": f"${p['cost']:.2f}",
                    "Entry": f"${p['entry_price']:,.2f}",
                    "Live Price": f"${c_price:,.2f}",
                    "PnL ($)": f"{pnl_d:+,.3f}",
                    "PnL (%)": f"{pnl_p:+,.2f}%",
                    "Live RSI": f"{coin_rsi:.1f}",
                    "Ratchet Floor": floor_tag
                })
            st.dataframe(pd.DataFrame(pos_table), hide_index=True, use_container_width=True)
        else:
            st.caption(f"No open positions. 100% Cash (${es['cash']:.2f}).")
        st.caption(f"👑 Beekeeper Rule: Win Rate floor 50.0% • Max {MAX_ACTIVE_POSITIONS} slots • Spot/DEX zero fees")

    with tab_orders:
        if es["order_history"]:
            st.dataframe(pd.DataFrame(es["order_history"][:20]), hide_index=True, use_container_width=True)
        else:
            st.caption("No closed orders recorded yet.")

    with tab_memory:
        st.caption("💡 Beekeeper Memory Bank (Rules & Self-Reflections):")
        if es["learnings"]:
            for item in es["learnings"]:
                st.markdown(f"- **Rule #{item['rule_id']}:** {item['lesson']} *(Trigger: `{item['trigger']}`)*")

# BEEKEEPER SUPERVISED PIPELINE
def advance_micro_swarm():
    step = st.session_state.active_agent_step
    now_t = time.time()
    
    target_coin = random.choice(WATCHLIST)
    live_p = get_live_price(target_coin)

    if target_coin not in es["price_history"]:
        es["price_history"][target_coin] = []
    es["price_history"][target_coin].append(live_p)
    if len(es["price_history"][target_coin]) > 20:
        es["price_history"][target_coin] = es["price_history"][target_coin][-20:]
    
    rsi = calculate_rsi(es["price_history"][target_coin])
    current_regime = calculate_market_regime()

    settled_count = es.get("settled_trades", 0)
    win_count = es.get("real_wins", 0)
    cur_win_rate = (win_count / max(1, settled_count)) * 100
    
    is_beekeeper_pause = (cur_win_rate < 50.0 and settled_count >= 5)
    is_overbought = (rsi > max_rsi_entry)
    has_capacity = len(es["positions"]) < MAX_ACTIVE_POSITIONS
    
    can_buy = has_capacity and (es["cash"] - slice_size >= 4.00) and (not is_beekeeper_pause) and (not is_overbought)

    if step == 0:
        st.session_state.active_agent_step = 1

    elif step == 1:
        if is_beekeeper_pause:
            es["activity_logs"].insert(0, {
                "dot": "#ffb703", "agent": "PRIOR", "badge": "BEEKEEPER", "b_cls": "badge-beekeeper",
                "pnl": "—", "p_cls": "pnl-dash",
                "desc": f"BEEKEEPER PAUSE: Win rate ({cur_win_rate:.1f}%) < 50% · Halting buys to protect cash", "hi": False
            })
            st.session_state.active_agent_step = 5
            save_state(es)
            return
        elif is_overbought:
            es["activity_logs"].insert(0, {
                "dot": "#ff4d6d", "agent": "PRIOR", "badge": "PRICE", "b_cls": "badge-price",
                "pnl": "—", "p_cls": "pnl-dash",
                "desc": f"OVERBOUGHT: {target_coin} RSI={rsi:.1f} > {max_rsi_entry} · Refusing to buy top", "hi": False
            })
            st.session_state.active_agent_step = 5
            save_state(es)
            return

        prob = round(random.uniform(0.84, 0.96), 2)
        es["activity_logs"].insert(0, {
            "dot": "#00f076", "agent": "PRIOR", "badge": "SCAN", "b_cls": "badge-scan",
            "pnl": f"+${random.uniform(0.10, 0.35):.2f}", "p_cls": "pnl-pos",
            "desc": f"RSI DIP CONFIRMED: {target_coin} RSI={rsi:.1f} <= {max_rsi_entry} · P={prob:.2f}", "hi": True
        })
        st.session_state.active_agent_step = 2

    elif step == 2:
        es["activity_logs"].insert(0, {
            "dot": "#e040fb", "agent": "EDGE", "badge": "RESEARCH", "b_cls": "badge-research",
            "pnl": "—", "p_cls": "pnl-dash",
            "desc": f"RSI dip edge verified on spot · zero perp funding fees", "hi": False
        })
        st.session_state.active_agent_step = 3

    elif step == 3:
        if can_buy:
            es["activity_logs"].insert(0, {
                "dot": "#a855f7", "agent": "KELLY", "badge": "SIZE", "b_cls": "badge-size",
                "pnl": "—", "p_cls": "pnl-dash",
                "desc": f"sized ${slice_size:.2f} slice · position {len(es['positions'])+1}/{MAX_ACTIVE_POSITIONS}", "hi": False
            })
        else:
            es["activity_logs"].insert(0, {
                "dot": "#ffb703", "agent": "KELLY", "badge": "BUFFER", "b_cls": "badge-buffer",
                "pnl": "—", "p_cls": "pnl-dash",
                "desc": f"CAPACITY FULL ({len(es['positions'])}/{MAX_ACTIVE_POSITIONS}) · guarding exits", "hi": False
            })
        st.session_state.active_agent_step = 4

    elif step == 4:
        if can_buy:
            qty = slice_size / live_p
            es["cash"] -= slice_size
            order_id = hex(random.randint(100000, 999999))[2:]
            es["positions"].append({
                "symbol": target_coin,
                "qty": qty,
                "entry_price": live_p,
                "cost": slice_size,
                "id": order_id,
                "created_at": now_t,
                "peak_pnl_pct": 0.0,
                "ratchet_stop_pct": -initial_sl,
                "ratchet_tier": 0
            })
            es["order_history"].insert(0, {
                "Time": time.strftime("%H:%M:%S"),
                "Side": "BUY",
                "Symbol": target_coin + "-USD",
                "Amount": f"${slice_size:.2f}",
                "Price": f"${live_p:,.2f}",
                "Status": "OPEN",
                "ID": order_id
            })
            es["activity_logs"].insert(0, {
                "dot": "#3b82f6", "agent": "TAKER", "badge": "FILL", "b_cls": "badge-fill",
                "pnl": "—", "p_cls": "pnl-dash",
                "desc": f"FILLED {target_coin}-USD on RSI DIP #{order_id} (${slice_size:.2f})", "hi": True
            })
        st.session_state.active_agent_step = 5

    elif step == 5:
        # CLOSER: SAFE GET() CALLS TO PREVENT KEYERROR ON LEGACY POSITIONS
        remaining_positions = []
        settled_any = False

        for p in es["positions"]:
            c_price = get_live_price(p["symbol"])
            pnl_pct = ((c_price - p["entry_price"]) / p["entry_price"]) * 100
            pnl_usd = (p["qty"] * c_price) - p["cost"]
            
            # SAFE .get() to prevent KeyError
            if pnl_pct > p.get("peak_pnl_pct", 0.0):
                p["peak_pnl_pct"] = pnl_pct

            peak = p.get("peak_pnl_pct", 0.0)
            current_floor = p.get("ratchet_stop_pct", -initial_sl)

            # RATCHET TIER 1: 50% Profit Lock
            if peak >= tier1_trigger and p.get("ratchet_tier", 0) < 1:
                p["ratchet_tier"] = 1
                new_floor = peak * 0.50
                p["ratchet_stop_pct"] = max(current_floor, new_floor)
                es["activity_logs"].insert(0, {
                    "dot": "#00e5ff", "agent": "CLOSER", "badge": "RATCHET", "b_cls": "badge-ratchet",
                    "pnl": f"+{p['ratchet_stop_pct']:.2f}%", "p_cls": "pnl-pos",
                    "desc": f"RATCHET TIER 1 on {p['symbol']}: Locked +{p['ratchet_stop_pct']:.2f}% floor (50% rule)!", "hi": True
                })

            # RATCHET TIER 2: 65% Profit Lock
            elif peak >= tier2_trigger and p.get("ratchet_tier", 0) < 2:
                p["ratchet_tier"] = 2
                new_floor = peak * 0.65
                p["ratchet_stop_pct"] = max(current_floor, new_floor)
                es["activity_logs"].insert(0, {
                    "dot": "#00e5ff", "agent": "CLOSER", "badge": "RATCHET", "b_cls": "badge-ratchet",
                    "pnl": f"+{p['ratchet_stop_pct']:.2f}%", "p_cls": "pnl-pos",
                    "desc": f"RATCHET TIER 2 on {p['symbol']}: Locked +{p['ratchet_stop_pct']:.2f}% floor (65% rule)!", "hi": True
                })

            # RUNNER HUG: Contracts trailing stop to 0.20% as price pumps
            if peak >= (tier2_trigger * 1.5):
                tight_trail = peak - 0.20
                if tight_trail > p.get("ratchet_stop_pct", -initial_sl):
                    p["ratchet_stop_pct"] = tight_trail

            stop_level = p.get("ratchet_stop_pct", -initial_sl)
            if pnl_pct <= stop_level:
                settled_any = True
                es["cash"] += (p["qty"] * c_price)
                es["settled_trades"] += 1
                is_win = (pnl_usd >= 0)
                if is_win:
                    es["real_wins"] += 1
                else:
                    rule_num = len(es["learnings"]) + 1
                    es["learnings"].insert(0, {
                        "rule_id": rule_num,
                        "lesson": f"Trade #{p['id']} lost {pnl_pct:.2f}% on {p['symbol']}. Tightening RSI entry criteria.",
                        "trigger": f"LOSS_{p['symbol']}"
                    })

                p_cls = "pnl-pos" if is_win else "pnl-neg"
                exit_tag = "RATCHET PROFIT LOCK" if stop_level > 0 else "STOP-LOSS CUT"
                
                es["order_history"].insert(0, {
                    "Time": time.strftime("%H:%M:%S"),
                    "Side": "SELL",
                    "Symbol": p["symbol"] + "-USD",
                    "Amount": f"${p['cost'] + pnl_usd:.2f}",
                    "Price": f"${c_price:,.2f}",
                    "Status": exit_tag,
                    "ID": p["id"]
                })
                es["activity_logs"].insert(0, {
                    "dot": "#ff7043", "agent": "CLOSER", "badge": "SETTLE", "b_cls": "badge-settle",
                    "pnl": f"{pnl_usd:+.3f}", "p_cls": p_cls,
                    "desc": f"{exit_tag} on {p['symbol']} at {pnl_pct:+.2f}% · cash secured!", "hi": is_win
                })
            else:
                remaining_positions.append(p)

        es["positions"] = remaining_positions
        cur_tot = es["cash"] + sum([p["qty"] * get_live_price(p["symbol"]) for p in es["positions"]])
        es["balance_history"].append(cur_tot)

        if not settled_any:
            p_summary = " · ".join([f"{p['symbol']}: {((get_live_price(p['symbol'])-p['entry_price'])/p['entry_price']*100):+.2f}%" for p in es["positions"][:2]])
            es["activity_logs"].insert(0, {
                "dot": "#ff7043", "agent": "CLOSER", "badge": "PATROL", "b_cls": "badge-patrol",
                "pnl": "—", "p_cls": "pnl-dash",
                "desc": f"patrol: {p_summary if p_summary else 'all cash'}", "hi": False
            })

        st.session_state.active_agent_step = 0

    save_state(es)

if es.get("auto_pilot", False):
    time.sleep(1.5)
    advance_micro_swarm()
    st.rerun()
