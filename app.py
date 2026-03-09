import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import time

st.set_page_config(
    page_title="Quantum Trade | AI Stock Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Inter:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:#060a0f;}
.main .block-container{padding-top:1rem;max-width:1400px;}
section[data-testid="stSidebar"]{background:#0d1117!important;border-right:1px solid #1f2937;}
div[data-testid="metric-container"]{background:#0d1117;border:1px solid #1f2937;border-radius:8px;padding:12px 16px;}
div[data-testid="metric-container"] label{color:#6b7280!important;font-size:10px!important;letter-spacing:1.5px;text-transform:uppercase;font-family:'Space Mono',monospace!important;}
div[data-testid="metric-container"] div[data-testid="stMetricValue"]{color:#00ff9d!important;font-family:'Space Mono',monospace!important;font-size:20px!important;}
.stSelectbox>div>div{background:#0d1117!important;border-color:#1f2937!important;color:#e5e7eb!important;}
.stNumberInput input{background:#0d1117!important;border-color:#1f2937!important;color:#00ff9d!important;font-family:'Space Mono',monospace!important;}
.stButton button{background:#1f2937!important;border:1px solid #374151!important;color:#9ca3af!important;font-family:'Space Mono',monospace!important;font-size:11px!important;letter-spacing:1px;}
.stButton button:hover{border-color:#00ff9d!important;color:#00ff9d!important;}
h1,h2,h3{color:#ffffff!important;font-family:'Space Mono',monospace!important;}
.stTabs [data-baseweb="tab-list"]{background:#0d1117;border-bottom:1px solid #1f2937;}
.stTabs [data-baseweb="tab"]{background:transparent!important;color:#4b5563!important;font-family:'Space Mono',monospace!important;font-size:11px!important;letter-spacing:1px;border-bottom:2px solid transparent!important;}
.stTabs [aria-selected="true"]{color:#00ff9d!important;border-bottom:2px solid #00ff9d!important;}
</style>
""", unsafe_allow_html=True)

TOP_STOCKS = {
    "AAPL":  {"name":"Apple Inc.",         "sector":"Technology"},
    "NVDA":  {"name":"NVIDIA Corp.",       "sector":"Technology"},
    "MSFT":  {"name":"Microsoft Corp.",    "sector":"Technology"},
    "GOOGL": {"name":"Alphabet Inc.",      "sector":"Technology"},
    "AMZN":  {"name":"Amazon.com",         "sector":"Consumer"},
    "TSLA":  {"name":"Tesla Inc.",         "sector":"Automotive"},
    "META":  {"name":"Meta Platforms",     "sector":"Technology"},
    "BRK-B": {"name":"Berkshire Hathaway", "sector":"Finance"},
    "JPM":   {"name":"JPMorgan Chase",     "sector":"Finance"},
    "V":     {"name":"Visa Inc.",          "sector":"Finance"},
}

BROKERS = [
    {"name":"Interactive Brokers","rating":9.5,"fee":"$0.005/acción","access":"Global","ideal":"Traders avanzados e internacionales","url":"interactivebrokers.com"},
    {"name":"TD Ameritrade",      "rating":9.0,"fee":"$0",           "access":"EEUU",  "ideal":"Análisis técnico profesional",     "url":"tdameritrade.com"},
    {"name":"Fidelity",           "rating":8.8,"fee":"$0",           "access":"EEUU",  "ideal":"Inversión a largo plazo",          "url":"fidelity.com"},
    {"name":"Robinhood",          "rating":7.5,"fee":"$0",           "access":"EEUU",  "ideal":"Principiantes, interfaz simple",   "url":"robinhood.com"},
    {"name":"Saxo Bank",          "rating":8.5,"fee":"Variable",     "access":"Global","ideal":"Inversores internacionales",       "url":"home.saxo"},
    {"name":"XTB",                "rating":8.2,"fee":"$0",           "access":"Global","ideal":"Disponible en Colombia",           "url":"xtb.com"},
]

@st.cache_data(ttl=60)
def fetch_data(symbol, period="1y", interval="1d"):
    try:
        df = yf.Ticker(symbol).history(period=period, interval=interval)
        if df.empty: return pd.DataFrame()
        df.index = pd.to_datetime(df.index)
        df = df[["Open","High","Low","Close","Volume"]].copy()
        df.columns = ["open","high","low","close","volume"]
        return df
    except:
        return pd.DataFrame()

def add_indicators(df):
    if df.empty or len(df)<5: return df
    df = df.copy()
    for w in [7,20,50,200]:
        if len(df)>=w: df[f"ma{w}"] = df["close"].rolling(w).mean()
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    df["rsi"] = 100-(100/(1+(gain/loss.replace(0,np.nan))))
    df["bb_mid"]   = df["close"].rolling(20).mean()
    std            = df["close"].rolling(20).std()
    df["bb_upper"] = df["bb_mid"]+2*std
    df["bb_lower"] = df["bb_mid"]-2*std
    ema12=df["close"].ewm(span=12).mean(); ema26=df["close"].ewm(span=26).mean()
    df["macd"]=ema12-ema26; df["macd_signal"]=df["macd"].ewm(span=9).mean()
    df["macd_hist"]=df["macd"]-df["macd_signal"]
    hl=df["high"]-df["low"]; hpc=abs(df["high"]-df["close"].shift()); lpc=abs(df["low"]-df["close"].shift())
    df["atr"]=pd.concat([hl,hpc,lpc],axis=1).max(axis=1).rolling(14).mean()
    return df

def generate_signal(df):
    if df.empty or len(df)<50:
        return {"signal":"NEUTRAL","strength":50,"reasons":["Datos insuficientes"],"color":"#ffd60a"}
    last=df.iloc[-1]; score=50; reasons=[]
    if pd.notna(last.get("ma7")) and pd.notna(last.get("ma20")):
        if last["ma7"]>last["ma20"]: score+=12; reasons.append("✅ MA7 > MA20 — cruce alcista")
        else: score-=12; reasons.append("❌ MA7 < MA20 — cruce bajista")
    if pd.notna(last.get("ma50")):
        if last["close"]>last["ma50"]: score+=8; reasons.append("✅ Precio sobre MA50 — tendencia alcista")
        else: score-=8; reasons.append("❌ Precio bajo MA50 — tendencia bajista")
    rsi=last.get("rsi",50)
    if pd.notna(rsi):
        if rsi<30: score+=18; reasons.append(f"✅ RSI {rsi:.1f} — sobrevendido (señal COMPRA)")
        elif rsi>70: score-=18; reasons.append(f"❌ RSI {rsi:.1f} — sobrecomprado (señal VENTA)")
        else: reasons.append(f"➖ RSI {rsi:.1f} — zona neutral")
    if pd.notna(last.get("bb_lower")) and pd.notna(last.get("bb_upper")):
        if last["close"]<last["bb_lower"]: score+=10; reasons.append("✅ Precio bajo banda inferior Bollinger")
        elif last["close"]>last["bb_upper"]: score-=10; reasons.append("❌ Precio sobre banda superior Bollinger")
    if pd.notna(last.get("macd")) and pd.notna(last.get("macd_signal")):
        if last["macd"]>last["macd_signal"]: score+=8; reasons.append("✅ MACD positivo — momentum alcista")
        else: score-=8; reasons.append("❌ MACD negativo — momentum bajista")
    score=max(0,min(100,score))
    if score>=65: sig,col="COMPRAR","#00ff9d"
    elif score<=35: sig,col="VENDER","#ff4d6d"
    else: sig,col="NEUTRAL","#ffd60a"
    return {"signal":sig,"strength":score,"reasons":reasons,"color":col}

def kelly_criterion(win_rate=0.55, avg_win=1.5, avg_loss=1.0):
    b=avg_win/avg_loss; k=win_rate-(1-win_rate)/b
    return max(0.0,min(0.25,k))

def build_main_chart(df, symbol):
    fig=make_subplots(rows=3,cols=1,shared_xaxes=True,row_heights=[0.6,0.2,0.2],vertical_spacing=0.02)
    fig.add_trace(go.Candlestick(x=df.index,open=df["open"],high=df["high"],low=df["low"],close=df["close"],
        name="Precio",increasing_fillcolor="#00ff9d",decreasing_fillcolor="#ff4d6d",
        increasing_line_color="#00ff9d",decreasing_line_color="#ff4d6d"),row=1,col=1)
    for ma,color in [("ma7","#ffd60a"),("ma20","#0ea5e9"),("ma50","#a78bfa")]:
        if ma in df.columns and df[ma].notna().any():
            fig.add_trace(go.Scatter(x=df.index,y=df[ma],name=ma.upper(),line=dict(color=color,width=1.2,dash="dot"),opacity=0.8),row=1,col=1)
    if "bb_upper" in df.columns:
        fig.add_trace(go.Scatter(x=df.index,y=df["bb_upper"],name="BB+",line=dict(color="#0ea5e9",width=1,dash="dash"),opacity=0.5),row=1,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df["bb_lower"],name="BB-",line=dict(color="#a78bfa",width=1,dash="dash"),fill="tonexty",fillcolor="rgba(14,165,233,0.05)",opacity=0.5),row=1,col=1)
    colors_vol=["#00ff9d" if c>=o else "#ff4d6d" for c,o in zip(df["close"],df["open"])]
    fig.add_trace(go.Bar(x=df.index,y=df["volume"],name="Volumen",marker_color=colors_vol,opacity=0.6),row=2,col=1)
    if "macd" in df.columns:
        fig.add_trace(go.Scatter(x=df.index,y=df["macd"],name="MACD",line=dict(color="#0ea5e9",width=1.5)),row=3,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df["macd_signal"],name="Signal",line=dict(color="#ffd60a",width=1.5)),row=3,col=1)
        ch=["#00ff9d" if v>=0 else "#ff4d6d" for v in df["macd_hist"].fillna(0)]
        fig.add_trace(go.Bar(x=df.index,y=df["macd_hist"],name="Histograma",marker_color=ch,opacity=0.7),row=3,col=1)
    fig.update_layout(template="plotly_dark",plot_bgcolor="#0d1117",paper_bgcolor="#0d1117",
        font=dict(family="Space Mono",color="#9ca3af",size=10),
        legend=dict(bgcolor="#0d1117",bordercolor="#1f2937",borderwidth=1,orientation="h",y=1.02),
        margin=dict(l=0,r=0,t=40,b=0),height=550,
        title=dict(text=f"  {symbol} — Análisis Técnico Completo",font=dict(color="#fff",size=14)),
        xaxis_rangeslider_visible=False)
    for i in [1,2,3]:
        fig.update_xaxes(gridcolor="#1f2937",row=i,col=1)
        fig.update_yaxes(gridcolor="#1f2937",row=i,col=1)
    return fig

def build_multi_tf(symbol):
    configs=[("5d","1h","5 Días (1h)"),("1mo","1d","1 Mes (1d)"),("6mo","1wk","6 Meses (1sem)"),("5y","1mo","5 Años (1mes)")]
    fig=make_subplots(rows=2,cols=2,subplot_titles=[c[2] for c in configs],vertical_spacing=0.12,horizontal_spacing=0.05)
    pos=[(1,1),(1,2),(2,1),(2,2)]; pal=["#00ff9d","#0ea5e9","#ffd60a","#a78bfa"]
    for idx,(period,interval,label) in enumerate(configs):
        r,c=pos[idx]; df=fetch_data(symbol,period,interval)
        if df.empty: continue
        df=add_indicators(df); col=pal[idx]
        rgb=tuple(int(col[i:i+2],16) for i in (1,3,5))
        fig.add_trace(go.Scatter(x=df.index,y=df["close"],name=label,
            line=dict(color=col,width=1.8),fill="tozeroy",fillcolor=f"rgba({rgb[0]},{rgb[1]},{rgb[2]},0.08)"),row=r,col=c)
        if "ma20" in df.columns and df["ma20"].notna().any():
            fig.add_trace(go.Scatter(x=df.index,y=df["ma20"],line=dict(color="#ffd60a",width=1,dash="dot"),showlegend=False),row=r,col=c)
        fig.update_xaxes(gridcolor="#1f2937",row=r,col=c)
        fig.update_yaxes(gridcolor="#1f2937",row=r,col=c)
    fig.update_layout(template="plotly_dark",plot_bgcolor="#0d1117",paper_bgcolor="#0d1117",
        font=dict(family="Space Mono",color="#9ca3af",size=10),height=520,
        margin=dict(l=0,r=0,t=40,b=0),showlegend=False)
    return fig

def build_rsi_bb(df):
    fig=make_subplots(rows=2,cols=1,shared_xaxes=True,row_heights=[0.5,0.5],
        subplot_titles=["RSI (14 períodos)","Bandas de Bollinger"])
    if "rsi" in df.columns:
        fig.add_trace(go.Scatter(x=df.index,y=df["rsi"],name="RSI",line=dict(color="#ffd60a",width=2)),row=1,col=1)
        fig.add_hline(y=70,line_dash="dash",line_color="#ff4d6d",opacity=0.7,row=1,col=1)
        fig.add_hline(y=30,line_dash="dash",line_color="#00ff9d",opacity=0.7,row=1,col=1)
        fig.add_hrect(y0=0,y1=30,fillcolor="#00ff9d",opacity=0.05,row=1,col=1)
        fig.add_hrect(y0=70,y1=100,fillcolor="#ff4d6d",opacity=0.05,row=1,col=1)
    if "bb_upper" in df.columns:
        fig.add_trace(go.Scatter(x=df.index,y=df["close"],name="Precio",line=dict(color="#fff",width=1.5)),row=2,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df["bb_upper"],name="BB+",line=dict(color="#0ea5e9",width=1,dash="dot")),row=2,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df["bb_mid"],name="BB mid",line=dict(color="#9ca3af",width=1,dash="dot")),row=2,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df["bb_lower"],name="BB-",line=dict(color="#a78bfa",width=1,dash="dot"),
            fill="tonexty",fillcolor="rgba(14,165,233,0.06)"),row=2,col=1)
    fig.update_layout(template="plotly_dark",plot_bgcolor="#0d1117",paper_bgcolor="#0d1117",
        font=dict(family="Space Mono",color="#9ca3af",size=10),height=480,
        margin=dict(l=0,r=0,t=40,b=0),
        legend=dict(bgcolor="#0d1117",bordercolor="#1f2937",borderwidth=1,orientation="h",y=1.02))
    for i in [1,2]:
        fig.update_xaxes(gridcolor="#1f2937",row=i,col=1)
        fig.update_yaxes(gridcolor="#1f2937",row=i,col=1)
    return fig

# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:16px 0 8px;'>
        <div style='font-size:36px'>📈</div>
        <div style='color:#fff;font-family:Space Mono;font-weight:700;font-size:16px;letter-spacing:2px;'>QUANTUM TRADE</div>
        <div style='color:#4b5563;font-size:9px;letter-spacing:3px;'>AI STOCK ANALYTICS</div>
    </div><hr style='border-color:#1f2937;margin:8px 0 16px;'>
    """, unsafe_allow_html=True)
    symbol   = st.selectbox("🎯 Selecciona Acción",list(TOP_STOCKS.keys()),format_func=lambda x:f"{x} — {TOP_STOCKS[x]['name']}")
    portfolio= st.number_input("💰 Capital disponible (USD)",min_value=100,max_value=10_000_000,value=10_000,step=500)
    st.markdown("<div style='color:#4b5563;font-size:9px;letter-spacing:2px;text-transform:uppercase;margin-top:12px;'>Parámetros Kelly</div>",unsafe_allow_html=True)
    win_rate = st.slider("Win Rate (%)",40,70,55)/100
    avg_win  = st.slider("Beneficio promedio (x)",1.0,3.0,1.5,0.1)
    avg_loss = st.slider("Pérdida promedio (x)",0.5,2.0,1.0,0.1)
    auto_ref = st.checkbox("🔄 Auto-refresh (60s)",value=False)
    if st.button("↻  Actualizar datos"):
        st.cache_data.clear(); st.rerun()
    st.markdown("<hr style='border-color:#1f2937;margin:16px 0 8px;'><div style='color:#4b5563;font-size:9px;line-height:1.7;'>Datos: Yahoo Finance · TTL: 60s<br>Modelos: MA · RSI · MACD · Bollinger · Kelly</div>",unsafe_allow_html=True)

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
with st.spinner(f"Cargando {symbol}..."):
    df_1d = fetch_data(symbol,"1y","1d")
    df_1h = fetch_data(symbol,"5d","1h")

if df_1d.empty:
    st.error("No se pudo cargar el dato. Verifica tu conexión a internet.")
    st.stop()

df_1d=add_indicators(df_1d)
df_1h=add_indicators(df_1h) if not df_1h.empty else df_1d
sig=generate_signal(df_1d)
kelly_pct=kelly_criterion(win_rate,avg_win,avg_loss)
invest_amt=portfolio*kelly_pct
last=df_1d.iloc[-1]; prev=df_1d.iloc[-2]
price_now=last["close"]; price_chg=((price_now-prev["close"])/prev["close"])*100

# ── HEADER ────────────────────────────────────────────────────────────────────
sc=sig["color"]
st.markdown(f"""
<div style='background:#0d1117;border:1px solid #1f2937;border-radius:10px;padding:20px 24px;margin-bottom:16px;'>
<div style='display:flex;justify-content:space-between;align-items:center;'>
  <div>
    <div style='display:flex;align-items:center;gap:12px;'>
      <span style='color:#fff;font-family:Space Mono;font-weight:700;font-size:24px;'>{symbol}</span>
      <span style='color:#6b7280;font-size:14px;'>{TOP_STOCKS[symbol]['name']}</span>
      <span style='background:#1f2937;color:#9ca3af;padding:2px 8px;border-radius:3px;font-size:10px;'>{TOP_STOCKS[symbol]['sector']}</span>
    </div>
    <div style='display:flex;align-items:baseline;gap:12px;margin-top:4px;'>
      <span style='color:#fff;font-family:Space Mono;font-size:34px;font-weight:700;'>${price_now:,.2f}</span>
      <span style='color:{"#00ff9d" if price_chg>=0 else "#ff4d6d"};font-family:Space Mono;font-size:16px;'>
        {"▲" if price_chg>=0 else "▼"} {abs(price_chg):.2f}%
      </span>
    </div>
  </div>
  <div style='text-align:right;'>
    <div style='background:{sc}20;border:1px solid {sc};color:{sc};padding:10px 24px;border-radius:6px;
                font-family:Space Mono;font-size:20px;font-weight:700;letter-spacing:2px;'>
      {"🟢" if sig["signal"]=="COMPRAR" else "🔴" if sig["signal"]=="VENDER" else "🟡"} {sig["signal"]}
    </div>
    <div style='color:#6b7280;font-size:11px;margin-top:6px;'>Fuerza: {sig["strength"]}%</div>
  </div>
</div>
</div>
""", unsafe_allow_html=True)

# ── METRICS ───────────────────────────────────────────────────────────────────
c1,c2,c3,c4,c5,c6=st.columns(6)
rsi_v=last.get("rsi",50)
c1.metric("RSI (14)",f"{rsi_v:.1f}","Sobrevendido" if rsi_v<30 else ("Sobrecomprado" if rsi_v>70 else "Neutral"))
c2.metric("MA 20",f"${last.get('ma20',0):,.2f}")
c3.metric("MA 50",f"${last.get('ma50',0):,.2f}")
c4.metric("BB Superior",f"${last.get('bb_upper',0):,.2f}")
c5.metric("Kelly %",f"{kelly_pct*100:.1f}%","Óptimo según modelo")
c6.metric("💰 Invertir",f"${invest_amt:,.0f}",f"{kelly_pct*100:.1f}% de ${portfolio:,.0f}")

st.markdown("<br>",unsafe_allow_html=True)

# ── SESSION STATE para portafolio personal ────────────────────────────────────
if "trades" not in st.session_state:
    st.session_state.trades = []  # lista de dicts con info de cada operación

def add_trade(symbol, buy_price, shares, buy_date, tp_pct, sl_pct, notes):
    st.session_state.trades.append({
        "id": len(st.session_state.trades),
        "symbol": symbol,
        "buy_price": buy_price,
        "shares": shares,
        "invested": buy_price * shares,
        "buy_date": str(buy_date),
        "tp_price": round(buy_price * (1 + tp_pct/100), 2),
        "sl_price": round(buy_price * (1 - sl_pct/100), 2),
        "tp_pct": tp_pct,
        "sl_pct": sl_pct,
        "notes": notes,
        "status": "ABIERTA",
        "sell_price": None,
        "sell_date": None,
    })

def close_trade(idx, sell_price, sell_date):
    t = st.session_state.trades[idx]
    t["sell_price"] = sell_price
    t["sell_date"] = str(sell_date)
    pnl = (sell_price - t["buy_price"]) * t["shares"]
    t["status"] = "GANANCIA ✅" if pnl >= 0 else "PÉRDIDA ❌"
    t["pnl"] = round(pnl, 2)
    t["pnl_pct"] = round((sell_price - t["buy_price"]) / t["buy_price"] * 100, 2)

# ── TABS ──────────────────────────────────────────────────────────────────────
t1,t2,t3,t4,t5,t6=st.tabs(["📊  Gráfica Principal","📅  Multi-Período","⚡  RSI & Bollinger","🧮  Análisis & Señal","💼  Mis Inversiones","🏦  Brokers"])

with t1:
    df_show=df_1h if not df_1h.empty else df_1d
    st.plotly_chart(build_main_chart(df_show,symbol),use_container_width=True)

with t2:
    st.plotly_chart(build_multi_tf(symbol),use_container_width=True)
    st.markdown("<div style='background:#0d1117;border:1px solid #1f2937;border-radius:8px;padding:12px 16px;font-size:11px;color:#6b7280;'>💡 <strong style='color:#9ca3af;'>Intersección de tendencias:</strong> Cuando todos los marcos temporales muestran la misma dirección, la señal es más confiable. Una divergencia entre marcos cortos y largos indica indecisión.</div>",unsafe_allow_html=True)

with t3:
    st.plotly_chart(build_rsi_bb(df_1d),use_container_width=True)

with t4:
    cl,cr=st.columns(2)
    with cl:
        st.markdown("### 📋 Señales Detectadas")
        for r in sig["reasons"]:
            color="#00ff9d" if "✅" in r else ("#ff4d6d" if "❌" in r else "#9ca3af")
            st.markdown(f"<div style='color:{color};font-size:12px;padding:4px 0;font-family:Space Mono;'>{r}</div>",unsafe_allow_html=True)
        s=sig["strength"]
        st.markdown(f"""<div style='margin-top:16px;'>
        <div style='color:#4b5563;font-size:9px;letter-spacing:2px;text-transform:uppercase;margin-bottom:6px;'>FUERZA DE SEÑAL</div>
        <div style='background:#1f2937;border-radius:4px;height:8px;width:100%;'>
          <div style='background:{sig["color"]};border-radius:4px;height:8px;width:{s}%;'></div>
        </div>
        <div style='color:{sig["color"]};font-family:Space Mono;font-size:20px;font-weight:700;margin-top:6px;'>{s}%</div>
        </div>""",unsafe_allow_html=True)
    with cr:
        st.markdown("### 🧮 Criterio de Kelly")
        ic=("#00ff9d" if sig["signal"]=="COMPRAR" else "#ff4d6d" if sig["signal"]=="VENDER" else "#ffd60a")
        st.markdown(f"""<div style='background:#0d1117;border:1px solid #1f2937;border-radius:10px;padding:20px;'>
        <div style='background:#060a0f;border:1px solid #1f2937;border-radius:6px;padding:12px;
                    font-family:Space Mono;font-size:13px;color:#9ca3af;margin-bottom:16px;'>
          f* = W − (1−W) / B<br>
          <span style='font-size:10px;color:#4b5563;'>W={win_rate:.0%} win rate · B={avg_win/avg_loss:.2f} ratio beneficio/pérdida</span>
        </div>
        <div style='text-align:center;'>
          <div style='color:#ffd60a;font-family:Space Mono;font-size:42px;font-weight:700;'>{kelly_pct*100:.1f}%</div>
          <div style='color:#4b5563;font-size:11px;'>del capital a invertir</div>
          <div style='margin:16px 0;border-top:1px solid #1f2937;padding-top:16px;'>
            <div style='color:#6b7280;font-size:11px;'>Monto sugerido para {symbol}</div>
            <div style='color:{ic};font-family:Space Mono;font-size:28px;font-weight:700;'>${invest_amt:,.2f}</div>
            <div style='color:#4b5563;font-size:10px;'>{kelly_pct*100:.1f}% × ${portfolio:,.0f}</div>
          </div>
        </div></div>""",unsafe_allow_html=True)
        p52h=df_1d["high"].max(); p52l=df_1d["low"].min(); avol=df_1d["volume"].mean()
        st.markdown(f"""<div style='background:#0d1117;border:1px solid #1f2937;border-radius:8px;padding:14px;
                    font-family:Space Mono;font-size:11px;margin-top:12px;'>
        <div style='color:#4b5563;letter-spacing:2px;margin-bottom:8px;font-size:9px;'>ESTADÍSTICAS 52 SEMANAS</div>
        <div style='display:grid;grid-template-columns:1fr 1fr;gap:8px;'>
          <div><span style='color:#4b5563;'>Máximo:</span> <span style='color:#00ff9d;'>${p52h:,.2f}</span></div>
          <div><span style='color:#4b5563;'>Mínimo:</span> <span style='color:#ff4d6d;'>${p52l:,.2f}</span></div>
          <div><span style='color:#4b5563;'>ATR(14):</span> <span style='color:#a78bfa;'>${last.get("atr",0):.2f}</span></div>
          <div><span style='color:#4b5563;'>Vol. prom:</span> <span style='color:#0ea5e9;'>{avol/1e6:.1f}M</span></div>
          <div><span style='color:#4b5563;'>MACD:</span> <span style='color:{"#00ff9d" if last.get("macd",0)>0 else "#ff4d6d"};'>{last.get("macd",0):.3f}</span></div>
          <div><span style='color:#4b5563;'>BB Ancho:</span> <span style='color:#ffd60a;'>${(last.get("bb_upper",0)-last.get("bb_lower",0)):.2f}</span></div>
        </div></div>""",unsafe_allow_html=True)

with t5:
    st.markdown("### 💼 Mis Inversiones — Tracker Personal")
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Proyección del modelo para esta acción ────────────────────────────────
    atr_val = last.get("atr", price_now * 0.02)
    proj_tp  = round(price_now + atr_val * 2.5, 2)   # Take profit sugerido
    proj_sl  = round(price_now - atr_val * 1.5, 2)   # Stop loss sugerido
    proj_tp_pct = round((proj_tp - price_now) / price_now * 100, 1)
    proj_sl_pct = round((price_now - proj_sl) / price_now * 100, 1)
    rr_ratio    = round(proj_tp_pct / proj_sl_pct, 2) if proj_sl_pct > 0 else 0

    # Horizonte temporal proyectado según MACD y MA
    macd_v = last.get("macd", 0)
    if sig["strength"] >= 65:
        horizonte = "Corto plazo (1–5 días)"
        horizonte_color = "#00ff9d"
    elif sig["strength"] >= 50:
        horizonte = "Mediano plazo (1–3 semanas)"
        horizonte_color = "#ffd60a"
    else:
        horizonte = "Esperar mejor entrada"
        horizonte_color = "#ff4d6d"

    st.markdown(f"""
    <div style='background:#0d1117;border:1px solid #1f2937;border-radius:10px;padding:20px;margin-bottom:16px;'>
      <div style='color:#4b5563;font-size:9px;letter-spacing:2px;text-transform:uppercase;margin-bottom:14px;font-family:Space Mono;'>
        📡 PROYECCIÓN DEL MODELO — {symbol} @ ${price_now:,.2f}
      </div>
      <div style='display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px;'>
        <div style='background:#060a0f;border:1px solid #1f2937;border-radius:8px;padding:12px;text-align:center;'>
          <div style='color:#4b5563;font-size:9px;letter-spacing:1px;'>SEÑAL ACTUAL</div>
          <div style='color:{sig["color"]};font-family:Space Mono;font-size:18px;font-weight:700;margin-top:4px;'>{sig["signal"]}</div>
          <div style='color:#4b5563;font-size:10px;'>Fuerza {sig["strength"]}%</div>
        </div>
        <div style='background:#060a0f;border:1px solid #00ff9d30;border-radius:8px;padding:12px;text-align:center;'>
          <div style='color:#4b5563;font-size:9px;letter-spacing:1px;'>TAKE PROFIT 🎯</div>
          <div style='color:#00ff9d;font-family:Space Mono;font-size:18px;font-weight:700;margin-top:4px;'>${proj_tp:,.2f}</div>
          <div style='color:#00ff9d;font-size:10px;'>+{proj_tp_pct}% (ATR×2.5)</div>
        </div>
        <div style='background:#060a0f;border:1px solid #ff4d6d30;border-radius:8px;padding:12px;text-align:center;'>
          <div style='color:#4b5563;font-size:9px;letter-spacing:1px;'>STOP LOSS 🛑</div>
          <div style='color:#ff4d6d;font-family:Space Mono;font-size:18px;font-weight:700;margin-top:4px;'>${proj_sl:,.2f}</div>
          <div style='color:#ff4d6d;font-size:10px;'>-{proj_sl_pct}% (ATR×1.5)</div>
        </div>
        <div style='background:#060a0f;border:1px solid #ffd60a30;border-radius:8px;padding:12px;text-align:center;'>
          <div style='color:#4b5563;font-size:9px;letter-spacing:1px;'>RATIO R/R</div>
          <div style='color:#ffd60a;font-family:Space Mono;font-size:18px;font-weight:700;margin-top:4px;'>{rr_ratio}:1</div>
          <div style='color:{"#00ff9d" if rr_ratio>=1.5 else "#ff4d6d"};font-size:10px;'>{"✅ Favorable" if rr_ratio>=1.5 else "❌ No favorable"}</div>
        </div>
      </div>
      <div style='background:#060a0f;border:1px solid #1f2937;border-radius:6px;padding:10px 14px;display:flex;align-items:center;gap:10px;'>
        <span style='font-size:14px;'>⏱️</span>
        <div>
          <span style='color:#4b5563;font-size:10px;'>HORIZONTE PROYECTADO: </span>
          <span style='color:{horizonte_color};font-family:Space Mono;font-size:11px;font-weight:700;'>{horizonte}</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Formulario para registrar nueva inversión ─────────────────────────────
    with st.expander("➕ Registrar nueva inversión", expanded=len(st.session_state.trades)==0):
        st.markdown("<div style='color:#9ca3af;font-size:12px;margin-bottom:12px;'>Completa los datos de tu operación. El sistema calculará automáticamente el Take Profit y Stop Loss sugeridos.</div>", unsafe_allow_html=True)

        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            trade_symbol = st.selectbox("Acción", list(TOP_STOCKS.keys()),
                index=list(TOP_STOCKS.keys()).index(symbol), key="trade_sym")
            trade_shares = st.number_input("Cantidad de acciones", min_value=1, max_value=10000, value=10, key="trade_sh")
        with fc2:
            trade_buy_price = st.number_input("Precio de compra (USD)", min_value=0.01, value=float(round(price_now, 2)), step=0.01, key="trade_bp")
            trade_buy_date  = st.date_input("Fecha de compra", value=pd.Timestamp.today(), key="trade_bd")
        with fc3:
            trade_tp = st.number_input("Take Profit %", min_value=0.5, max_value=100.0, value=float(proj_tp_pct), step=0.5, key="trade_tp")
            trade_sl = st.number_input("Stop Loss %",   min_value=0.5, max_value=50.0,  value=float(proj_sl_pct), step=0.5, key="trade_sl")

        trade_notes = st.text_input("Notas / Razón de la operación", placeholder="Ej: Cruce MA7>MA20, RSI en 28, rebote en soporte...", key="trade_notes")

        # Preview
        tp_price_prev = round(trade_buy_price * (1 + trade_tp/100), 2)
        sl_price_prev = round(trade_buy_price * (1 - trade_sl/100), 2)
        inv_total     = round(trade_buy_price * trade_shares, 2)
        ganancia_pot  = round((tp_price_prev - trade_buy_price) * trade_shares, 2)
        perdida_pot   = round((trade_buy_price - sl_price_prev) * trade_shares, 2)

        st.markdown(f"""
        <div style='background:#060a0f;border:1px solid #1f2937;border-radius:8px;padding:12px;margin:10px 0;
                    display:grid;grid-template-columns:repeat(5,1fr);gap:8px;font-family:Space Mono;font-size:11px;'>
          <div style='text-align:center;'><div style='color:#4b5563;font-size:9px;'>INVERTIDO</div><div style='color:#fff;'>${inv_total:,.2f}</div></div>
          <div style='text-align:center;'><div style='color:#4b5563;font-size:9px;'>TP PRECIO</div><div style='color:#00ff9d;'>${tp_price_prev:,.2f}</div></div>
          <div style='text-align:center;'><div style='color:#4b5563;font-size:9px;'>SL PRECIO</div><div style='color:#ff4d6d;'>${sl_price_prev:,.2f}</div></div>
          <div style='text-align:center;'><div style='color:#4b5563;font-size:9px;'>GANANCIA POT.</div><div style='color:#00ff9d;'>+${ganancia_pot:,.2f}</div></div>
          <div style='text-align:center;'><div style='color:#4b5563;font-size:9px;'>PÉRDIDA POT.</div><div style='color:#ff4d6d;'>-${perdida_pot:,.2f}</div></div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("✅ Registrar Inversión", key="btn_add_trade"):
            if trade_shares > 0 and trade_buy_price > 0:
                add_trade(trade_symbol, trade_buy_price, trade_shares, trade_buy_date, trade_tp, trade_sl, trade_notes)
                st.success(f"✅ Inversión en {trade_symbol} registrada correctamente.")
                st.rerun()

    # ── Tabla de operaciones ──────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)

    open_trades  = [t for t in st.session_state.trades if t["status"] == "ABIERTA"]
    closed_trades= [t for t in st.session_state.trades if t["status"] != "ABIERTA"]

    if not st.session_state.trades:
        st.markdown("""
        <div style='background:#0d1117;border:1px dashed #1f2937;border-radius:10px;padding:40px;text-align:center;'>
          <div style='font-size:32px;margin-bottom:8px;'>📂</div>
          <div style='color:#4b5563;font-family:Space Mono;font-size:12px;'>No hay operaciones registradas todavía.</div>
          <div style='color:#374151;font-size:11px;margin-top:4px;'>Usa el formulario de arriba para registrar tu primera inversión.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # ── Resumen global ────────────────────────────────────────────────────
        total_invested = sum(t["invested"] for t in st.session_state.trades)
        total_pnl      = sum(t.get("pnl", 0) for t in closed_trades)
        open_exposure  = sum(t["invested"] for t in open_trades)

        sm1, sm2, sm3, sm4 = st.columns(4)
        sm1.metric("Total Invertido",  f"${total_invested:,.2f}")
        sm2.metric("Posiciones Abiertas", str(len(open_trades)))
        sm3.metric("Operaciones Cerradas", str(len(closed_trades)))
        sm4.metric("P&L Realizado", f"${total_pnl:+,.2f}", delta="ganancia" if total_pnl>=0 else "pérdida")
        st.markdown("<br>", unsafe_allow_html=True)

        # ── Posiciones abiertas con estado en tiempo real ─────────────────────
        if open_trades:
            st.markdown("#### 🟢 Posiciones Abiertas")
            for i, trade in enumerate(open_trades):
                orig_idx = st.session_state.trades.index(trade)
                # Intentar obtener precio actual
                try:
                    cur_price_data = fetch_data(trade["symbol"], "1d", "1h")
                    cur_price = cur_price_data["close"].iloc[-1] if not cur_price_data.empty else trade["buy_price"]
                except:
                    cur_price = trade["buy_price"]

                unreal_pnl = round((cur_price - trade["buy_price"]) * trade["shares"], 2)
                unreal_pct = round((cur_price - trade["buy_price"]) / trade["buy_price"] * 100, 2)
                pnl_color  = "#00ff9d" if unreal_pnl >= 0 else "#ff4d6d"

                # Estado respecto a TP / SL
                if cur_price >= trade["tp_price"]:
                    alert_msg   = "🎯 ¡TAKE PROFIT ALCANZADO! Considera vender."
                    alert_color = "#00ff9d"
                    alert_bg    = "#00ff9d15"
                elif cur_price <= trade["sl_price"]:
                    alert_msg   = "🛑 STOP LOSS ALCANZADO. Evalúa cerrar posición."
                    alert_color = "#ff4d6d"
                    alert_bg    = "#ff4d6d15"
                elif unreal_pct >= trade["tp_pct"] * 0.7:
                    alert_msg   = "⚡ Cerca del Take Profit. Mantente atento."
                    alert_color = "#ffd60a"
                    alert_bg    = "#ffd60a10"
                else:
                    alert_msg   = "⏳ Posición activa. Sin señal de salida todavía."
                    alert_color = "#4b5563"
                    alert_bg    = "#1f293710"

                # Progreso hacia TP y SL
                range_total = trade["tp_price"] - trade["sl_price"]
                progress    = max(0, min(1, (cur_price - trade["sl_price"]) / range_total)) if range_total > 0 else 0.5

                st.markdown(f"""
                <div style='background:#0d1117;border:1px solid #1f2937;border-radius:10px;padding:18px;margin-bottom:12px;'>
                  <div style='display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;'>
                    <div>
                      <span style='color:#fff;font-family:Space Mono;font-weight:700;font-size:16px;'>{trade["symbol"]}</span>
                      <span style='color:#4b5563;font-size:11px;margin-left:10px;'>{trade["shares"]} acciones · compradas el {trade["buy_date"]}</span>
                      {f'<div style="color:#6b7280;font-size:10px;margin-top:2px;font-style:italic;">{trade["notes"]}</div>' if trade["notes"] else ""}
                    </div>
                    <div style='text-align:right;'>
                      <div style='color:#fff;font-family:Space Mono;font-size:18px;font-weight:700;'>${cur_price:,.2f}</div>
                      <div style='color:{pnl_color};font-family:Space Mono;font-size:13px;'>{unreal_pct:+.2f}% ({unreal_pnl:+,.2f} USD)</div>
                    </div>
                  </div>
                  <div style='display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:12px;font-family:Space Mono;font-size:10px;'>
                    <div style='background:#060a0f;border-radius:6px;padding:8px;text-align:center;'>
                      <div style='color:#4b5563;font-size:9px;'>COMPRA</div>
                      <div style='color:#9ca3af;'>${trade["buy_price"]:,.2f}</div>
                    </div>
                    <div style='background:#060a0f;border:1px solid #00ff9d30;border-radius:6px;padding:8px;text-align:center;'>
                      <div style='color:#4b5563;font-size:9px;'>TAKE PROFIT 🎯</div>
                      <div style='color:#00ff9d;'>${trade["tp_price"]:,.2f} (+{trade["tp_pct"]}%)</div>
                    </div>
                    <div style='background:#060a0f;border:1px solid #ff4d6d30;border-radius:6px;padding:8px;text-align:center;'>
                      <div style='color:#4b5563;font-size:9px;'>STOP LOSS 🛑</div>
                      <div style='color:#ff4d6d;'>${trade["sl_price"]:,.2f} (-{trade["sl_pct"]}%)</div>
                    </div>
                    <div style='background:#060a0f;border-radius:6px;padding:8px;text-align:center;'>
                      <div style='color:#4b5563;font-size:9px;'>INVERTIDO</div>
                      <div style='color:#9ca3af;'>${trade["invested"]:,.2f}</div>
                    </div>
                  </div>
                  <div style='margin-bottom:10px;'>
                    <div style='display:flex;justify-content:space-between;font-size:9px;color:#4b5563;margin-bottom:4px;'>
                      <span>SL ${trade["sl_price"]:,.2f}</span>
                      <span>Precio actual ${cur_price:,.2f}</span>
                      <span>TP ${trade["tp_price"]:,.2f}</span>
                    </div>
                    <div style='background:#1f2937;border-radius:4px;height:6px;position:relative;'>
                      <div style='background:linear-gradient(90deg,#ff4d6d,#ffd60a,#00ff9d);border-radius:4px;height:6px;width:100%;opacity:0.3;'></div>
                      <div style='position:absolute;top:-3px;left:{progress*100:.1f}%;transform:translateX(-50%);
                                  width:12px;height:12px;background:#fff;border-radius:50%;border:2px solid #0d1117;'></div>
                    </div>
                  </div>
                  <div style='background:{alert_bg};border:1px solid {alert_color}40;border-radius:6px;padding:8px 12px;font-size:11px;color:{alert_color};'>
                    {alert_msg}
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # Botón de cerrar posición
                with st.expander(f"💰 Cerrar posición {trade['symbol']} #{i+1}"):
                    sc1, sc2 = st.columns(2)
                    with sc1:
                        sell_p = st.number_input("Precio de venta (USD)", min_value=0.01, value=float(round(cur_price,2)), step=0.01, key=f"sell_p_{orig_idx}")
                    with sc2:
                        sell_d = st.date_input("Fecha de venta", value=pd.Timestamp.today(), key=f"sell_d_{orig_idx}")
                    pnl_preview = round((sell_p - trade["buy_price"]) * trade["shares"], 2)
                    pnl_pct_preview = round((sell_p - trade["buy_price"]) / trade["buy_price"] * 100, 2)
                    st.markdown(f"""
                    <div style='background:#060a0f;border:1px solid #1f2937;border-radius:6px;padding:10px;
                                font-family:Space Mono;font-size:12px;margin:8px 0;text-align:center;'>
                      P&L: <span style='color:{"#00ff9d" if pnl_preview>=0 else "#ff4d6d"};font-size:16px;font-weight:700;'>
                        {pnl_preview:+,.2f} USD ({pnl_pct_preview:+.2f}%)
                      </span>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Confirmar cierre de {trade['symbol']}", key=f"close_{orig_idx}"):
                        close_trade(orig_idx, sell_p, sell_d)
                        st.success("Posición cerrada correctamente.")
                        st.rerun()

        # ── Historial de operaciones cerradas ─────────────────────────────────
        if closed_trades:
            st.markdown("<br>#### 📋 Historial de Operaciones Cerradas")
            rows = []
            for t in closed_trades:
                rows.append({
                    "Acción": t["symbol"],
                    "Compra": f"${t['buy_price']:,.2f}",
                    "Venta": f"${t['sell_price']:,.2f}",
                    "Acciones": t["shares"],
                    "Invertido": f"${t['invested']:,.2f}",
                    "P&L": f"${t.get('pnl',0):+,.2f}",
                    "Rendimiento": f"{t.get('pnl_pct',0):+.2f}%",
                    "Estado": t["status"],
                    "Comprado": t["buy_date"],
                    "Vendido": t["sell_date"],
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            # Gráfico P&L histórico
            if len(closed_trades) > 1:
                pnl_vals  = [t.get("pnl", 0) for t in closed_trades]
                pnl_syms  = [f"{t['symbol']} {t['sell_date']}" for t in closed_trades]
                pnl_cum   = pd.Series(pnl_vals).cumsum().tolist()
                fig_pnl = go.Figure()
                fig_pnl.add_trace(go.Bar(x=pnl_syms, y=pnl_vals, name="P&L por operación",
                    marker_color=["#00ff9d" if v>=0 else "#ff4d6d" for v in pnl_vals]))
                fig_pnl.add_trace(go.Scatter(x=pnl_syms, y=pnl_cum, name="P&L acumulado",
                    line=dict(color="#ffd60a", width=2), mode="lines+markers"))
                fig_pnl.update_layout(template="plotly_dark", plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
                    font=dict(family="Space Mono", color="#9ca3af", size=10),
                    height=280, margin=dict(l=0,r=0,t=30,b=0),
                    title=dict(text="Historial de P&L", font=dict(color="#fff",size=13)),
                    legend=dict(bgcolor="#0d1117",bordercolor="#1f2937",borderwidth=1))
                fig_pnl.update_xaxes(gridcolor="#1f2937"); fig_pnl.update_yaxes(gridcolor="#1f2937")
                st.plotly_chart(fig_pnl, use_container_width=True)

        # Botón para limpiar todo
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️  Borrar todo el historial"):
            st.session_state.trades = []
            st.rerun()

with t6:
    st.markdown("### 🏦 Brokers Recomendados para Invertir")
    st.markdown("<br>",unsafe_allow_html=True)
    cols=st.columns(3); pal=["#00ff9d","#0ea5e9","#ffd60a","#a78bfa","#f97316","#ec4899"]
    for i,b in enumerate(BROKERS):
        with cols[i%3]:
            c=pal[i]
            stars="".join([f'<span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:{""+c if j<int(b["rating"]) else "#1f2937"};margin-right:2px;"></span>' for j in range(10)])
            st.markdown(f"""<div style='background:#0d1117;border:1px solid #1f2937;border-top:3px solid {c};
                border-radius:10px;padding:18px;margin-bottom:16px;'>
              <div style='display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;'>
                <div><div style='color:#fff;font-weight:600;font-size:14px;'>{b["name"]}</div>
                <div style='color:#4b5563;font-size:10px;margin-top:2px;'>{b["url"]}</div></div>
                <div style='color:{c};font-family:Space Mono;font-size:18px;font-weight:700;'>{b["rating"]}</div>
              </div>
              <div style='color:#9ca3af;font-size:11px;margin-bottom:10px;'>{b["ideal"]}</div>
              <div style='display:flex;justify-content:space-between;font-size:10px;margin-bottom:8px;'>
                <span style='color:#00ff9d;font-family:Space Mono;'>💰 {b["fee"]}</span>
                <span style='color:#4b5563;'>🌍 {b["access"]}</span>
              </div>
              <div>{stars}</div>
            </div>""",unsafe_allow_html=True)
    st.markdown("""<div style='background:#0d1117;border:1px solid #ffd60a40;border-radius:10px;padding:16px;margin-top:8px;'>
    <div style='color:#ffd60a;font-size:12px;font-weight:600;margin-bottom:8px;'>⚠️ Aviso Legal Importante</div>
    <div style='color:#6b7280;font-size:11px;line-height:1.8;'>Este dashboard es una <strong style='color:#9ca3af;'>herramienta educativa de análisis técnico</strong>.
    Las señales son generadas por algoritmos y <strong style='color:#ff4d6d;'>no garantizan rentabilidad ni constituyen asesoría financiera</strong>.
    Toda inversión conlleva riesgo de pérdida. Consulta con un asesor certificado antes de invertir.</div>
    </div>""",unsafe_allow_html=True)

if auto_ref:
    time.sleep(60); st.rerun()
