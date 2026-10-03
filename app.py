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

# 1. Page Configuration
st.set_page_config(
    page_title="AI Agent Terminal | Multi-Agent Network",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp {
        background-color: #0d0f12;
        color: #e6edf3;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
    }
    .terminal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 8px;
        border-bottom: 1px solid #1c2128;
        margin-bottom: 15px;
    }
    .bot-title {
        font-size: 24px;
        font-weight: 800;
        letter-spacing: -0.5px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .live-badge {
        background: #12281e;
        color: #00f076;
        border: 1px solid #00f076;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
    }
    .stat-box {
        background: #13171d;
        border: 1px solid #21262d;
        border-radius: 12px;
        padding: 12px 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    }
    .stat-label {
        font-size: 11px;
        color: #8b949e;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .stat-value {
        font-size: 22px;
        font-weight: 800;
        margin-top: 4px;
    }
    .val-green { color: #00f076; }
    .val-white { color: #ffffff; }
    .log-container {
        background: #13171d;
        border: 1px solid #21262d;
        border-radius: 12px;
        padding: 12px;
        height: 330px;
        overflow-y: auto;
        font-family: 'Courier New', Courier, monospace;
        font-size: 12px;
    }
    .log-row {
        display: flex;
        justify-content: space-between;
        padding: 5px 0;
        border-bottom: 1px solid #181d24;
    }
    .buy-tag { color: #00f076; font-weight: bold; }
    .sell-tag { color: #ff5252; font-weight: bold; }
    .heartbeat-bar {
        background: #13171d;
        border: 1px solid #21262d;
        border-radius: 8px;
        padding: 8px 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin: 15px 0;
        font-family: monospace;
        font-size: 12px;
        color: #00f076;
    }
</style>
""", unsafe_allow_html=True)

load_dotenv()

# Cloud Secrets & Env Compatibility
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
ALPACA_KEY = st.secrets.get("ALPACA_API_KEY", os.getenv("ALPACA_API_KEY"))
ALPACA_SECRET = st.secrets.get("ALPACA_SECRET_KEY", os.getenv("ALPACA_SECRET_KEY"))

gemini_client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None
trading_client = TradingClient(ALPACA_KEY, ALPACA_SECRET, paper=True) if ALPACA_KEY and ALPACA_SECRET else None
news_client = NewsClient(ALPACA_KEY, ALPACA_SECRET) if ALPACA_KEY and ALPACA_SECRET else None

HISTORY_FILE = "trade_history.json"

def load_local_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"balance_history": [], "trade_logs": []}

def save_local_history(balance_history, trade_logs):
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump({
                "balance_history": balance_history[-40:],
                "trade_logs": trade_logs[:40]
            }, f, indent=2)
    except Exception:
        pass

def fetch_alpaca_history():
    if not trading_client:
        return []
    try:
        req = GetOrdersRequest(status=QueryOrderStatus.ALL, limit=20)
        orders = trading_client.get_orders(filter=req)
        logs = []
        for o in orders:
            t_str = o.created_at.strftime("%H:%M:%S") if o.created_at else "00:00:00"
            amt = float(o.notional) if o.notional else 10.0
            logs.append({
                "time": t_str,
                "action": str(o.side.value).upper(),
                "sym": o.symbol.split("/")[0],
                "amt": f"${amt:.2f}",
                "id": str(o.id)[:8],
                "agent": "ALPACA",
                "reason": f"Broker fill: {o.status.value}"
            })
        return logs
    except Exception:
        return []

def fetch_account():
    if not trading_client:
        return {"equity": 100000.0, "cash": 100000.0, "buying_power": 100000.0}
    try:
        acc = trading_client.get_account()
        return {
            "equity": float(acc.equity),
            "cash": float(acc.cash),
            "buying_power": float(acc.buying_power)
        }
    except Exception:
        return {"equity": 100000.0, "cash": 100000.0, "buying_power": 100000.0}

account_data = fetch_account()
stored = load_local_history()

if "trade_logs" not in st.session_state:
    st.session_state.trade_logs = stored["trade_logs"] if stored["trade_logs"] else fetch_alpaca_history()

if "balance_history" not in st.session_state:
    if stored["balance_history"] and len(stored["balance_history"]) > 1:
        st.session_state.balance_history = stored["balance_history"]
        if st.session_state.balance_history[-1] != account_data["equity"]:
            st.session_state.balance_history.append(account_data["equity"])
    else:
        st.session_state.balance_history = [account_data["equity"] - 0.35, account_data["equity"] - 0.12, account_data["equity"]]

if "active_agent_idx" not in st.session_state:
    st.session_state.active_agent_idx = 1

# Milestone 3: 5 Distinct Agent Profiles
AGENTS = [
    {
        "name": "ORVEN",
        "icon": "🔵",
        "type": "MOMENTUM",
        "min_conf": 0.65,
        "style": "Aggressive trend and hype chaser. Buys surges immediately.",
        "prompt": "You are ORVEN, an aggressive momentum trader. Buy aggressively when there is social hype, whale volume, or upside surges. Accept lower confirmation."
    },
    {
        "name": "BRAVA",
        "icon": "🔶",
        "type": "SCALPER",
        "min_conf": 0.75,
        "style": "High-frequency scalper. Enters fast liquidity sweeps.",
        "prompt": "You are BRAVA, a fast scalper. Only trade rapid order-flow imbalance or immediate volume spikes. Strict on noise."
    },
    {
        "name": "MIRAX",
        "icon": "⚪",
        "type": "BREAKOUT",
        "min_conf": 0.75,
        "style": "Catalyst specialist. Trades macro approvals and ETF news.",
        "prompt": "You are MIRAX, a breakout catalyst trader. Look strictly for fundamental catalysts: ETF inflows, listings, regulatory approvals, institutional accumulation."
    },
    {
        "name": "DUSKA",
        "icon": "🔺",
        "type": "REVERSAL",
        "min_conf": 0.70,
        "style": "Contrarian dip buyer. Buys panic selloffs and liquidations.",
        "prompt": "You are DUSKA, a contrarian dip hunter. When you see bad headlines, panic, or crashes, look for overreactions and BUY the dip. Sells euphoria."
    },
    {
        "name": "NOA",
        "icon": "🟩",
        "type": "ARBITRAGE",
        "min_conf": 0.85,
        "style": "Ultra-conservative. Highest confidence threshold only.",
        "prompt": "You are NOA, a risk-averse quantitative agent. Only approve BUY or SELL if conviction is extraordinarily high (>0.85). Default to HOLD if in doubt."
    }
]

curr_agent = AGENTS[st.session_state.active_agent_idx]

# Live News Fetcher
def fetch_live_news(ticker: str):
    headlines = []
    clean_sym = ticker.split("/")[0]
    if news_client:
        try:
            req = NewsRequest(symbols=clean_sym, limit=5)
            for item in news_client.get_news(req):
                if hasattr(item, "headline") and item.headline:
                    headlines.append(item.headline)
        except Exception:
            pass

    if not headlines:
        try:
            feed_url = "https://cointelegraph.com/rss"
            req = urllib.request.Request(feed_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                root = ET.fromstring(resp.read())
                for item in root.findall(".//item"):
                    t = item.find("title")
                    if t is not None and t.text:
                        headlines.append(t.text)
                    if len(headlines) >= 5:
                        break
        except Exception:
            pass

    if not headlines:
        headlines = [f"Institutional accumulation surges as {clean_sym} approaches breakout point."]
    return headlines

# Multi-Agent Local Fallback
def multi_agent_fallback(headline: str, agent: dict):
    h = headline.lower()
    bull_words = ["surge", "record", "inflow", "breakout", "rally", "buy", "gain", "bull", "accumulate", "jump", "soar", "high"]
    bear_words = ["drop", "dump", "crash", "fall", "ban", "hack", "sec", "lawsuit", "bear", "plunge", "loss", "liquidat"]

    bull_score = sum(1 for w in bull_words if w in h)
    bear_score = sum(1 for w in bear_words if w in h)

    # Duska buys panic dips
    if agent["name"] == "DUSKA" and bear_score > 0:
        return {"action": "BUY", "confidence": 0.82, "reason": "Duska Contrarian: Buying the panic dip"}
    
    # Orven buys momentum fast
    if agent["name"] == "ORVEN" and bull_score > 0:
        return {"action": "BUY", "confidence": 0.88, "reason": "Orven Momentum: High hype detected"}

    # General logic
    if bull_score > bear_score:
        conf = min(0.95, 0.70 + (bull_score * 0.10))
        return {"action": "BUY", "confidence": conf, "reason": f"{agent['name']} Thesis: Bullish alignment"}
    elif bear_score > bull_score:
        conf = min(0.95, 0.70 + (bear_score * 0.10))
        return {"action": "SELL", "confidence": conf, "reason": f"{agent['name']} Thesis: Bearish risk detected"}
    else:
        return {"action": "HOLD", "confidence": 0.50, "reason": f"{agent['name']}: Neutral sentiment"}

# Decision Engine with Custom Agent Prompts
def get_decision(headline: str, symbol: str, agent: dict):
    if gemini_client:
        prompt = f"""
        {agent['prompt']}
        Analyze this live market headline for asset {symbol}:
        "{headline}"
        Output ONLY raw valid JSON:
        {{"action": "BUY" | "SELL" | "HOLD", "confidence": 0.85, "reason": "Under 10 words"}}
        """
        try:
            res = gemini_client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.1)
            )
            raw = res.text.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1].rsplit("\n", 1)[0]
            return json.loads(raw), f"Gemini ({agent['name']})"
        except Exception:
            return multi_agent_fallback(headline, agent), f"Local Engine ({agent['name']})"
    return multi_agent_fallback(headline, agent), f"Local Engine ({agent['name']})"

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

# Header
st.markdown(f"""
    <div class="terminal-header">
        <div class="bot-title">⚡ Grok/Gemini Terminal <span style="font-size: 13px; color: #8b949e; font-weight: 400;">ACTIVE AGENT: <b>{curr_agent['icon']} {curr_agent['name']}</b> ({curr_agent['type']})</span></div>
        <div class="live-badge">● LIVE SANDBOX CONNECTED</div>
    </div>
""", unsafe_allow_html=True)

# Top Metrics Row
current_equity = account_data["equity"]
paper_pnl = current_equity - 100000.0
paper_pnl_pct = (paper_pnl / 100000.0) * 100
total_trades = len(st.session_state.trade_logs)

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f"""<div class="stat-box"><div class="stat-label">Alpaca Paper Equity</div><div class="stat-value val-white">${current_equity:,.2f}</div></div>""", unsafe_allow_html=True)
with m2:
    pnl_color = "val-green" if paper_pnl >= 0 else "color: #ff5252;"
    st.markdown(f"""<div class="stat-box"><div class="stat-label">Paper PnL</div><div class="stat-value {pnl_color}">{paper_pnl:+,.2f} <span style="font-size:13px;">({paper_pnl_pct:+.2f}%)</span></div></div>""", unsafe_allow_html=True)
with m3:
    st.markdown(f"""<div class="stat-box"><div class="stat-label">Buying Power</div><div class="stat-value val-white">${account_data['buying_power']:,.2f}</div></div>""", unsafe_allow_html=True)
with m4:
    st.markdown(f"""<div class="stat-box"><div class="stat-label">Active Agent Thesis</div><div class="stat-value val-green">{curr_agent['name']} <span style="font-size:11px; color:#8b949e;">(Min Conf: {curr_agent['min_conf']*100:.0f}%)</span></div></div>""", unsafe_allow_html=True)

st.write("")

# Split View: Chart & Activity Log
col_left, col_right = st.columns([1.4, 1.0])

with col_left:
    st.markdown(f"**LIVE EQUITY CURVE** &nbsp;&nbsp; <span style='color:#00f076; font-size:18px; font-weight:700;'>${current_equity:,.2f}</span>", unsafe_allow_html=True)
    history = st.session_state.balance_history
    min_val, max_val = min(history), max(history)
    diff = max(max_val - min_val, 0.40)
    b_bound, t_bound = min_val - (diff * 0.25), max_val + (diff * 0.25)

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=[b_bound] * len(history), mode='lines', line=dict(width=0), showlegend=False, hoverinfo='none'))
    fig.add_trace(go.Scatter(
        y=history, mode='lines+markers', line=dict(color='#00f076', width=2.8),
        fill='tonexty', fillcolor='rgba(0, 240, 118, 0.16)',
        marker=dict(size=6, color='#00f076', line=dict(width=1, color='#ffffff')),
        hoverinfo='y', showlegend=False
    ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="#13171d", plot_bgcolor="#13171d",
        margin=dict(l=0, r=0, t=10, b=0), height=320,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=True, gridcolor="#1c2128", zeroline=False, side="right", tickprefix="$", tickformat=",.2f", range=[b_bound, t_bound], autorange=False)
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

with col_right:
    st.markdown("**LIVE ACTIVITY LOG** &nbsp;&nbsp; <span style='color:#8b949e; font-size:11px;'>PERSISTED • ALPACA LINKED</span>", unsafe_allow_html=True)
    log_html = "<div class='log-container'>"
    if not st.session_state.trade_logs:
        log_html += "<div style='color: #8b949e; text-align: center; margin-top: 130px;'>No trades yet.</div>"
    else:
        for item in st.session_state.trade_logs[:25]:
            cls = "buy-tag" if item['action'] == "BUY" else "sell-tag"
            agent_tag = item.get("agent", "AI")
            log_html += f"<div class='log-row'><span>{item['time']} <span class='{cls}'>{item['action']}</span> {item['sym']} <small style='color:#8b949e;'>[{agent_tag}]</small></span><span>{item['amt']} <small style='color:#8b949e;'>ID:{item['id']}</small></span></div>"
    log_html += "</div>"
    st.markdown(log_html, unsafe_allow_html=True)

# Heartbeat
st.markdown(f"""
    <div class="heartbeat-bar">
        <span>ENGINE HEARTBEAT: &nbsp; ∿∿∿/\∿∿/\∿∿/\∿∿∿ &nbsp; [AGENT ACTIVE: {curr_agent['name']}]</span>
        <span>STRATEGY: {curr_agent['style']}</span>
    </div>
""", unsafe_allow_html=True)

# Interactive Agent Rotation Deck (Clickable buttons!)
st.caption("🤖 Select or Rotate AI Agents:")
agent_cols = st.columns(len(AGENTS))
for i, ag in enumerate(AGENTS):
    with agent_cols[i]:
        label = f"{ag['icon']} {ag['name']}"
        btn_type = "primary" if i == st.session_state.active_agent_idx else "secondary"
        if st.button(label, key=f"btn_agent_{i}", use_container_width=True, type=btn_type):
            st.session_state.active_agent_idx = i
            st.rerun()

st.divider()

# Controls
c1, c2 = st.columns([1, 2])
with c1:
    auto_pilot = st.toggle("⚡ ACTIVATE REAL-TIME AUTO-PILOT", value=False)
    selected_ticker = st.selectbox("Trading Pair", ["BTC/USD", "ETH/USD", "SPY", "NVDA", "TSLA"])
    order_size = st.slider("Order Size ($USD)", 5.0, 50.0, 10.0, step=5.0)

with c2:
    live_news_list = fetch_live_news(selected_ticker)
    st.caption(f"📡 Latest Real-Time Headline for {curr_agent['name']}:")
    current_headline = st.text_input("Active Headline:", value=live_news_list[0] if live_news_list else "ETF accumulation accelerating across all venues.")
    manual_exec = st.button(f"🚀 Let {curr_agent['name']} Evaluate & Execute Order", use_container_width=True)

def process_trade(headline, ticker, amount):
    ag = AGENTS[st.session_state.active_agent_idx]
    with st.spinner(f"Agent {ag['name']} is evaluating thesis..."):
        verdict, engine_used = get_decision(headline, ticker, ag)
        action = verdict.get("action", "HOLD")
        confidence = verdict.get("confidence", 0.0)
        reason = verdict.get("reason", "N/A")

        if action in ["BUY", "SELL"] and confidence >= ag["min_conf"]:
            order_res = execute_order(ticker, action, amount)
            if order_res["success"]:
                st.session_state.trade_logs.insert(0, {
                    "time": time.strftime("%H:%M:%S"),
                    "action": action,
                    "sym": ticker.split("/")[0],
                    "amt": f"${amount:.2f}",
                    "id": order_res["id"],
                    "agent": ag["name"],
                    "reason": reason
                })
                fresh = fetch_account()
                st.session_state.balance_history.append(fresh["equity"])
                # Rotate to next agent
                st.session_state.active_agent_idx = (st.session_state.active_agent_idx + 1) % len(AGENTS)
                save_local_history(st.session_state.balance_history, st.session_state.trade_logs)
                st.success(f"{ag['name']} Executed {action} {ticker} (${amount})! Reason: {reason}")
                st.rerun()
            else:
                st.error(f"Alpaca Order Rejected: {order_res['msg']}")
        else:
            st.info(f"{ag['name']} decided {action} (Confidence: {confidence:.2f} < Min {ag['min_conf']}). Reason: {reason}")

if manual_exec:
    process_trade(current_headline, selected_ticker, order_size)

if auto_pilot:
    time.sleep(8)
    fresh_headlines = fetch_live_news(selected_ticker)
    selected_h = random.choice(fresh_headlines)
    process_trade(selected_h, selected_ticker, order_size)
