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

# ── TABS ──────────────────────────────────────────────────────────────────────
t1,t2,t3,t4,t5=st.tabs(["📊  Gráfica Principal","📅  Multi-Período","⚡  RSI & Bollinger","🧮  Análisis & Señal","🏦  Brokers"])

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
