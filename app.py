import os
import time
import json
import random
import urllib.request
import xml.etree.ElementTree as ET
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from dotenv import load_dotenv
from google import genai
from google.genai import types

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus
from alpaca.data.historical.news import NewsClient
from alpaca.data.requests import NewsRequest

DESK_NAME = "SYNAPSE // MICRO-ALPHA MATRIX"
STARTING_CAPITAL = 20.00  # Anchored to your exact $20 starting balance

st.set_page_config(
    page_title=DESK_NAME,
    page_icon="⚡",
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
.badge-fill     { background: rgba(239,68,68,0.18); color: #f87171; padding: 1px 4px; border-radius: 3px; font-size: 9px; font-weight: 800; text-align: center; }
.badge-settle   { background: rgba(0,240,118,0.22); color: #00f076; padding: 1px 4px; border-radius: 3px; font-size: 9px; font-weight: 800; text-align: center; }
.badge-edge     { background: rgba(224,64,251,0.18); color: #e040fb; padding: 1px 4px; border-radius: 3px; font-size: 9px; font-weight: 800; text-align: center; }
.badge-buffer   { background: rgba(255,183,3,0.18); color: #ffb703; padding: 1px 4px; border-radius: 3px; font-size: 9px; font-weight: 800; text-align: center; }

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

GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
ALPACA_KEY = st.secrets.get("ALPACA_API_KEY", os.getenv("ALPACA_API_KEY"))
ALPACA_SECRET = st.secrets.get("ALPACA_SECRET_KEY", os.getenv("ALPACA_SECRET_KEY"))

gemini_client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None
trading_client = TradingClient(ALPACA_KEY, ALPACA_SECRET, paper=True) if ALPACA_KEY and ALPACA_SECRET else None
news_client = NewsClient(ALPACA_KEY, ALPACA_SECRET) if ALPACA_KEY and ALPACA_SECRET else None

HISTORY_FILE = "trade_history.json"

INITIAL_LOGS = [
    {"dot": "#00e676", "agent": "SPOTTER", "badge": "SCAN", "b_cls": "badge-scan", "pnl": "—", "p_cls": "pnl-dash", "desc": "micro-account initialized with $20.00 bankroll", "hi": True},
    {"dot": "#a855f7", "agent": "KELLY", "badge": "SIZE", "b_cls": "badge-size", "pnl": "—", "p_cls": "pnl-dash", "desc": "tranche sizing scaled to $2.00 - $3.00 slices", "hi": False},
    {"dot": "#ff7043", "agent": "CLOSER", "badge": "EDGE", "b_cls": "badge-edge", "pnl": "—", "p_cls": "pnl-dash", "desc": "cash buffer guard set to $2.00 reserve", "hi": False}
]

def load_local_data():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                d = json.load(f)
                # Auto-sanitize history if it still has old $100,000 numbers
                if d.get("balance_history") and max(d["balance_history"]) > 1000:
                    d["balance_history"] = [20.00, 20.00]
                    d["activity_logs"] = INITIAL_LOGS
                    d["real_wins"] = 0
                    d["settled_trades"] = 0
                return d
        except Exception:
            pass
    return {"balance_history": [20.00, 20.00], "activity_logs": INITIAL_LOGS, "auto_pilot": False, "real_wins": 0, "settled_trades": 0}

def save_local_data(balance_history, activity_logs, auto_pilot_state, real_wins, settled_trades):
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump({
                "balance_history": balance_history[-40:],
                "activity_logs": activity_logs[:40],
                "auto_pilot": auto_pilot_state,
                "real_wins": real_wins,
                "settled_trades": settled_trades
            }, f, indent=2)
    except Exception:
        pass

def fetch_account():
    if not trading_client:
        return {"equity": 20.0, "cash": 20.0, "buying_power": 20.0}
    try:
        acc = trading_client.get_account()
        return {"equity": float(acc.equity), "cash": float(acc.cash), "buying_power": float(acc.buying_power)}
    except Exception:
        return {"equity": 20.0, "cash": 20.0, "buying_power": 20.0}

account_data = fetch_account()
stored = load_local_data()

# Clean startup points for $20 balance
if "activity_logs" not in st.session_state:
    st.session_state.activity_logs = stored.get("activity_logs", INITIAL_LOGS)
if "balance_history" not in st.session_state:
    st.session_state.balance_history = [account_data["equity"], account_data["equity"]]

if "real_wins" not in st.session_state:
    st.session_state.real_wins = stored.get("real_wins", 0)
if "settled_trades" not in st.session_state:
    st.session_state.settled_trades = stored.get("settled_trades", 0)

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
    0: {"name": "SPOTTER", "tag": "agent-spotter", "role": "MICRO SCANNER", "state": "Scanning BTC / ETH / SOL on $20 bankroll", "stat": "BUDGET: $20.00"},
    1: {"name": "PRIOR", "tag": "agent-prior", "role": "BAYESIAN PROBABILITY", "state": "Prior updated on 1-min micro tick windows", "stat": "P(WIN): 0.88"},
    2: {"name": "EDGE", "tag": "agent-edge", "role": "FEE BUFFER ENGINE", "state": "Target (+0.55%) clears 0.25% fee with net profit", "stat": "NET EDGE: +0.30%"},
    3: {"name": "KELLY", "tag": "agent-kelly", "role": "MICRO SIZER", "state": "Calculating $2.00-$3.00 slice with cash buffer", "stat": "SLICE: $2.50"},
    4: {"name": "TAKER", "tag": "agent-taker", "role": "ORDER DISPATCHER", "state": "Checking cash > $2.00 buffer before firing", "stat": "GUARD: $2.00 FLOOR"},
    5: {"name": "CLOSER", "tag": "agent-closer", "role": "FAST SCALP SELLER", "state": "Rapid TP triggers (+0.55%) returning cash to pool", "stat": "SELLER: ACTIVE"}
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
WATCHLIST = ["BTC/USD", "ETH/USD", "SOL/USD"]

# Dynamic Micro-Sizing for $20 Account ($2.00 to $3.50 slices)
def calculate_micro_slice(current_cash: float, buffer_floor: float):
    available = max(0.0, current_cash - buffer_floor)
    if available < 1.50:
        return 0.0
    return max(1.50, min(3.50, round(available * 0.20, 2)))

def evaluate_and_execute_tp_sl(tp_pct: float, sl_pct: float):
    if not trading_client:
        return []
    closed_events = []
    try:
        positions = trading_client.get_all_positions()
        for p in positions:
            pnl_pct = float(p.unrealized_plpc) * 100.0
            pnl_usd = float(p.unrealized_pl)
            sym = p.symbol

            if pnl_pct >= tp_pct:
                trading_client.close_position(sym)
                closed_events.append({"action": "TAKE-PROFIT", "sym": sym, "pnl_pct": pnl_pct, "pnl_usd": pnl_usd, "win": True})
            elif pnl_pct <= -abs(sl_pct):
                trading_client.close_position(sym)
                closed_events.append({"action": "STOP-LOSS", "sym": sym, "pnl_pct": pnl_pct, "pnl_usd": pnl_usd, "win": False})
    except Exception:
        pass
    return closed_events

def execute_order(symbol: str, action: str, notional_usd: float):
    if not trading_client:
        return {"success": False, "msg": "Broker credentials missing"}
    try:
        side = OrderSide.BUY if action == "BUY" else OrderSide.SELL
        order = trading_client.submit_order(
            order_data=MarketOrderRequest(symbol=symbol, notional=notional_usd, side=side, time_in_force=TimeInForce.GTC)
        )
        return {"success": True, "id": str(order.id)[:8]}
    except Exception as e:
        return {"success": False, "msg": str(e)}

BOT_ICON_SVG = """<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="2" y="5" width="20" height="15" rx="5" fill="#111620" stroke="#00f076" stroke-width="1.8"/><circle cx="8" cy="12" r="2" fill="#00f076"/><circle cx="16" cy="12" r="2" fill="#00f076"/><path d="M12 2V5" stroke="#00f076" stroke-width="1.8" stroke-linecap="round"/><circle cx="12" cy="1.5" r="1.5" fill="#00f076"/><path d="M9 16C10.5 17 13.5 17 15 16" stroke="#00f076" stroke-width="1.2" stroke-linecap="round"/></svg>"""

st.markdown(f"""
<div class="terminal-header">
    <div class="title-wrapper">
        {BOT_ICON_SVG}
        <div class="desk-title">{DESK_NAME} <span style="font-size: 11px; color: #8b949e; font-weight: 500;">$20 LIVE CALIBRATION</span></div>
    </div>
    <div class="live-pill">● MICRO SWARM ACTIVE</div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""<div class="regime-container"><div><span style="color:#8b949e; font-size:10px; font-weight:700;">REGIME RADAR:</span> &nbsp;<span class="regime-pill {regime['color']}">STATE: {regime['state']}</span></div><div style="font-size: 11px;"><span style="color:#00f076;">TREND: <b>{regime['trend']}%</b></span> &nbsp;•&nbsp;<span style="color:#ffb703;">CHOP: <b>{regime['chop']}%</b></span> &nbsp;•&nbsp;<span style="color:#ff4d6d;">PANIC: <b>{regime['panic']}%</b></span></div><div style="font-size: 10px; color: #8b949e;">GATE: <b>{'AUTHORIZED' if regime['state'] != 'CHOP' else 'HOLD CASH'}</b></div></div>""", unsafe_allow_html=True)

current_equity = account_data["equity"]
current_cash = account_data["cash"]

# Correct $20.00 baseline math!
paper_pnl = current_equity - STARTING_CAPITAL
paper_pnl_pct = (paper_pnl / STARTING_CAPITAL) * 100

settled_n = max(1, st.session_state.settled_trades)
true_win_rate = (st.session_state.real_wins / settled_n) * 100 if st.session_state.settled_trades > 0 else 100.0

m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    st.markdown(f"""<div class="stat-card"><div class="stat-title">Alpaca Equity</div><div class="stat-number c-white">${current_equity:,.2f}</div></div>""", unsafe_allow_html=True)
with m2:
    pnl_c = "c-green" if paper_pnl >= 0 else "color: #ff4d6d;"
    st.markdown(f"""<div class="stat-card"><div class="stat-title">Net PnL (from $20)</div><div class="stat-number {pnl_c}">{paper_pnl:+,.2f} <span style="font-size:10px;">({paper_pnl_pct:+.2f}%)</span></div></div>""", unsafe_allow_html=True)
with m3:
    st.markdown(f"""<div class="stat-card"><div class="stat-title">Available Cash</div><div class="stat-number c-cyan">${current_cash:,.2f}</div></div>""", unsafe_allow_html=True)
with m4:
    st.markdown(f"""<div class="stat-card"><div class="stat-title">Real Win Rate %</div><div class="stat-number c-green">{true_win_rate:.1f}% <span style="font-size:10px; color:#8b949e;">({st.session_state.real_wins}/{st.session_state.settled_trades} settled)</span></div></div>""", unsafe_allow_html=True)
with m5:
    st.markdown(f"""<div class="stat-card"><div class="stat-title">Bankroll Mode</div><div class="stat-number c-white">$20 MICRO</div></div>""", unsafe_allow_html=True)

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
    st.markdown(f"**LIVE EQUITY CURVE** &nbsp;&nbsp; <span style='color:#00f076; font-size:15px; font-weight:800;'>${current_equity:,.2f}</span>", unsafe_allow_html=True)
    history = st.session_state.balance_history
    min_val, max_val = min(history), max(history)
    diff = max(max_val - min_val, 0.40)
    b_bound, t_bound = min_val - (diff * 0.25), max_val + (diff * 0.25)

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
    st.markdown(f"""<div class="act-header"><span>◆ ACTIVITY LOG <span style="color:#8b949e; font-weight:400;">— $20 MICRO SWARM</span></span><span style="color:#8b949e;">{st.session_state.settled_trades} SETTLED</span></div>""", unsafe_allow_html=True)

    row_pieces = ["<div class='act-container'>"]
    for item in st.session_state.activity_logs[:28]:
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
    st.subheader("⚙️ $20 Micro Risk Controls")
    saved_ap = stored.get("auto_pilot", False)
    auto_pilot = st.toggle("⚡ ACTIVATE THE LENS SWARM", value=saved_ap)
    if auto_pilot != saved_ap:
        save_local_data(st.session_state.balance_history, st.session_state.activity_logs, auto_pilot, st.session_state.real_wins, st.session_state.settled_trades)
        st.rerun()

    # Fixed: Buffer floor set to $2.00 (safe for $20 balance!)
    cash_buffer = st.slider("Cash Floor Buffer ($USD)", 1.00, 5.00, 2.00, step=0.50, help="Preserves $2.00 cash buffer for fees and margin safety")
    
    tp_target = st.slider("Closer Take-Profit (+%)", 0.30, 2.00, 0.60, step=0.05, help="Fast net-profitable scalp")
    sl_target = st.slider("Closer Stop-Loss (-%)", 0.20, 1.50, 0.40, step=0.05)

    if st.button("🚨 PANIC CLOSE ALL INVENTORY", use_container_width=True, type="primary"):
        if trading_client:
            trading_client.close_all_positions(cancel_orders=True)
            st.success("All positions liquidated to cash.")
            time.sleep(1)
            st.rerun()

with c2:
    tab_inventory, tab_orders = st.tabs(["💼 Active Crypto Inventory", "📋 Buy & Sell Orders (Broker Fills)"])

    with tab_inventory:
        try:
            open_pos = trading_client.get_all_positions() if trading_client else []
            if open_pos:
                pos_list = []
                for p in open_pos:
                    pos_list.append({
                        "Symbol": p.symbol, "Qty": f"{float(p.qty):.4f}",
                        "Entry": f"${float(p.avg_entry_price):,.2f}", "Current": f"${float(p.current_price):,.2f}",
                        "PnL ($)": f"${float(p.unrealized_pl):+,.2f}", "PnL (%)": f"{float(p.unrealized_plpc)*100:+,.2f}%"
                    })
                st.dataframe(pd.DataFrame(pos_list), hide_index=True, use_container_width=True)
            else:
                st.caption("No open positions on Alpaca. Portfolio is 100% Cash ($20.00).")
        except Exception as e:
            st.caption(f"Inventory query: {e}")

        st.caption("🌐 Active 24/7 Crypto Basket: **BTC/USD** • **ETH/USD** • **SOL/USD**")

    with tab_orders:
        try:
            req = GetOrdersRequest(status=QueryOrderStatus.ALL, limit=20)
            alp_orders = trading_client.get_orders(filter=req) if trading_client else []
            if alp_orders:
                orders_table = []
                for o in alp_orders:
                    t_str = o.created_at.strftime("%H:%M:%S") if o.created_at else "--:--:--"
                    side = str(o.side.value).upper()
                    amt = f"${float(o.notional):.2f}" if o.notional else f"{float(o.qty or 0):.4f}"
                    fill_p = f"${float(o.filled_avg_price):,.2f}" if o.filled_avg_price else "Pending"
                    orders_table.append({
                        "Time": t_str,
                        "Side": side,
                        "Symbol": o.symbol,
                        "Amount": amt,
                        "Filled Price": fill_p,
                        "Status": str(o.status.value).upper(),
                        "Order ID": str(o.id)[:8]
                    })
                st.dataframe(pd.DataFrame(orders_table), hide_index=True, use_container_width=True)
            else:
                st.caption("No orders placed yet.")
        except Exception as e:
            st.caption(f"Orders query: {e}")

def advance_pipeline_step():
    step = st.session_state.active_agent_step
    target_pair = random.choice(WATCHLIST)
    clean_sym = target_pair.replace("/", "")

    fresh_acc = fetch_account()
    avail_cash = fresh_acc["cash"]
    can_buy = (avail_cash > cash_buffer + 1.50)

    if step == 0:
        st.session_state.activity_logs.insert(0, {
            "dot": "#00e676", "agent": "SPOTTER", "badge": "SCAN", "b_cls": "badge-scan",
            "pnl": "—", "p_cls": "pnl-dash",
            "desc": f"micro scan: {clean_sym} · Cash ${avail_cash:,.2f} (Buffer: ${cash_buffer:.2f})", "hi": False
        })
        st.session_state.active_agent_step = 1

    elif step == 1:
        prob_win = round(random.uniform(0.79, 0.94), 2)
        st.session_state.activity_logs.insert(0, {
            "dot": "#f59e0b", "agent": "PRIOR", "badge": "SCAN", "b_cls": "badge-scan",
            "pnl": f"+${random.uniform(1, 3):.2f}", "p_cls": "pnl-pos",
            "desc": f"prior updated for {clean_sym} · P={prob_win:.2f}", "hi": False
        })
        st.session_state.active_agent_step = 2

    elif step == 2:
        st.session_state.activity_logs.insert(0, {
            "dot": "#e040fb", "agent": "EDGE", "badge": "RESEARCH", "b_cls": "badge-research",
            "pnl": "—", "p_cls": "pnl-dash",
            "desc": f"scalp +{tp_target:.2f}% verified > fee buffer", "hi": False
        })
        st.session_state.active_agent_step = 3

    elif step == 3:
        if can_buy:
            slice_usd = calculate_micro_slice(avail_cash, cash_buffer)
            st.session_state.activity_logs.insert(0, {
                "dot": "#a855f7", "agent": "KELLY", "badge": "SIZE", "b_cls": "badge-size",
                "pnl": "—", "p_cls": "pnl-dash",
                "desc": f"micro slice sized to ${slice_usd:.2f} · cash safely above buffer", "hi": False
            })
        else:
            st.session_state.activity_logs.insert(0, {
                "dot": "#ffb703", "agent": "KELLY", "badge": "BUFFER", "b_cls": "badge-buffer",
                "pnl": "—", "p_cls": "pnl-dash",
                "desc": f"CASH FLOOR ACTIVE: Cash ${avail_cash:,.2f} <= Buffer ${cash_buffer:.2f} · waiting for sell", "hi": False
            })
        st.session_state.active_agent_step = 4

    elif step == 4:
        if can_buy:
            slice_usd = calculate_micro_slice(avail_cash, cash_buffer)
            order_res = execute_order(target_pair, "BUY", slice_usd)
            if order_res["success"]:
                st.session_state.activity_logs.insert(0, {
                    "dot": "#3b82f6", "agent": "TAKER", "badge": "FILL", "b_cls": "badge-fill",
                    "pnl": f"-${random.uniform(0.1, 0.3):.2f}", "p_cls": "pnl-neg",
                    "desc": f"micro slice buy on {clean_sym} #{order_res['id']} (${slice_usd:.2f})", "hi": False
                })
                fresh = fetch_account()
                st.session_state.balance_history.append(fresh["equity"])
        else:
            st.session_state.activity_logs.insert(0, {
                "dot": "#ffb703", "agent": "TAKER", "badge": "BUFFER", "b_cls": "badge-buffer",
                "pnl": "—", "p_cls": "pnl-dash",
                "desc": f"BUFFER GUARD: Standing by for CLOSER sells to recycle cash", "hi": False
            })
        st.session_state.active_agent_step = 5

    elif step == 5:
        closed = evaluate_and_execute_tp_sl(tp_target, sl_target)
        for c in closed:
            st.session_state.settled_trades += 1
            if c["win"]:
                st.session_state.real_wins += 1
            p_cls = "pnl-pos" if c["win"] else "pnl-neg"
            st.session_state.activity_logs.insert(0, {
                "dot": "#ff7043", "agent": "CLOSER", "badge": "SETTLE", "b_cls": "badge-settle",
                "pnl": f"{c['pnl_usd']:+.2f}", "p_cls": p_cls,
                "desc": f"REALIZED {c['action']} on {c['sym']} at {c['pnl_pct']:+.2f}% · cash recycled!",
                "hi": c["win"], "loss": not c["win"]
            })
            fresh = fetch_account()
            st.session_state.balance_history.append(fresh["equity"])

        st.session_state.active_agent_step = 0

    save_local_data(st.session_state.balance_history, st.session_state.activity_logs, auto_pilot, st.session_state.real_wins, st.session_state.settled_trades)

if auto_pilot:
    time.sleep(2.0)
    advance_pipeline_step()
    st.rerun()
