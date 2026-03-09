import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
from datetime import datetime

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
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
.main .block-container{padding-top:1rem;max-width:1440px;}
section[data-testid="stSidebar"]{background:#0d1117!important;border-right:1px solid #1f2937;}
div[data-testid="metric-container"]{background:#0d1117;border:1px solid #1f2937;border-radius:8px;padding:12px 16px;}
div[data-testid="metric-container"] label{color:#6b7280!important;font-size:10px!important;letter-spacing:1.5px;text-transform:uppercase;font-family:'Space Mono',monospace!important;}
div[data-testid="metric-container"] div[data-testid="stMetricValue"]{color:#00ff9d!important;font-family:'Space Mono',monospace!important;font-size:20px!important;}
.stSelectbox>div>div{background:#0d1117!important;border-color:#1f2937!important;color:#e5e7eb!important;}
.stNumberInput input{background:#0d1117!important;border-color:#1f2937!important;color:#00ff9d!important;font-family:'Space Mono',monospace!important;}
.stTextInput input{background:#0d1117!important;border-color:#1f2937!important;color:#e5e7eb!important;}
.stButton button{background:#1f2937!important;border:1px solid #374151!important;color:#9ca3af!important;font-family:'Space Mono',monospace!important;font-size:11px!important;letter-spacing:1px;}
.stButton button:hover{border-color:#00ff9d!important;color:#00ff9d!important;}
h1,h2,h3{color:#ffffff!important;font-family:'Space Mono',monospace!important;}
.stTabs [data-baseweb="tab-list"]{background:#0d1117;border-bottom:1px solid #1f2937;}
.stTabs [data-baseweb="tab"]{background:transparent!important;color:#4b5563!important;font-family:'Space Mono',monospace!important;font-size:11px!important;letter-spacing:1px;border-bottom:2px solid transparent!important;}
.stTabs [aria-selected="true"]{color:#00ff9d!important;border-bottom:2px solid #00ff9d!important;}
div[data-testid="stExpander"]{background:#0d1117!important;border:1px solid #1f2937!important;border-radius:8px!important;}
</style>
""", unsafe_allow_html=True)

# ─── ACCIONES AMPLIADAS ───────────────────────────────────────────────────────
ALL_STOCKS = {
    # 🔵 Tecnología (alta rentabilidad histórica)
    "AAPL":  {"name":"Apple Inc.",          "sector":"Tecnología",   "riesgo":"Bajo",   "min_usd":1,   "desc":"La empresa más valiosa del mundo. Ideal para empezar.",         "dividendo":False},
    "MSFT":  {"name":"Microsoft Corp.",     "sector":"Tecnología",   "riesgo":"Bajo",   "min_usd":1,   "desc":"Nube Azure + IA. Crecimiento estable y constante.",              "dividendo":True},
    "GOOGL": {"name":"Alphabet (Google)",   "sector":"Tecnología",   "riesgo":"Bajo",   "min_usd":1,   "desc":"Dominio absoluto en búsquedas y publicidad digital.",            "dividendo":False},
    "NVDA":  {"name":"NVIDIA Corp.",        "sector":"Tecnología",   "riesgo":"Medio",  "min_usd":1,   "desc":"Chips de IA. Alto crecimiento pero también alta volatilidad.",    "dividendo":False},
    "META":  {"name":"Meta Platforms",      "sector":"Tecnología",   "riesgo":"Medio",  "min_usd":1,   "desc":"Facebook + Instagram + WhatsApp. Publicidad global.",            "dividendo":False},
    "AMZN":  {"name":"Amazon.com",          "sector":"Tecnología",   "riesgo":"Medio",  "min_usd":1,   "desc":"E-commerce + AWS cloud. Líder indiscutible.",                    "dividendo":False},
    "TSLA":  {"name":"Tesla Inc.",          "sector":"Automotriz",   "riesgo":"Alto",   "min_usd":1,   "desc":"Vehículos eléctricos. Muy volátil pero con alto potencial.",      "dividendo":False},
    "ORCL":  {"name":"Oracle Corp.",        "sector":"Tecnología",   "riesgo":"Bajo",   "min_usd":1,   "desc":"Bases de datos y nube empresarial. Estable y con dividendo.",    "dividendo":True},
    "ADBE":  {"name":"Adobe Inc.",          "sector":"Tecnología",   "riesgo":"Medio",  "min_usd":1,   "desc":"Software creativo. Photoshop, Acrobat. Modelo por suscripción.", "dividendo":False},
    "CRM":   {"name":"Salesforce",          "sector":"Tecnología",   "riesgo":"Medio",  "min_usd":1,   "desc":"CRM empresarial #1 del mundo. Crecimiento en IA.",               "dividendo":False},
    # 💰 Finanzas (estables, muchos pagan dividendo)
    "JPM":   {"name":"JPMorgan Chase",      "sector":"Finanzas",     "riesgo":"Bajo",   "min_usd":1,   "desc":"Banco más grande de EEUU. Dividendo confiable.",                "dividendo":True},
    "V":     {"name":"Visa Inc.",           "sector":"Finanzas",     "riesgo":"Bajo",   "min_usd":1,   "desc":"Red de pagos global. Sin riesgo de crédito directo.",           "dividendo":True},
    "MA":    {"name":"Mastercard",          "sector":"Finanzas",     "riesgo":"Bajo",   "min_usd":1,   "desc":"Competidor directo de Visa. Igual de estable y rentable.",      "dividendo":True},
    "BRK-B": {"name":"Berkshire Hathaway",  "sector":"Finanzas",     "riesgo":"Bajo",   "min_usd":1,   "desc":"El portafolio de Warren Buffett. Diversificación automática.",  "dividendo":False},
    "GS":    {"name":"Goldman Sachs",       "sector":"Finanzas",     "riesgo":"Medio",  "min_usd":1,   "desc":"Banco de inversión élite. Buen rendimiento histórico.",         "dividendo":True},
    # 🏥 Salud (defensivo, baja correlación con crisis)
    "JNJ":   {"name":"Johnson & Johnson",   "sector":"Salud",        "riesgo":"Bajo",   "min_usd":1,   "desc":"50+ años aumentando dividendo. Ideal para largo plazo.",        "dividendo":True},
    "UNH":   {"name":"UnitedHealth",        "sector":"Salud",        "riesgo":"Bajo",   "min_usd":1,   "desc":"Seguro médico más grande de EEUU. Muy estable.",               "dividendo":True},
    "PFE":   {"name":"Pfizer Inc.",         "sector":"Salud",        "riesgo":"Medio",  "min_usd":1,   "desc":"Farmacéutica gigante. Precio deprimido = oportunidad.",         "dividendo":True},
    # 🛒 Consumo (resisten recesiones)
    "WMT":   {"name":"Walmart Inc.",        "sector":"Consumo",      "riesgo":"Bajo",   "min_usd":1,   "desc":"Retailer #1 del mundo. La gente compra en crisis o no.",        "dividendo":True},
    "COST":  {"name":"Costco Wholesale",    "sector":"Consumo",      "riesgo":"Bajo",   "min_usd":1,   "desc":"Membresías = ingresos recurrentes. Clientes muy fieles.",       "dividendo":True},
    "KO":    {"name":"Coca-Cola Co.",       "sector":"Consumo",      "riesgo":"Bajo",   "min_usd":1,   "desc":"60+ años aumentando dividendo. Clásico de Buffett.",           "dividendo":True},
    "MCD":   {"name":"McDonald's Corp.",    "sector":"Consumo",      "riesgo":"Bajo",   "min_usd":1,   "desc":"Franquicias = modelo de negocio casi perfecto.",               "dividendo":True},
    # ⚡ Energía y commodities
    "XOM":   {"name":"ExxonMobil",          "sector":"Energía",      "riesgo":"Medio",  "min_usd":1,   "desc":"Petróleo gigante. Dividendo histórico muy confiable.",         "dividendo":True},
    "NEE":   {"name":"NextEra Energy",      "sector":"Energía",      "riesgo":"Bajo",   "min_usd":1,   "desc":"Energía renovable #1. El futuro de la electricidad.",          "dividendo":True},
    # 📦 ETFs (diversificación total, perfectos para principiantes)
    "SPY":   {"name":"S&P 500 ETF",         "sector":"ETF",          "riesgo":"Bajo",   "min_usd":1,   "desc":"Las 500 mejores empresas de EEUU en 1 solo activo. RECOMENDADO PRINCIPIANTES.", "dividendo":True},
    "QQQ":   {"name":"Nasdaq 100 ETF",      "sector":"ETF",          "riesgo":"Medio",  "min_usd":1,   "desc":"Las 100 mejores tecnológicas. Alto crecimiento histórico.",     "dividendo":False},
    "VTI":   {"name":"Total Market ETF",    "sector":"ETF",          "riesgo":"Bajo",   "min_usd":1,   "desc":"Todo el mercado americano. Máxima diversificación.",           "dividendo":True},
    "VYM":   {"name":"High Dividend ETF",   "sector":"ETF",          "riesgo":"Bajo",   "min_usd":1,   "desc":"ETF de empresas con altos dividendos. Ingreso pasivo.",        "dividendo":True},
}

# ─── BROKERS MEJORADOS ────────────────────────────────────────────────────────
BROKERS_INFO = [
    {
        "name":"XTB", "rating":9.2, "fee":"$0", "min_deposit":"$0",
        "acceso_colombia":True, "acepta_fraccion":True,
        "ideal_para":"⭐ MEJOR PARA PRINCIPIANTES EN COLOMBIA",
        "descripcion":"Disponible directamente desde Colombia sin intermediarios. Sin monto mínimo para abrir cuenta. Acciones fraccionadas desde $1 dólar.",
        "ventajas":["✅ Sin monto mínimo","✅ Regulado (CySEC, FCA)","✅ App móvil excelente","✅ Soporte en español","✅ Acciones fraccionadas"],
        "url":"https://www.xtb.com/es",
        "color":"#00ff9d",
        "para_empezar":"Puedes empezar con $50 USD y comprar fracciones de cualquier acción."
    },
    {
        "name":"Interactive Brokers (IBKR)", "rating":9.5, "fee":"$0 (Plan LITE)",  "min_deposit":"$0",
        "acceso_colombia":True, "acepta_fraccion":True,
        "ideal_para":"🏆 MEJOR PLATAFORMA GLOBAL",
        "descripcion":"El broker más completo del mundo. Acepta clientes colombianos. Plan LITE sin comisiones.",
        "ventajas":["✅ Sin monto mínimo","✅ Regulado (SEC, FINRA)","✅ Acciones fraccionadas","✅ +150 mercados globales","✅ Tasa de interés sobre efectivo"],
        "url":"https://www.interactivebrokers.com",
        "color":"#0ea5e9",
        "para_empezar":"Abre cuenta gratis. Transfiere desde Colombia vía transferencia internacional."
    },
    {
        "name":"Stake", "rating":8.5, "fee":"$0", "min_deposit":"$1",
        "acceso_colombia":True, "acepta_fraccion":True,
        "ideal_para":"📱 MÁS FÁCIL PARA LATINOAMÉRICA",
        "descripcion":"App 100% enfocada en Latinoamérica. Interfaz muy simple. Acceso al mercado americano.",
        "ventajas":["✅ Diseñado para LATAM","✅ App muy simple","✅ Desde $1 USD","✅ Sin comisiones","✅ Soporte en español"],
        "url":"https://www.stake.com",
        "color":"#a78bfa",
        "para_empezar":"Descarga la app, verifica tu identidad (cédula), deposita desde $1."
    },
    {
        "name":"Charles Schwab", "rating":9.0, "fee":"$0", "min_deposit":"$0",
        "acceso_colombia":True, "acepta_fraccion":True,
        "ideal_para":"🏦 MEJOR PARA LARGO PLAZO",
        "descripcion":"Uno de los brokers más antiguos y confiables de EEUU. Acepta no-residentes.",
        "ventajas":["✅ Sin monto mínimo","✅ Sin comisiones","✅ Fondos indexados gratis","✅ Muy regulado","✅ Excelente para ETFs"],
        "url":"https://www.schwab.com",
        "color":"#ffd60a",
        "para_empezar":"Abre cuenta internacional. Necesitas pasaporte y comprobante de dirección."
    },
    {
        "name":"Revolut (Brokerage)", "rating":7.8, "fee":"$0 (3 trades/mes gratis)", "min_deposit":"$1",
        "acceso_colombia":False, "acepta_fraccion":True,
        "ideal_para":"💳 PARA QUIENES YA USAN REVOLUT",
        "descripcion":"Si ya tienes cuenta Revolut, puedes invertir directamente desde la app.",
        "ventajas":["✅ Integrado con tarjeta","✅ Muy fácil","✅ Fracciones desde $1","⚠️ Limitado a 3 trades gratis/mes"],
        "url":"https://www.revolut.com",
        "color":"#f97316",
        "para_empezar":"Requiere cuenta Revolut activa. Actualmente disponibilidad limitada en Colombia."
    },
    {
        "name":"Etoro", "rating":8.0, "fee":"$0 (spread)", "min_deposit":"$50",
        "acceso_colombia":True, "acepta_fraccion":True,
        "ideal_para":"🤝 MEJOR PARA COPIAR INVERSORES EXPERTOS",
        "descripcion":"Puedes copiar automáticamente las inversiones de traders exitosos. Muy visual.",
        "ventajas":["✅ Copy trading","✅ Red social de inversores","✅ Acciones fraccionadas","✅ App excelente","⚠️ Spread como comisión"],
        "url":"https://www.etoro.com",
        "color":"#ec4899",
        "para_empezar":"Mínimo $50 USD. Verifica identidad con cédula o pasaporte."
    },
]

# ─── FUNCIONES DE DATOS ───────────────────────────────────────────────────────
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

@st.cache_data(ttl=300)
def fetch_quick_price(symbol):
    try:
        df = yf.Ticker(symbol).history(period="2d", interval="1h")
        if df.empty: return None, None
        close = df["Close"].iloc[-1]
        prev  = df["Close"].iloc[-2] if len(df)>1 else close
        return round(close,2), round((close-prev)/prev*100,2)
    except:
        return None, None

def add_indicators(df):
    if df.empty or len(df)<5: return df
    df = df.copy()
    for w in [7,20,50,200]:
        if len(df)>=w: df[f"ma{w}"] = df["close"].rolling(w).mean()
    delta = df["close"].diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
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

# ─── SISTEMA DE ALERTAS POR CORREO ───────────────────────────────────────────
def send_email_alert(to_email, sender_email, sender_pass, subject, body_html):
    """Envía correo usando Gmail SMTP."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = sender_email
        msg["To"]      = to_email
        msg.attach(MIMEText(body_html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_pass)
            server.sendmail(sender_email, to_email, msg.as_string())
        return True, "✅ Correo enviado correctamente"
    except smtplib.SMTPAuthenticationError:
        return False, "❌ Error de autenticación. Verifica tu correo y contraseña de aplicación."
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

def build_buy_email(symbol, price, signal, reasons, tp, sl, kelly_pct, invest_amt, stock_info):
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    reasons_html = "".join([f"<li style='margin:4px 0;color:{'#00c97a' if '✅' in r else '#ff6b6b' if '❌' in r else '#9ca3af'};'>{r}</li>" for r in reasons])
    return f"""
    <div style="background:#060a0f;font-family:Arial,sans-serif;padding:32px;max-width:600px;margin:0 auto;border-radius:12px;border:1px solid #1f2937;">
      <div style="text-align:center;margin-bottom:24px;">
        <div style="font-size:36px;">📈</div>
        <div style="color:#00ff9d;font-size:22px;font-weight:700;letter-spacing:2px;margin-top:8px;">QUANTUM TRADE</div>
        <div style="color:#4b5563;font-size:11px;letter-spacing:3px;">ALERTA DE INVERSIÓN</div>
      </div>
      <div style="background:#00ff9d15;border:2px solid #00ff9d;border-radius:10px;padding:20px;text-align:center;margin-bottom:20px;">
        <div style="color:#4b5563;font-size:12px;letter-spacing:1px;">SEÑAL DETECTADA</div>
        <div style="color:#00ff9d;font-size:36px;font-weight:700;margin:8px 0;">🟢 COMPRAR</div>
        <div style="color:#fff;font-size:28px;font-weight:700;">{symbol} — ${price:,.2f}</div>
        <div style="color:#9ca3af;font-size:13px;">{stock_info.get('name','')}</div>
        <div style="color:#4b5563;font-size:11px;margin-top:8px;">{now}</div>
      </div>
      <div style="display:grid;margin-bottom:20px;">
        <table width="100%" cellpadding="8" cellspacing="0">
          <tr>
            <td style="background:#0d1117;border:1px solid #1f2937;border-radius:6px;text-align:center;padding:12px;">
              <div style="color:#4b5563;font-size:10px;letter-spacing:1px;">TAKE PROFIT 🎯</div>
              <div style="color:#00ff9d;font-size:18px;font-weight:700;">${tp:,.2f}</div>
            </td>
            <td style="width:8px;"></td>
            <td style="background:#0d1117;border:1px solid #1f2937;border-radius:6px;text-align:center;padding:12px;">
              <div style="color:#4b5563;font-size:10px;letter-spacing:1px;">STOP LOSS 🛑</div>
              <div style="color:#ff6b6b;font-size:18px;font-weight:700;">${sl:,.2f}</div>
            </td>
            <td style="width:8px;"></td>
            <td style="background:#0d1117;border:1px solid #ffd60a40;border-radius:6px;text-align:center;padding:12px;">
              <div style="color:#4b5563;font-size:10px;letter-spacing:1px;">INVERTIR (KELLY)</div>
              <div style="color:#ffd60a;font-size:18px;font-weight:700;">${invest_amt:,.0f}</div>
            </td>
          </tr>
        </table>
      </div>
      <div style="background:#0d1117;border:1px solid #1f2937;border-radius:8px;padding:16px;margin-bottom:20px;">
        <div style="color:#4b5563;font-size:10px;letter-spacing:2px;margin-bottom:10px;">RAZONES DE LA SEÑAL</div>
        <ul style="margin:0;padding-left:16px;">{reasons_html}</ul>
      </div>
      <div style="background:#ff4d6d10;border:1px solid #ff4d6d40;border-radius:8px;padding:14px;font-size:11px;color:#6b7280;">
        ⚠️ <strong style="color:#9ca3af;">Aviso:</strong> Esta alerta es generada por algoritmos de análisis técnico y 
        <strong style="color:#ff6b6b;">no constituye asesoría financiera</strong>. Toda inversión conlleva riesgo.
      </div>
    </div>
    """

def build_sell_email(symbol, buy_price, current_price, pnl, pnl_pct, reason):
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    is_profit = pnl >= 0
    color = "#00ff9d" if is_profit else "#ff4d6d"
    emoji = "🎯" if is_profit else "🛑"
    return f"""
    <div style="background:#060a0f;font-family:Arial,sans-serif;padding:32px;max-width:600px;margin:0 auto;border-radius:12px;border:1px solid #1f2937;">
      <div style="text-align:center;margin-bottom:24px;">
        <div style="font-size:36px;">📈</div>
        <div style="color:#00ff9d;font-size:22px;font-weight:700;letter-spacing:2px;margin-top:8px;">QUANTUM TRADE</div>
        <div style="color:#4b5563;font-size:11px;letter-spacing:3px;">ALERTA DE VENTA</div>
      </div>
      <div style="background:{color}15;border:2px solid {color};border-radius:10px;padding:20px;text-align:center;margin-bottom:20px;">
        <div style="color:#4b5563;font-size:12px;letter-spacing:1px;">SEÑAL DE SALIDA</div>
        <div style="color:{color};font-size:36px;font-weight:700;margin:8px 0;">{emoji} {"TAKE PROFIT" if is_profit else "STOP LOSS"}</div>
        <div style="color:#fff;font-size:28px;font-weight:700;">{symbol} — ${current_price:,.2f}</div>
        <div style="color:{color};font-size:20px;font-weight:700;margin-top:8px;">{pnl:+,.2f} USD ({pnl_pct:+.2f}%)</div>
        <div style="color:#4b5563;font-size:11px;margin-top:8px;">{now}</div>
      </div>
      <div style="background:#0d1117;border:1px solid #1f2937;border-radius:8px;padding:16px;margin-bottom:20px;">
        <table width="100%" cellpadding="6">
          <tr><td style="color:#4b5563;font-size:11px;">Precio de compra</td><td style="color:#fff;font-weight:700;text-align:right;">${buy_price:,.2f}</td></tr>
          <tr><td style="color:#4b5563;font-size:11px;">Precio actual</td><td style="color:{color};font-weight:700;text-align:right;">${current_price:,.2f}</td></tr>
          <tr><td style="color:#4b5563;font-size:11px;">Razón</td><td style="color:#9ca3af;font-size:11px;text-align:right;">{reason}</td></tr>
        </table>
      </div>
      <div style="background:#ff4d6d10;border:1px solid #ff4d6d40;border-radius:8px;padding:14px;font-size:11px;color:#6b7280;">
        ⚠️ Esta alerta es educativa y no constituye asesoría financiera.
      </div>
    </div>
    """

# ─── GRÁFICAS ─────────────────────────────────────────────────────────────────
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
    cv=["#00ff9d" if c>=o else "#ff4d6d" for c,o in zip(df["close"],df["open"])]
    fig.add_trace(go.Bar(x=df.index,y=df["volume"],name="Volumen",marker_color=cv,opacity=0.6),row=2,col=1)
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
    configs=[("5d","1h","5 Días (1h)"),("1mo","1d","1 Mes (1d)"),("6mo","1wk","6 Meses"),("5y","1mo","5 Años")]
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
        fig.update_xaxes(gridcolor="#1f2937",row=i,col=1); fig.update_yaxes(gridcolor="#1f2937",row=i,col=1)
    return fig

# ─── SESSION STATE ────────────────────────────────────────────────────────────
if "trades" not in st.session_state:       st.session_state.trades = []
if "alert_log" not in st.session_state:    st.session_state.alert_log = []
if "email_config" not in st.session_state: st.session_state.email_config = {"to":"","from":"","pass":"","active":False}

def add_trade(symbol, buy_price, shares, buy_date, tp_pct, sl_pct, notes):
    st.session_state.trades.append({
        "id":len(st.session_state.trades),"symbol":symbol,"buy_price":buy_price,
        "shares":shares,"invested":round(buy_price*shares,2),"buy_date":str(buy_date),
        "tp_price":round(buy_price*(1+tp_pct/100),2),"sl_price":round(buy_price*(1-sl_pct/100),2),
        "tp_pct":tp_pct,"sl_pct":sl_pct,"notes":notes,"status":"ABIERTA",
        "sell_price":None,"sell_date":None,"alert_buy_sent":False,"alert_sell_sent":False,
    })

def close_trade(idx, sell_price, sell_date):
    t=st.session_state.trades[idx]
    t["sell_price"]=sell_price; t["sell_date"]=str(sell_date)
    pnl=(sell_price-t["buy_price"])*t["shares"]
    t["status"]="GANANCIA ✅" if pnl>=0 else "PÉRDIDA ❌"
    t["pnl"]=round(pnl,2); t["pnl_pct"]=round((sell_price-t["buy_price"])/t["buy_price"]*100,2)

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:16px 0 8px;'>
        <div style='font-size:36px'>📈</div>
        <div style='color:#fff;font-family:Space Mono;font-weight:700;font-size:16px;letter-spacing:2px;'>QUANTUM TRADE</div>
        <div style='color:#4b5563;font-size:9px;letter-spacing:3px;'>AI STOCK ANALYTICS</div>
    </div><hr style='border-color:#1f2937;margin:8px 0 16px;'>
    """, unsafe_allow_html=True)

    # Filtros de acciones
    sector_filter = st.selectbox("🔎 Filtrar por sector",
        ["Todos","Tecnología","Finanzas","Salud","Consumo","Energía","ETF","Automotriz"])
    riesgo_filter = st.selectbox("⚡ Filtrar por riesgo", ["Todos","Bajo","Medio","Alto"])

    filtered = {k:v for k,v in ALL_STOCKS.items()
                if (sector_filter=="Todos" or v["sector"]==sector_filter)
                and (riesgo_filter=="Todos" or v["riesgo"]==riesgo_filter)}
    if not filtered: filtered = ALL_STOCKS

    symbol = st.selectbox("🎯 Acción", list(filtered.keys()),
        format_func=lambda x: f"{x} — {ALL_STOCKS[x]['name']}")

    st.markdown(f"""
    <div style='background:#0d1117;border:1px solid #1f2937;border-radius:6px;padding:10px;margin:4px 0 12px;'>
      <div style='color:{"#00ff9d" if ALL_STOCKS[symbol]["riesgo"]=="Bajo" else "#ffd60a" if ALL_STOCKS[symbol]["riesgo"]=="Medio" else "#ff4d6d"};
                  font-size:10px;font-weight:700;'>Riesgo: {ALL_STOCKS[symbol]["riesgo"]}</div>
      <div style='color:#6b7280;font-size:10px;margin-top:3px;line-height:1.5;'>{ALL_STOCKS[symbol]["desc"]}</div>
      {"<div style='color:#00ff9d;font-size:10px;margin-top:4px;'>💵 Paga dividendo</div>" if ALL_STOCKS[symbol]["dividendo"] else ""}
    </div>
    """, unsafe_allow_html=True)

    portfolio = st.number_input("💰 Capital disponible (USD)", min_value=1, max_value=10_000_000, value=100, step=10)
    st.markdown("<div style='color:#4b5563;font-size:10px;margin-top:-8px;'>Puedes empezar con $1 USD en acciones fraccionadas</div>", unsafe_allow_html=True)

    st.markdown("<div style='color:#4b5563;font-size:9px;letter-spacing:2px;text-transform:uppercase;margin-top:12px;'>Parámetros Kelly</div>", unsafe_allow_html=True)
    win_rate = st.slider("Win Rate (%)", 40, 70, 55) / 100
    avg_win  = st.slider("Beneficio promedio (x)", 1.0, 3.0, 1.5, 0.1)
    avg_loss = st.slider("Pérdida promedio (x)", 0.5, 2.0, 1.0, 0.1)

    auto_ref = st.checkbox("🔄 Auto-refresh (60s)", value=False)
    if st.button("↻  Actualizar datos"):
        st.cache_data.clear(); st.rerun()

    st.markdown("<hr style='border-color:#1f2937;margin:16px 0 8px;'><div style='color:#4b5563;font-size:9px;line-height:1.7;'>Datos: Yahoo Finance · TTL: 60s<br>Modelos: MA · RSI · MACD · Bollinger · Kelly</div>", unsafe_allow_html=True)

# ─── CARGAR DATOS ─────────────────────────────────────────────────────────────
with st.spinner(f"Cargando {symbol}..."):
    df_1d = fetch_data(symbol, "1y",  "1d")
    df_1h = fetch_data(symbol, "5d",  "1h")
if df_1d.empty:
    st.error("No se pudo cargar el dato. Verifica tu conexión.")
    st.stop()

df_1d=add_indicators(df_1d)
df_1h=add_indicators(df_1h) if not df_1h.empty else df_1d
sig=generate_signal(df_1d)
kelly_pct=kelly_criterion(win_rate,avg_win,avg_loss)
invest_amt=portfolio*kelly_pct
last=df_1d.iloc[-1]; prev=df_1d.iloc[-2]
price_now=last["close"]; price_chg=((price_now-prev["close"])/prev["close"])*100
atr_val=last.get("atr", price_now*0.02)
proj_tp=round(price_now+atr_val*2.5,2)
proj_sl=round(price_now-atr_val*1.5,2)

# ─── ESCÁNER AUTOMÁTICO COMPLETO ─────────────────────────────────────────────
# Inicializar estado del escáner
if "last_scan_time"    not in st.session_state: st.session_state.last_scan_time    = 0
if "scanner_results"   not in st.session_state: st.session_state.scanner_results   = []
if "scanned_signals"   not in st.session_state: st.session_state.scanned_signals   = {}  # symbol -> last signal sent

SCAN_INTERVAL = 300  # segundos entre escaneos (5 minutos)

def build_scanner_email(results_buy, results_sell, results_tp, results_sl):
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    def rows_html(items, color, icon):
        if not items: return f"<tr><td colspan='4' style='color:#4b5563;font-size:11px;padding:8px;text-align:center;'>Sin señales en este momento</td></tr>"
        html = ""
        for sym, price, strength, reason in items:
            html += f"""<tr>
              <td style='padding:8px;color:#fff;font-family:monospace;font-weight:700;'>{icon} {sym}</td>
              <td style='padding:8px;color:{color};font-family:monospace;'>${price:,.2f}</td>
              <td style='padding:8px;color:{color};font-family:monospace;'>{strength}%</td>
              <td style='padding:8px;color:#6b7280;font-size:10px;'>{reason}</td>
            </tr>"""
        return html

    buy_rows  = rows_html(results_buy,  "#00ff9d", "🟢")
    sell_rows = rows_html(results_sell, "#ff4d6d", "🔴")
    tp_rows   = rows_html(results_tp,   "#00ff9d", "🎯")
    sl_rows   = rows_html(results_sl,   "#ff4d6d", "🛑")

    total = len(results_buy) + len(results_sell) + len(results_tp) + len(results_sl)

    return f"""
    <div style="background:#060a0f;font-family:Arial,sans-serif;padding:28px;max-width:650px;margin:0 auto;border-radius:12px;border:1px solid #1f2937;">
      <div style="text-align:center;margin-bottom:20px;">
        <div style="font-size:32px;">📊</div>
        <div style="color:#00ff9d;font-size:20px;font-weight:700;letter-spacing:2px;margin-top:6px;">QUANTUM TRADE</div>
        <div style="color:#4b5563;font-size:10px;letter-spacing:3px;">REPORTE AUTOMÁTICO DE MERCADO</div>
        <div style="color:#374151;font-size:11px;margin-top:4px;">{now} · {total} señales detectadas</div>
      </div>

      {"" if not results_tp and not results_sl else f'''
      <div style="background:#ff4d6d10;border:1px solid #ff4d6d40;border-radius:8px;padding:14px;margin-bottom:16px;">
        <div style="color:#ff4d6d;font-weight:700;font-size:13px;margin-bottom:10px;">⚡ TUS POSICIONES — ACCIÓN REQUERIDA</div>
        <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
          <tr style="border-bottom:1px solid #1f2937;">
            <th style="color:#4b5563;font-size:9px;padding:6px 8px;text-align:left;letter-spacing:1px;">ACCIÓN</th>
            <th style="color:#4b5563;font-size:9px;padding:6px 8px;text-align:left;letter-spacing:1px;">PRECIO</th>
            <th style="color:#4b5563;font-size:9px;padding:6px 8px;text-align:left;letter-spacing:1px;">SEÑAL</th>
            <th style="color:#4b5563;font-size:9px;padding:6px 8px;text-align:left;letter-spacing:1px;">DETALLE</th>
          </tr>
          {tp_rows}{sl_rows}
        </table>
      </div>'''}

      <div style="background:#0d1117;border:1px solid #1f2937;border-radius:8px;padding:14px;margin-bottom:12px;">
        <div style="color:#00ff9d;font-weight:700;font-size:13px;margin-bottom:10px;">🟢 OPORTUNIDADES DE COMPRA</div>
        <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
          <tr style="border-bottom:1px solid #1f2937;">
            <th style="color:#4b5563;font-size:9px;padding:6px 8px;text-align:left;letter-spacing:1px;">ACCIÓN</th>
            <th style="color:#4b5563;font-size:9px;padding:6px 8px;text-align:left;letter-spacing:1px;">PRECIO</th>
            <th style="color:#4b5563;font-size:9px;padding:6px 8px;text-align:left;letter-spacing:1px;">FUERZA</th>
            <th style="color:#4b5563;font-size:9px;padding:6px 8px;text-align:left;letter-spacing:1px;">RAZÓN</th>
          </tr>
          {buy_rows}
        </table>
      </div>

      <div style="background:#0d1117;border:1px solid #1f2937;border-radius:8px;padding:14px;margin-bottom:16px;">
        <div style="color:#ff4d6d;font-weight:700;font-size:13px;margin-bottom:10px;">🔴 SEÑALES DE VENTA / PRECAUCIÓN</div>
        <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
          <tr style="border-bottom:1px solid #1f2937;">
            <th style="color:#4b5563;font-size:9px;padding:6px 8px;text-align:left;letter-spacing:1px;">ACCIÓN</th>
            <th style="color:#4b5563;font-size:9px;padding:6px 8px;text-align:left;letter-spacing:1px;">PRECIO</th>
            <th style="color:#4b5563;font-size:9px;padding:6px 8px;text-align:left;letter-spacing:1px;">FUERZA</th>
            <th style="color:#4b5563;font-size:9px;padding:6px 8px;text-align:left;letter-spacing:1px;">RAZÓN</th>
          </tr>
          {sell_rows}
        </table>
      </div>

      <div style="background:#ff4d6d10;border:1px solid #ff4d6d30;border-radius:6px;padding:10px 14px;font-size:10px;color:#6b7280;">
        ⚠️ Alertas generadas por análisis técnico automático. No constituyen asesoría financiera.
      </div>
    </div>
    """

def run_full_scanner(cfg, portfolio_trades):
    """Escanea todas las acciones y posiciones abiertas. Retorna resultados y envía correo."""
    results_buy  = []  # (symbol, price, strength, reason)
    results_sell = []
    results_tp   = []  # posiciones abiertas que tocaron TP
    results_sl   = []  # posiciones abiertas que tocaron SL

    prev_signals = st.session_state.scanned_signals

    # ── 1. Escanear TODAS las acciones ────────────────────────────────────────
    for sym in ALL_STOCKS.keys():
        try:
            df = fetch_data(sym, "3mo", "1d")
            if df.empty or len(df) < 50: continue
            df  = add_indicators(df)
            sig = generate_signal(df)
            cp  = df["close"].iloc[-1]

            prev_sig = prev_signals.get(sym, "NEUTRAL")

            # Solo alertar si la señal CAMBIÓ respecto al último escaneo
            if sig["signal"] == "COMPRAR" and sig["strength"] >= 65 and prev_sig != "COMPRAR":
                last_row = df.iloc[-1]
                reasons  = " · ".join([r.replace("✅ ","").replace("❌ ","").replace("➖ ","") for r in sig["reasons"][:2]])
                results_buy.append((sym, cp, sig["strength"], reasons))

            elif sig["signal"] == "VENDER" and sig["strength"] <= 35 and prev_sig != "VENDER":
                last_row = df.iloc[-1]
                reasons  = " · ".join([r.replace("✅ ","").replace("❌ ","").replace("➖ ","") for r in sig["reasons"][:2]])
                results_sell.append((sym, cp, sig["strength"], reasons))

            # Actualizar estado
            st.session_state.scanned_signals[sym] = sig["signal"]

        except: continue

    # ── 2. Revisar posiciones abiertas ────────────────────────────────────────
    for t in portfolio_trades:
        if t["status"] != "ABIERTA": continue
        try:
            cp, _ = fetch_quick_price(t["symbol"])
            if cp is None: continue
            unreal_pct = (cp - t["buy_price"]) / t["buy_price"] * 100

            if cp >= t["tp_price"] and not t.get("alert_sell_sent"):
                pnl = (cp - t["buy_price"]) * t["shares"]
                results_tp.append((t["symbol"], cp, round(unreal_pct, 1), f"TP alcanzado · P&L +${pnl:,.2f}"))
                t["alert_sell_sent"] = True

            elif cp <= t["sl_price"] and not t.get("alert_sell_sent"):
                pnl = (cp - t["buy_price"]) * t["shares"]
                results_sl.append((t["symbol"], cp, round(unreal_pct, 1), f"SL alcanzado · P&L ${pnl:,.2f}"))
                t["alert_sell_sent"] = True
        except: continue

    # ── 3. Guardar resultados en session state ────────────────────────────────
    all_results = []
    for sym, price, strength, reason in results_buy:
        all_results.append({"type":"COMPRAR","symbol":sym,"price":price,"strength":strength,"reason":reason,"color":"#00ff9d","time":datetime.now().strftime("%H:%M")})
    for sym, price, strength, reason in results_sell:
        all_results.append({"type":"VENDER","symbol":sym,"price":price,"strength":strength,"reason":reason,"color":"#ff4d6d","time":datetime.now().strftime("%H:%M")})
    for sym, price, strength, reason in results_tp:
        all_results.append({"type":"TP ✅","symbol":sym,"price":price,"strength":strength,"reason":reason,"color":"#00ff9d","time":datetime.now().strftime("%H:%M")})
    for sym, price, strength, reason in results_sl:
        all_results.append({"type":"SL 🛑","symbol":sym,"price":price,"strength":strength,"reason":reason,"color":"#ff4d6d","time":datetime.now().strftime("%H:%M")})

    if all_results:
        st.session_state.scanner_results = all_results + st.session_state.scanner_results
        st.session_state.scanner_results = st.session_state.scanner_results[:50]  # keep last 50

    # ── 4. Enviar correo si hay señales nuevas ────────────────────────────────
    total_new = len(results_buy) + len(results_sell) + len(results_tp) + len(results_sl)
    if total_new > 0 and cfg["active"] and cfg["to"] and cfg["from"] and cfg["pass"]:
        html = build_scanner_email(results_buy, results_sell, results_tp, results_sl)
        subject = f"📊 Quantum Trade — {total_new} señal(es) detectada(s) · {datetime.now().strftime('%H:%M')}"
        ok, msg = send_email_alert(cfg["to"], cfg["from"], cfg["pass"], subject, html)
        if ok:
            st.session_state.alert_log.append({
                "time": datetime.now().strftime("%H:%M"),
                "msg": f"📧 Reporte enviado — {total_new} señales ({len(results_buy)} compra, {len(results_sell)} venta, {len(results_tp)+len(results_sl)} posiciones)",
                "color": "#00ff9d"
            })

    st.session_state.last_scan_time = time.time()
    return all_results

# ── Ejecutar escáner si pasaron 5 minutos ─────────────────────────────────────
cfg = st.session_state.email_config
tiempo_desde_scan = time.time() - st.session_state.last_scan_time
debe_escanear     = tiempo_desde_scan >= SCAN_INTERVAL

if debe_escanear and cfg.get("active") and cfg.get("to") and cfg.get("from") and cfg.get("pass"):
    with st.spinner("🔍 Escaneando mercado..."):
        run_full_scanner(cfg, st.session_state.trades)

# ─── HEADER — variables pre-calculadas para evitar f-string con ternarios ────
sc           = sig["color"]
sig_label    = sig["signal"]
sig_emoji    = "🟢" if sig_label == "COMPRAR" else ("🔴" if sig_label == "VENDER" else "🟡")
price_arrow  = "▲" if price_chg >= 0 else "▼"
price_color  = "#00ff9d" if price_chg >= 0 else "#ff4d6d"
riesgo_val   = ALL_STOCKS[symbol]["riesgo"]
riesgo_bg    = "#00ff9d20" if riesgo_val == "Bajo" else ("#ffd60a20" if riesgo_val == "Medio" else "#ff4d6d20")
riesgo_color = "#00ff9d"   if riesgo_val == "Bajo" else ("#ffd60a"   if riesgo_val == "Medio" else "#ff4d6d")
div_badge    = "<span style='background:#00ff9d20;color:#00ff9d;padding:2px 8px;border-radius:3px;font-size:10px;'>💵 Dividendo</span>" if ALL_STOCKS[symbol]["dividendo"] else ""
stock_name   = ALL_STOCKS[symbol]["name"]
stock_sector = ALL_STOCKS[symbol]["sector"]

st.markdown(f"""
<div style='background:#0d1117;border:1px solid #1f2937;border-radius:10px;padding:20px 24px;margin-bottom:16px;'>
  <div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;'>
    <div>
      <div style='display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:6px;'>
        <span style='color:#fff;font-family:Space Mono;font-weight:700;font-size:24px;'>{symbol}</span>
        <span style='color:#6b7280;font-size:14px;'>{stock_name}</span>
        <span style='background:#1f2937;color:#9ca3af;padding:2px 8px;border-radius:3px;font-size:10px;'>{stock_sector}</span>
        <span style='background:{riesgo_bg};color:{riesgo_color};padding:2px 8px;border-radius:3px;font-size:10px;'>Riesgo {riesgo_val}</span>
        {div_badge}
      </div>
      <div style='display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;'>
        <span style='color:#fff;font-family:Space Mono;font-size:34px;font-weight:700;'>${price_now:,.2f}</span>
        <span style='color:{price_color};font-family:Space Mono;font-size:16px;'>{price_arrow} {abs(price_chg):.2f}%</span>
      </div>
    </div>
    <div style='text-align:right;'>
      <div style='background:{sc}20;border:2px solid {sc};color:{sc};padding:10px 24px;border-radius:8px;
                  font-family:Space Mono;font-size:20px;font-weight:700;letter-spacing:2px;'>
        {sig_emoji} {sig_label}
      </div>
      <div style='color:#6b7280;font-size:11px;margin-top:6px;'>Fuerza de señal: {sig["strength"]}%</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── PANEL DE CONCLUSIONES — cuándo y por qué invertir ───────────────────────
def build_conclusions(df, sig, price_now, proj_tp, proj_sl, symbol, stock_info):
    """Genera conclusiones legibles en español sobre el momento de inversión."""
    last = df.iloc[-1]
    rsi_v   = last.get("rsi", 50)
    ma7     = last.get("ma7",  0)
    ma20    = last.get("ma20", 0)
    ma50    = last.get("ma50", 0)
    macd_v  = last.get("macd", 0)
    macd_s  = last.get("macd_signal", 0)
    bb_up   = last.get("bb_upper", price_now)
    bb_low  = last.get("bb_lower", price_now)
    bb_mid  = last.get("bb_mid",   price_now)
    atr_v   = last.get("atr", price_now * 0.02)

    items = []

    # ── 1. Cruce de medias móviles ────────────────────────────────────────────
    if ma7 > 0 and ma20 > 0:
        diff_pct = abs(ma7 - ma20) / ma20 * 100
        if ma7 > ma20:
            if diff_pct < 0.5:
                items.append(("🔀", "Cruce MA7 × MA20 reciente", "COMPRA",
                    f"La media de 7 días (${ma7:,.2f}) acaba de cruzar por encima de la de 20 días (${ma20:,.2f}). "
                    f"Diferencia de solo {diff_pct:.1f}% — el cruce es muy fresco. BUEN momento de entrada.","#00ff9d"))
            else:
                items.append(("📈", "Tendencia alcista activa", "POSITIVO",
                    f"MA7 (${ma7:,.2f}) está por encima de MA20 (${ma20:,.2f}) con {diff_pct:.1f}% de diferencia. "
                    f"La tendencia de corto plazo es alcista y tiene momentum.","#00ff9d"))
        else:
            items.append(("📉", "Cruce bajista MA7 × MA20", "ESPERAR",
                f"MA7 (${ma7:,.2f}) está por debajo de MA20 (${ma20:,.2f}). "
                f"La presión vendedora domina. Espera que MA7 vuelva a cruzar hacia arriba antes de entrar.","#ff4d6d"))

    # ── 2. Precio vs MA50 (tendencia de fondo) ────────────────────────────────
    if ma50 > 0:
        dist50 = (price_now - ma50) / ma50 * 100
        if price_now > ma50:
            items.append(("🏔️", "Precio sobre MA50 — tendencia estructural alcista", "POSITIVO",
                f"El precio (${price_now:,.2f}) está un {dist50:.1f}% por encima de la media de 50 días (${ma50:,.2f}). "
                f"La tendencia de fondo es alcista. Las correcciones son oportunidades de compra.","#00ff9d"))
        else:
            items.append(("⚠️", "Precio bajo MA50 — tendencia estructural bajista", "PRECAUCIÓN",
                f"El precio está un {abs(dist50):.1f}% por debajo de MA50 (${ma50:,.2f}). "
                f"La tendencia de fondo es bajista. Solo considera comprar con señales muy fuertes.","#ffd60a"))

    # ── 3. RSI ────────────────────────────────────────────────────────────────
    if rsi_v < 30:
        items.append(("🟢", f"RSI en zona de SOBREVENTA ({rsi_v:.0f})", "COMPRA FUERTE",
            f"El RSI de {rsi_v:.0f} indica que la acción cayó demasiado rápido. "
            f"Históricamente cuando el RSI baja de 30 hay un rebote. "
            f"Es una de las mejores señales de entrada. Combina con soporte en Bollinger.", "#00ff9d"))
    elif rsi_v > 70:
        items.append(("🔴", f"RSI en zona de SOBRECOMPRA ({rsi_v:.0f})", "VENDER / ESPERAR",
            f"El RSI de {rsi_v:.0f} indica que la acción subió demasiado rápido sin descanso. "
            f"Alta probabilidad de corrección a la baja. Evita comprar ahora, espera que RSI baje a zona 40–55.", "#ff4d6d"))
    elif 40 <= rsi_v <= 60:
        items.append(("🟡", f"RSI en zona neutral ({rsi_v:.0f})", "NEUTRAL",
            f"RSI de {rsi_v:.0f} en zona central. No hay señal fuerte de sobrecompra ni sobreventa. "
            f"La decisión depende más del cruce de medias y el MACD.", "#ffd60a"))
    else:
        rsi_dir = "recuperándose" if rsi_v > 50 else "debilitándose"
        items.append(("🟡", f"RSI {rsi_v:.0f} — {rsi_dir}", "NEUTRAL",
            f"RSI en {rsi_v:.0f}, {rsi_dir}. Observa si continúa la dirección actual para confirmar señal.", "#ffd60a"))

    # ── 4. Bandas de Bollinger ────────────────────────────────────────────────
    bb_pos = (price_now - bb_low) / (bb_up - bb_low) * 100 if (bb_up - bb_low) > 0 else 50
    if price_now <= bb_low:
        items.append(("🎯", "Precio tocando banda INFERIOR de Bollinger", "ENTRADA IDEAL",
            f"El precio (${price_now:,.2f}) tocó la banda inferior (${bb_low:,.2f}). "
            f"Esto indica un nivel de soporte estadístico fuerte. En el 85% de los casos el precio rebota "
            f"hacia la banda media (${bb_mid:,.2f}). Excelente punto de entrada.", "#00ff9d"))
    elif price_now >= bb_up:
        items.append(("🚨", "Precio tocando banda SUPERIOR de Bollinger", "TOMAR GANANCIAS",
            f"El precio (${price_now:,.2f}) alcanzó la banda superior (${bb_up:,.2f}). "
            f"Zona de resistencia estadística. Alta probabilidad de retroceso hacia ${bb_mid:,.2f}. "
            f"Si ya tienes posición abierta, considera tomar ganancias parciales.", "#ff4d6d"))
    else:
        items.append(("📊", f"Precio en posición {bb_pos:.0f}% dentro del canal Bollinger", "INFO",
            f"El precio está al {bb_pos:.0f}% del recorrido entre banda inferior (${bb_low:,.2f}) "
            f"y superior (${bb_up:,.2f}). La banda media es ${bb_mid:,.2f}. "
            f"{'Por encima del centro — momentum positivo.' if bb_pos > 50 else 'Por debajo del centro — presión vendedora.'}", "#0ea5e9"))

    # ── 5. MACD ───────────────────────────────────────────────────────────────
    if macd_v > 0 and macd_v > macd_s:
        items.append(("⚡", "MACD positivo con momentum creciente", "POSITIVO",
            f"El MACD ({macd_v:.3f}) está por encima de su línea de señal ({macd_s:.3f}) y en territorio positivo. "
            f"Indica que la fuerza compradora está acelerando. Buen acompañamiento para señal de compra.", "#00ff9d"))
    elif macd_v < 0 and macd_v < macd_s:
        items.append(("💤", "MACD negativo con momentum bajista", "NEGATIVO",
            f"El MACD ({macd_v:.3f}) por debajo de su señal ({macd_s:.3f}) en terreno negativo. "
            f"La presión vendedora supera a la compradora. Espera cruce del MACD hacia arriba para confirmar entrada.", "#ff4d6d"))
    else:
        items.append(("🔄", "MACD en transición", "OBSERVAR",
            f"MACD ({macd_v:.3f}) cruzando su línea de señal ({macd_s:.3f}). "
            f"{'Posible inicio de tendencia alcista.' if macd_v > macd_s else 'Posible inicio de debilidad.'}", "#ffd60a"))

    # ── 6. Conclusión final ───────────────────────────────────────────────────
    s = sig["strength"]
    if s >= 70:
        concl = ("🚀", "MOMENTO ÓPTIMO DE COMPRA",
            f"Múltiples indicadores alineados a favor. Con ${price_now:,.2f} el modelo proyecta "
            f"Take Profit en ${proj_tp:,.2f} (+{(proj_tp-price_now)/price_now*100:.1f}%) y "
            f"Stop Loss en ${proj_sl:,.2f} (-{(price_now-proj_sl)/price_now*100:.1f}%). "
            f"Fuerza de señal: {s}%.", "#00ff9d")
    elif s >= 55:
        concl = ("👍", "CONDICIONES FAVORABLES — entrada con cautela",
            f"Señales mayoritariamente positivas pero no todas alineadas. "
            f"Puedes entrar con posición reducida (50% del monto Kelly). "
            f"TP sugerido: ${proj_tp:,.2f} · SL: ${proj_sl:,.2f}.", "#ffd60a")
    elif s >= 40:
        concl = ("⏸️", "ZONA NEUTRAL — esperar mejor momento",
            f"Las señales están divididas. No hay ventaja estadística clara en este momento. "
            f"Espera que RSI baje de 40 o que haya un cruce claro de medias móviles antes de entrar.", "#ffd60a")
    else:
        concl = ("🛑", "SEÑAL DE VENTA / NO ENTRAR",
            f"Los indicadores muestran presión bajista dominante (fuerza {s}%). "
            f"Si tienes posición abierta, considera protegerla con Stop Loss en ${proj_sl:,.2f}. "
            f"No abras posiciones nuevas en este momento.", "#ff4d6d")

    return items, concl

conclusions, final_concl = build_conclusions(df_1d, sig, price_now, proj_tp, proj_sl, symbol, ALL_STOCKS[symbol])

# Renderizar panel de conclusiones
st.markdown(f"""
<div style='background:#0d1117;border:1px solid #1f2937;border-radius:10px;padding:0;margin-bottom:16px;overflow:hidden;'>
  <div style='background:#060a0f;padding:12px 20px;border-bottom:1px solid #1f2937;display:flex;align-items:center;gap:10px;'>
    <span style='font-size:16px;'>🧠</span>
    <span style='color:#fff;font-family:Space Mono;font-weight:700;font-size:13px;letter-spacing:1px;'>ANÁLISIS AUTOMÁTICO — {symbol} · ¿Cuándo y por qué invertir?</span>
  </div>
  <div style='padding:16px 20px;display:grid;grid-template-columns:1fr 1fr;gap:10px;'>
""", unsafe_allow_html=True)

for icon, title, label, desc, color in conclusions:
    label_bg = color + "20"
    st.markdown(f"""
    <div style='background:#060a0f;border:1px solid #1f2937;border-left:3px solid {color};border-radius:6px;padding:12px 14px;'>
      <div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;'>
        <span style='color:#fff;font-size:12px;font-weight:600;'>{icon} {title}</span>
        <span style='background:{label_bg};color:{color};padding:2px 8px;border-radius:3px;font-size:9px;font-family:Space Mono;font-weight:700;letter-spacing:1px;'>{label}</span>
      </div>
      <div style='color:#6b7280;font-size:11px;line-height:1.7;'>{desc}</div>
    </div>
    """, unsafe_allow_html=True)

# Conclusión final destacada
fc_icon, fc_title, fc_desc, fc_color = final_concl
fc_bg = fc_color + "15"
st.markdown(f"""
  </div>
  <div style='padding:0 20px 16px;'>
    <div style='background:{fc_bg};border:2px solid {fc_color};border-radius:8px;padding:16px 18px;'>
      <div style='color:{fc_color};font-family:Space Mono;font-size:14px;font-weight:700;margin-bottom:8px;'>{fc_icon} CONCLUSIÓN: {fc_title}</div>
      <div style='color:#9ca3af;font-size:12px;line-height:1.8;'>{fc_desc}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── MÉTRICAS ─────────────────────────────────────────────────────────────────
c1,c2,c3,c4,c5,c6=st.columns(6)
rsi_v=last.get("rsi",50)
c1.metric("RSI (14)", f"{rsi_v:.1f}", "Sobrevendido" if rsi_v<30 else ("Sobrecomprado" if rsi_v>70 else "Neutral"))
c2.metric("MA 20", f"${last.get('ma20',0):,.2f}")
c3.metric("MA 50", f"${last.get('ma50',0):,.2f}")
c4.metric("BB Superior", f"${last.get('bb_upper',0):,.2f}")
c5.metric("Kelly %", f"{kelly_pct*100:.1f}%", "Óptimo según modelo")
c6.metric("💰 Invertir", f"${invest_amt:,.2f}", f"{kelly_pct*100:.1f}% de ${portfolio:,.0f}")
st.markdown("<br>", unsafe_allow_html=True)

# ─── TABS ─────────────────────────────────────────────────────────────────────
t1,t2,t3,t4,t5,t6,t7=st.tabs([
    "📊  Gráfica","📅  Multi-Período","⚡  RSI & Bollinger",
    "🧮  Señal","💼  Mis Inversiones","🔔  Alertas Correo","🏦  Brokers"
])

with t1:
    df_show=df_1h if not df_1h.empty else df_1d
    st.plotly_chart(build_main_chart(df_show,symbol),use_container_width=True)

with t2:
    st.plotly_chart(build_multi_tf(symbol),use_container_width=True)
    st.markdown("<div style='background:#0d1117;border:1px solid #1f2937;border-radius:8px;padding:12px 16px;font-size:11px;color:#6b7280;'>💡 <b style='color:#9ca3af;'>Intersección de tendencias:</b> Cuando todos los marcos temporales muestran la misma dirección, la señal es mucho más confiable.</div>", unsafe_allow_html=True)

with t3:
    st.plotly_chart(build_rsi_bb(df_1d),use_container_width=True)

with t4:
    cl,cr=st.columns(2)
    with cl:
        st.markdown("### 📋 Señales Detectadas")
        for r in sig["reasons"]:
            color="#00ff9d" if "✅" in r else ("#ff4d6d" if "❌" in r else "#9ca3af")
            st.markdown(f"<div style='color:{color};font-size:12px;padding:4px 0;font-family:Space Mono;'>{r}</div>", unsafe_allow_html=True)
        s=sig["strength"]
        st.markdown(f"""<div style='margin-top:16px;'>
        <div style='color:#4b5563;font-size:9px;letter-spacing:2px;text-transform:uppercase;margin-bottom:6px;'>FUERZA DE SEÑAL</div>
        <div style='background:#1f2937;border-radius:4px;height:8px;width:100%;'>
          <div style='background:{sig["color"]};border-radius:4px;height:8px;width:{s}%;'></div>
        </div>
        <div style='color:{sig["color"]};font-family:Space Mono;font-size:20px;font-weight:700;margin-top:6px;'>{s}%</div>
        </div>""", unsafe_allow_html=True)
    with cr:
        st.markdown("### 🧮 Criterio de Kelly")
        ic=("#00ff9d" if sig["signal"]=="COMPRAR" else "#ff4d6d" if sig["signal"]=="VENDER" else "#ffd60a")
        st.markdown(f"""<div style='background:#0d1117;border:1px solid #1f2937;border-radius:10px;padding:20px;'>
        <div style='background:#060a0f;border:1px solid #1f2937;border-radius:6px;padding:12px;font-family:Space Mono;font-size:13px;color:#9ca3af;margin-bottom:16px;'>
          f* = W − (1−W) / B<br><span style='font-size:10px;color:#4b5563;'>W={win_rate:.0%} · B={avg_win/avg_loss:.2f}</span>
        </div>
        <div style='text-align:center;'>
          <div style='color:#ffd60a;font-family:Space Mono;font-size:42px;font-weight:700;'>{kelly_pct*100:.1f}%</div>
          <div style='color:#4b5563;font-size:11px;'>del capital a invertir</div>
          <div style='margin:16px 0;border-top:1px solid #1f2937;padding-top:16px;'>
            <div style='color:#6b7280;font-size:11px;'>Monto sugerido para {symbol}</div>
            <div style='color:{ic};font-family:Space Mono;font-size:28px;font-weight:700;'>${invest_amt:,.2f}</div>
          </div>
        </div></div>""", unsafe_allow_html=True)
        p52h=df_1d["high"].max(); p52l=df_1d["low"].min(); avol=df_1d["volume"].mean()
        st.markdown(f"""<div style='background:#0d1117;border:1px solid #1f2937;border-radius:8px;padding:14px;font-family:Space Mono;font-size:11px;margin-top:12px;'>
        <div style='color:#4b5563;letter-spacing:2px;margin-bottom:8px;font-size:9px;'>ESTADÍSTICAS 52 SEMANAS</div>
        <div style='display:grid;grid-template-columns:1fr 1fr;gap:8px;'>
          <div><span style='color:#4b5563;'>Máximo:</span> <span style='color:#00ff9d;'>${p52h:,.2f}</span></div>
          <div><span style='color:#4b5563;'>Mínimo:</span> <span style='color:#ff4d6d;'>${p52l:,.2f}</span></div>
          <div><span style='color:#4b5563;'>ATR(14):</span> <span style='color:#a78bfa;'>${last.get("atr",0):.2f}</span></div>
          <div><span style='color:#4b5563;'>Vol. prom:</span> <span style='color:#0ea5e9;'>{avol/1e6:.1f}M</span></div>
        </div></div>""", unsafe_allow_html=True)

# ── TAB 5: MIS INVERSIONES ───────────────────────────────────────────────────
with t5:
    st.markdown("### 💼 Mis Inversiones — Tracker Personal")
    proj_tp_pct=round((proj_tp-price_now)/price_now*100,1)
    proj_sl_pct=round((price_now-proj_sl)/price_now*100,1)
    rr_ratio=round(proj_tp_pct/proj_sl_pct,2) if proj_sl_pct>0 else 0
    if sig["strength"]>=65: horizonte,hcolor="Corto plazo (1–5 días)","#00ff9d"
    elif sig["strength"]>=50: horizonte,hcolor="Mediano plazo (1–3 semanas)","#ffd60a"
    else: horizonte,hcolor="Esperar mejor entrada","#ff4d6d"

    st.markdown(f"""
    <div style='background:#0d1117;border:1px solid #1f2937;border-radius:10px;padding:20px;margin-bottom:16px;'>
      <div style='color:#4b5563;font-size:9px;letter-spacing:2px;text-transform:uppercase;margin-bottom:14px;font-family:Space Mono;'>📡 PROYECCIÓN DEL MODELO — {symbol} @ ${price_now:,.2f}</div>
      <div style='display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:14px;'>
        <div style='background:#060a0f;border:1px solid #1f2937;border-radius:8px;padding:12px;text-align:center;'>
          <div style='color:#4b5563;font-size:9px;'>SEÑAL</div>
          <div style='color:{sig["color"]};font-family:Space Mono;font-size:18px;font-weight:700;margin-top:4px;'>{sig["signal"]}</div>
          <div style='color:#4b5563;font-size:10px;'>Fuerza {sig["strength"]}%</div>
        </div>
        <div style='background:#060a0f;border:1px solid #00ff9d30;border-radius:8px;padding:12px;text-align:center;'>
          <div style='color:#4b5563;font-size:9px;'>TAKE PROFIT 🎯</div>
          <div style='color:#00ff9d;font-family:Space Mono;font-size:18px;font-weight:700;margin-top:4px;'>${proj_tp:,.2f}</div>
          <div style='color:#00ff9d;font-size:10px;'>+{proj_tp_pct}%</div>
        </div>
        <div style='background:#060a0f;border:1px solid #ff4d6d30;border-radius:8px;padding:12px;text-align:center;'>
          <div style='color:#4b5563;font-size:9px;'>STOP LOSS 🛑</div>
          <div style='color:#ff4d6d;font-family:Space Mono;font-size:18px;font-weight:700;margin-top:4px;'>${proj_sl:,.2f}</div>
          <div style='color:#ff4d6d;font-size:10px;'>-{proj_sl_pct}%</div>
        </div>
        <div style='background:#060a0f;border:1px solid #ffd60a30;border-radius:8px;padding:12px;text-align:center;'>
          <div style='color:#4b5563;font-size:9px;'>RATIO R/R</div>
          <div style='color:#ffd60a;font-family:Space Mono;font-size:18px;font-weight:700;margin-top:4px;'>{rr_ratio}:1</div>
          <div style='color:{"#00ff9d" if rr_ratio>=1.5 else "#ff4d6d"};font-size:10px;'>{"✅ Favorable" if rr_ratio>=1.5 else "❌ Desfavorable"}</div>
        </div>
      </div>
      <div style='background:#060a0f;border:1px solid #1f2937;border-radius:6px;padding:10px 14px;'>
        ⏱️ <span style='color:#4b5563;font-size:10px;'>HORIZONTE: </span>
        <span style='color:{hcolor};font-family:Space Mono;font-size:11px;font-weight:700;'>{horizonte}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("➕ Registrar nueva inversión", expanded=len(st.session_state.trades)==0):
        fc1,fc2,fc3=st.columns(3)
        with fc1:
            ts=st.selectbox("Acción",list(ALL_STOCKS.keys()),index=list(ALL_STOCKS.keys()).index(symbol),key="ts")
            tsh=st.number_input("Cantidad acciones",min_value=1,max_value=10000,value=1,key="tsh")
        with fc2:
            tbp=st.number_input("Precio de compra (USD)",min_value=0.01,value=float(round(price_now,2)),step=0.01,key="tbp")
            tbd=st.date_input("Fecha de compra",value=pd.Timestamp.today(),key="tbd")
        with fc3:
            ttp=st.number_input("Take Profit %",min_value=0.5,max_value=100.0,value=float(proj_tp_pct),step=0.5,key="ttp")
            tsl=st.number_input("Stop Loss %",min_value=0.5,max_value=50.0,value=float(proj_sl_pct),step=0.5,key="tsl")
        tnotes=st.text_input("Notas / Razón de la operación",placeholder="Ej: RSI en 28, rebote en soporte...",key="tnotes")
        tp_prev=round(tbp*(1+ttp/100),2); sl_prev=round(tbp*(1-tsl/100),2)
        inv_tot=round(tbp*tsh,2); gan_pot=round((tp_prev-tbp)*tsh,2); per_pot=round((tbp-sl_prev)*tsh,2)
        st.markdown(f"""<div style='background:#060a0f;border:1px solid #1f2937;border-radius:8px;padding:12px;margin:10px 0;
                    display:grid;grid-template-columns:repeat(5,1fr);gap:8px;font-family:Space Mono;font-size:11px;text-align:center;'>
          <div><div style='color:#4b5563;font-size:9px;'>INVERTIDO</div><div style='color:#fff;'>${inv_tot:,.2f}</div></div>
          <div><div style='color:#4b5563;font-size:9px;'>TP</div><div style='color:#00ff9d;'>${tp_prev:,.2f}</div></div>
          <div><div style='color:#4b5563;font-size:9px;'>SL</div><div style='color:#ff4d6d;'>${sl_prev:,.2f}</div></div>
          <div><div style='color:#4b5563;font-size:9px;'>GANANCIA POT.</div><div style='color:#00ff9d;'>+${gan_pot:,.2f}</div></div>
          <div><div style='color:#4b5563;font-size:9px;'>PÉRDIDA POT.</div><div style='color:#ff4d6d;'>-${per_pot:,.2f}</div></div>
        </div>""", unsafe_allow_html=True)
        if st.button("✅ Registrar Inversión",key="btn_add"):
            add_trade(ts,tbp,tsh,tbd,ttp,tsl,tnotes)
            st.success(f"✅ Inversión en {ts} registrada."); st.rerun()

    open_trades=[t for t in st.session_state.trades if t["status"]=="ABIERTA"]
    closed_trades=[t for t in st.session_state.trades if t["status"]!="ABIERTA"]

    if not st.session_state.trades:
        st.markdown("<div style='background:#0d1117;border:1px dashed #1f2937;border-radius:10px;padding:40px;text-align:center;'><div style='font-size:32px;'>📂</div><div style='color:#4b5563;font-family:Space Mono;font-size:12px;margin-top:8px;'>No hay operaciones registradas todavía.</div></div>", unsafe_allow_html=True)
    else:
        ti=sum(t["invested"] for t in st.session_state.trades)
        tp_total=sum(t.get("pnl",0) for t in closed_trades)
        sm1,sm2,sm3,sm4=st.columns(4)
        sm1.metric("Total Invertido",f"${ti:,.2f}")
        sm2.metric("Posiciones Abiertas",str(len(open_trades)))
        sm3.metric("Cerradas",str(len(closed_trades)))
        sm4.metric("P&L Realizado",f"${tp_total:+,.2f}","ganancia" if tp_total>=0 else "pérdida")
        st.markdown("<br>", unsafe_allow_html=True)

        if open_trades:
            st.markdown("#### 🟢 Posiciones Abiertas")
            for i,trade in enumerate(open_trades):
                oi=st.session_state.trades.index(trade)
                try:
                    cpd=fetch_data(trade["symbol"],"1d","1h")
                    cp=cpd["close"].iloc[-1] if not cpd.empty else trade["buy_price"]
                except: cp=trade["buy_price"]
                up=round((cp-trade["buy_price"])*trade["shares"],2)
                upc=round((cp-trade["buy_price"])/trade["buy_price"]*100,2)
                pc="#00ff9d" if up>=0 else "#ff4d6d"
                if cp>=trade["tp_price"]: am,ac,ab="🎯 ¡TAKE PROFIT ALCANZADO! Considera vender ahora.","#00ff9d","#00ff9d15"
                elif cp<=trade["sl_price"]: am,ac,ab="🛑 STOP LOSS ALCANZADO. Evalúa cerrar posición.","#ff4d6d","#ff4d6d15"
                elif upc>=trade["tp_pct"]*0.7: am,ac,ab="⚡ Cerca del Take Profit. Mantente atento.","#ffd60a","#ffd60a10"
                else: am,ac,ab="⏳ Posición activa. Sin señal de salida todavía.","#4b5563","#1f293710"
                rt=trade["tp_price"]-trade["sl_price"]
                prog=max(0,min(1,(cp-trade["sl_price"])/rt)) if rt>0 else 0.5
                st.markdown(f"""
                <div style='background:#0d1117;border:1px solid #1f2937;border-radius:10px;padding:18px;margin-bottom:12px;'>
                  <div style='display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;flex-wrap:wrap;gap:8px;'>
                    <div>
                      <span style='color:#fff;font-family:Space Mono;font-weight:700;font-size:16px;'>{trade["symbol"]}</span>
                      <span style='color:#4b5563;font-size:11px;margin-left:10px;'>{trade["shares"]} acciones · {trade["buy_date"]}</span>
                      {f'<div style="color:#6b7280;font-size:10px;font-style:italic;margin-top:2px;">{trade["notes"]}</div>' if trade["notes"] else ""}
                    </div>
                    <div style='text-align:right;'>
                      <div style='color:#fff;font-family:Space Mono;font-size:18px;font-weight:700;'>${cp:,.2f}</div>
                      <div style='color:{pc};font-family:Space Mono;'>{upc:+.2f}% ({up:+,.2f} USD)</div>
                    </div>
                  </div>
                  <div style='display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:12px;font-family:Space Mono;font-size:10px;'>
                    <div style='background:#060a0f;border-radius:6px;padding:8px;text-align:center;'>
                      <div style='color:#4b5563;font-size:9px;'>COMPRA</div><div style='color:#9ca3af;'>${trade["buy_price"]:,.2f}</div>
                    </div>
                    <div style='background:#060a0f;border:1px solid #00ff9d30;border-radius:6px;padding:8px;text-align:center;'>
                      <div style='color:#4b5563;font-size:9px;'>TP 🎯</div><div style='color:#00ff9d;'>${trade["tp_price"]:,.2f}</div>
                    </div>
                    <div style='background:#060a0f;border:1px solid #ff4d6d30;border-radius:6px;padding:8px;text-align:center;'>
                      <div style='color:#4b5563;font-size:9px;'>SL 🛑</div><div style='color:#ff4d6d;'>${trade["sl_price"]:,.2f}</div>
                    </div>
                    <div style='background:#060a0f;border-radius:6px;padding:8px;text-align:center;'>
                      <div style='color:#4b5563;font-size:9px;'>INVERTIDO</div><div style='color:#9ca3af;'>${trade["invested"]:,.2f}</div>
                    </div>
                  </div>
                  <div style='margin-bottom:10px;'>
                    <div style='display:flex;justify-content:space-between;font-size:9px;color:#4b5563;margin-bottom:4px;'>
                      <span>SL ${trade["sl_price"]:,.2f}</span><span>${cp:,.2f}</span><span>TP ${trade["tp_price"]:,.2f}</span>
                    </div>
                    <div style='background:#1f2937;border-radius:4px;height:6px;position:relative;overflow:visible;'>
                      <div style='background:linear-gradient(90deg,#ff4d6d,#ffd60a,#00ff9d);border-radius:4px;height:6px;width:100%;opacity:0.3;'></div>
                      <div style='position:absolute;top:-3px;left:{prog*100:.1f}%;transform:translateX(-50%);width:12px;height:12px;background:#fff;border-radius:50%;border:2px solid #0d1117;'></div>
                    </div>
                  </div>
                  <div style='background:{ab};border:1px solid {ac}40;border-radius:6px;padding:8px 12px;font-size:11px;color:{ac};'>{am}</div>
                </div>""", unsafe_allow_html=True)
                with st.expander(f"💰 Cerrar posición {trade['symbol']}"):
                    sc1,sc2=st.columns(2)
                    with sc1: sp=st.number_input("Precio de venta",min_value=0.01,value=float(round(cp,2)),step=0.01,key=f"sp{oi}")
                    with sc2: sd=st.date_input("Fecha de venta",value=pd.Timestamp.today(),key=f"sd{oi}")
                    pp=round((sp-trade["buy_price"])*trade["shares"],2)
                    ppp=round((sp-trade["buy_price"])/trade["buy_price"]*100,2)
                    st.markdown(f"<div style='background:#060a0f;border:1px solid #1f2937;border-radius:6px;padding:10px;font-family:Space Mono;font-size:12px;text-align:center;margin:8px 0;'>P&L: <span style='color:{'#00ff9d' if pp>=0 else '#ff4d6d'};font-size:16px;font-weight:700;'>{pp:+,.2f} USD ({ppp:+.2f}%)</span></div>", unsafe_allow_html=True)
                    if st.button(f"Confirmar cierre",key=f"close{oi}"):
                        close_trade(oi,sp,sd); st.success("Posición cerrada."); st.rerun()

        if closed_trades:
            st.markdown("<br>#### 📋 Historial Cerrado")
            rows=[{"Acción":t["symbol"],"Compra":f"${t['buy_price']:,.2f}","Venta":f"${t['sell_price']:,.2f}",
                   "Acciones":t["shares"],"P&L":f"${t.get('pnl',0):+,.2f}","Rendimiento":f"{t.get('pnl_pct',0):+.2f}%",
                   "Estado":t["status"],"Comprado":t["buy_date"],"Vendido":t["sell_date"]} for t in closed_trades]
            st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
            if len(closed_trades)>1:
                pnl_vals=[t.get("pnl",0) for t in closed_trades]
                pnl_syms=[f"{t['symbol']}" for t in closed_trades]
                fig_pnl=go.Figure()
                fig_pnl.add_trace(go.Bar(x=pnl_syms,y=pnl_vals,marker_color=["#00ff9d" if v>=0 else "#ff4d6d" for v in pnl_vals]))
                fig_pnl.add_trace(go.Scatter(x=pnl_syms,y=pd.Series(pnl_vals).cumsum().tolist(),name="Acumulado",line=dict(color="#ffd60a",width=2),mode="lines+markers"))
                fig_pnl.update_layout(template="plotly_dark",plot_bgcolor="#0d1117",paper_bgcolor="#0d1117",height=250,margin=dict(l=0,r=0,t=20,b=0),showlegend=False)
                st.plotly_chart(fig_pnl,use_container_width=True)

        if st.button("🗑️  Borrar historial"): st.session_state.trades=[]; st.rerun()

# ── TAB 6: ALERTAS POR CORREO ─────────────────────────────────────────────────
with t6:
    st.markdown("### 🔔 Alertas por Correo Electrónico")
    st.markdown("<br>", unsafe_allow_html=True)

    # Instrucciones paso a paso
    with st.expander("📖 ¿Cómo configurar? Guía paso a paso (léeme primero)", expanded=True):
        st.markdown("""
        <div style='background:#0d1117;border:1px solid #1f2937;border-radius:8px;padding:20px;font-size:12px;line-height:1.9;color:#9ca3af;'>

        <div style='color:#ffd60a;font-weight:700;font-size:14px;margin-bottom:12px;'>⚙️ Configuración Gmail — 3 pasos sencillos</div>

        <div style='margin-bottom:16px;'>
          <span style='color:#00ff9d;font-weight:700;'>Paso 1:</span> Activa la verificación en 2 pasos en tu cuenta Gmail<br>
          <span style='color:#4b5563;font-size:11px;'>→ gmail.com → Configuración → Seguridad → Verificación en 2 pasos → Activar</span>
        </div>

        <div style='margin-bottom:16px;'>
          <span style='color:#00ff9d;font-weight:700;'>Paso 2:</span> Crea una "Contraseña de aplicación" (es diferente a tu contraseña normal)<br>
          <span style='color:#4b5563;font-size:11px;'>→ myaccount.google.com/apppasswords → Selecciona "Otra" → Escribe "QuantumTrade" → Generar<br>
          → Te dará un código de 16 letras tipo: <span style='color:#ffd60a;font-family:monospace;'>xxxx xxxx xxxx xxxx</span> — ese es el que usas aquí</span>
        </div>

        <div style='margin-bottom:16px;'>
          <span style='color:#00ff9d;font-weight:700;'>Paso 3:</span> Ingresa tus datos abajo y activa las alertas<br>
          <span style='color:#4b5563;font-size:11px;'>→ Correo que envía = tu Gmail · Contraseña = el código de 16 letras del Paso 2<br>
          → Correo destino = donde quieres recibir las alertas (puede ser el mismo u otro)</span>
        </div>

        <div style='background:#00ff9d10;border:1px solid #00ff9d30;border-radius:6px;padding:10px;margin-top:8px;'>
          🔒 <span style='color:#6b7280;font-size:11px;'>Tu contraseña se guarda solo en tu sesión activa y nunca se almacena en ningún servidor.</span>
        </div>

        <div style='background:#ffd60a10;border:1px solid #ffd60a30;border-radius:6px;padding:10px;margin-top:8px;'>
          💡 <span style='color:#6b7280;font-size:11px;'>Las alertas se disparan automáticamente cuando el precio de alguna de tus posiciones abiertas 
          toca el Take Profit o el Stop Loss que configuraste.</span>
        </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_form, col_status = st.columns([1, 1])

    with col_form:
        st.markdown("<div style='color:#9ca3af;font-size:13px;font-weight:600;margin-bottom:12px;'>⚙️ Configuración</div>", unsafe_allow_html=True)
        email_to   = st.text_input("📨 Correo donde recibir alertas", value=st.session_state.email_config.get("to",""), placeholder="tu@correo.com", key="eto")
        email_from = st.text_input("📤 Tu Gmail (el que envía)", value=st.session_state.email_config.get("from",""), placeholder="tucorreo@gmail.com", key="efrom")
        email_pass = st.text_input("🔑 Contraseña de aplicación (16 letras)", value=st.session_state.email_config.get("pass",""), type="password", placeholder="xxxx xxxx xxxx xxxx", key="epass")
        alerts_on  = st.toggle("🔔 Activar alertas automáticas", value=st.session_state.email_config.get("active", False), key="aon")

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("💾 Guardar configuración"):
                st.session_state.email_config = {"to":email_to,"from":email_from,"pass":email_pass,"active":alerts_on}
                st.success("✅ Configuración guardada.")

        with col_b2:
            if st.button("🧪 Enviar correo de prueba"):
                if email_to and email_from and email_pass:
                    html_test = build_buy_email(symbol, price_now, sig, sig["reasons"], proj_tp, proj_sl, kelly_pct*100, invest_amt, ALL_STOCKS[symbol])
                    ok,msg = send_email_alert(email_to, email_from, email_pass, f"🧪 PRUEBA — Quantum Trade {symbol}", html_test)
                    if ok: st.success(msg)
                    else:  st.error(msg)
                else:
                    st.warning("Completa todos los campos primero.")

        # Alerta manual de compra
        st.markdown("<br><div style='color:#9ca3af;font-size:13px;font-weight:600;margin-bottom:8px;'>📤 Enviar alerta manual</div>", unsafe_allow_html=True)
        alert_symbol = st.selectbox("Acción", list(ALL_STOCKS.keys()), index=list(ALL_STOCKS.keys()).index(symbol), key="as2")
        alert_type   = st.radio("Tipo de alerta", ["🟢 Señal de COMPRA","🔴 Señal de VENTA"], horizontal=True, key="at")

        if st.button("📧 Enviar alerta ahora", key="send_manual"):
            if email_to and email_from and email_pass:
                if "COMPRA" in alert_type:
                    html_m = build_buy_email(alert_symbol, price_now, sig, sig["reasons"], proj_tp, proj_sl, kelly_pct*100, invest_amt, ALL_STOCKS[alert_symbol])
                    subj   = f"🟢 SEÑAL COMPRA — {alert_symbol} ${price_now:,.2f}"
                else:
                    html_m = build_sell_email(alert_symbol, price_now, price_now, 0, 0, "Señal de venta manual")
                    subj   = f"🔴 SEÑAL VENTA — {alert_symbol} ${price_now:,.2f}"
                ok,msg = send_email_alert(email_to, email_from, email_pass, subj, html_m)
                if ok:
                    st.success(msg)
                    st.session_state.alert_log.append({"time":datetime.now().strftime("%H:%M"),"msg":f"Alerta manual {alert_symbol} enviada","color":"#00ff9d"})
                else: st.error(msg)
            else:
                st.warning("Configura primero tu correo.")

    with col_status:
        st.markdown("<div style='color:#9ca3af;font-size:13px;font-weight:600;margin-bottom:12px;'>📊 Estado del sistema</div>", unsafe_allow_html=True)
        cfg_now = st.session_state.email_config
        status_color = "#00ff9d" if cfg_now.get("active") else "#4b5563"
        st.markdown(f"""
        <div style='background:#0d1117;border:1px solid #1f2937;border-radius:10px;padding:18px;'>
          <div style='display:flex;align-items:center;gap:8px;margin-bottom:16px;'>
            <div style='width:10px;height:10px;border-radius:50%;background:{status_color};{"box-shadow:0 0 8px "+status_color if cfg_now.get("active") else ""};'></div>
            <span style='color:{status_color};font-family:Space Mono;font-size:12px;font-weight:700;'>
              {"ALERTAS ACTIVAS" if cfg_now.get("active") else "ALERTAS INACTIVAS"}
            </span>
          </div>
          <div style='font-size:11px;color:#4b5563;line-height:2;font-family:Space Mono;'>
            <div>Destino: <span style='color:#9ca3af;'>{cfg_now.get("to","No configurado") or "No configurado"}</span></div>
            <div>Emisor: <span style='color:#9ca3af;'>{cfg_now.get("from","No configurado") or "No configurado"}</span></div>
            <div>Posiciones monitoreadas: <span style='color:#00ff9d;'>{len(open_trades)}</span></div>
          </div>
          <div style='margin-top:14px;padding-top:14px;border-top:1px solid #1f2937;'>
            <div style='color:#4b5563;font-size:9px;letter-spacing:2px;margin-bottom:8px;'>TIPOS DE ALERTA AUTOMÁTICA</div>
            <div style='font-size:11px;color:#6b7280;line-height:1.9;'>
              🎯 <span style='color:#00ff9d;'>Take Profit alcanzado</span> → alerta de venta con ganancia<br>
              🛑 <span style='color:#ff4d6d;'>Stop Loss tocado</span> → alerta urgente de salida<br>
              📊 <span style='color:#ffd60a;'>Señal fuerte (≥75%)</span> → alerta de posible compra
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Log de alertas enviadas
        if st.session_state.alert_log:
            st.markdown("<br><div style='color:#9ca3af;font-size:12px;font-weight:600;margin-bottom:8px;'>📋 Registro de alertas enviadas</div>", unsafe_allow_html=True)
            for log in reversed(st.session_state.alert_log[-10:]):
                st.markdown(f"<div style='background:#060a0f;border-left:3px solid {log['color']};padding:6px 10px;margin-bottom:4px;font-size:11px;color:#6b7280;font-family:Space Mono;'>[{log['time']}] {log['msg']}</div>", unsafe_allow_html=True)

    # ── Panel del escáner automático ─────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 🔍 Escáner Automático — Todas las acciones")

    tiempo_restante = max(0, SCAN_INTERVAL - (time.time() - st.session_state.last_scan_time))
    minutos = int(tiempo_restante // 60)
    segundos = int(tiempo_restante % 60)
    scan_pct = int((1 - tiempo_restante / SCAN_INTERVAL) * 100)
    ultimo_scan = datetime.fromtimestamp(st.session_state.last_scan_time).strftime("%H:%M:%S") if st.session_state.last_scan_time > 0 else "Nunca"

    scanner_active = cfg.get("active") and cfg.get("to") and cfg.get("from") and cfg.get("pass")
    scanner_color  = "#00ff9d" if scanner_active else "#4b5563"
    scanner_label  = "ACTIVO" if scanner_active else "INACTIVO — configura tu correo primero"

    st.markdown(f"""
    <div style='background:#0d1117;border:1px solid #1f2937;border-radius:10px;padding:20px;margin-bottom:16px;'>
      <div style='display:flex;align-items:center;gap:8px;margin-bottom:16px;'>
        <div style='width:10px;height:10px;border-radius:50%;background:{scanner_color};
                    {"box-shadow:0 0 10px "+scanner_color if scanner_active else ""};'></div>
        <span style='color:{scanner_color};font-family:Space Mono;font-size:13px;font-weight:700;'>ESCÁNER {scanner_label}</span>
      </div>

      <div style='display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px;'>
        <div style='background:#060a0f;border:1px solid #1f2937;border-radius:8px;padding:12px;text-align:center;'>
          <div style='color:#4b5563;font-size:9px;letter-spacing:1px;'>ACCIONES VIGILADAS</div>
          <div style='color:#00ff9d;font-family:Space Mono;font-size:22px;font-weight:700;margin-top:4px;'>{len(ALL_STOCKS)}</div>
          <div style='color:#4b5563;font-size:10px;'>en tiempo real</div>
        </div>
        <div style='background:#060a0f;border:1px solid #1f2937;border-radius:8px;padding:12px;text-align:center;'>
          <div style='color:#4b5563;font-size:9px;letter-spacing:1px;'>PRÓXIMO ESCANEO</div>
          <div style='color:#ffd60a;font-family:Space Mono;font-size:22px;font-weight:700;margin-top:4px;'>{minutos:02d}:{segundos:02d}</div>
          <div style='color:#4b5563;font-size:10px;'>cada 5 minutos</div>
        </div>
        <div style='background:#060a0f;border:1px solid #1f2937;border-radius:8px;padding:12px;text-align:center;'>
          <div style='color:#4b5563;font-size:9px;letter-spacing:1px;'>ÚLTIMO ESCANEO</div>
          <div style='color:#9ca3af;font-family:Space Mono;font-size:18px;font-weight:700;margin-top:4px;'>{ultimo_scan}</div>
          <div style='color:#4b5563;font-size:10px;'>señales: {len(st.session_state.scanner_results)}</div>
        </div>
      </div>

      <div style='background:#1f2937;border-radius:4px;height:6px;margin-bottom:8px;'>
        <div style='background:linear-gradient(90deg,#00ff9d,#ffd60a);border-radius:4px;height:6px;width:{scan_pct}%;transition:width 1s;'></div>
      </div>
      <div style='color:#4b5563;font-size:10px;text-align:right;'>{scan_pct}% completado</div>

      <div style='margin-top:12px;padding-top:12px;border-top:1px solid #1f2937;font-size:11px;color:#6b7280;line-height:1.9;'>
        🟢 Alerta de <strong style='color:#00ff9d;'>COMPRA</strong> cuando señal ≥ 65% y RSI &lt; 40 o cruce alcista de medias<br>
        🔴 Alerta de <strong style='color:#ff4d6d;'>VENTA</strong> cuando señal ≤ 35% o sobrecompra extrema<br>
        🎯 Alerta de <strong style='color:#ffd60a;'>TP/SL</strong> cuando tus posiciones abiertas tocan el precio objetivo<br>
        📧 Solo envía correo cuando la señal <strong style='color:#fff;'>CAMBIA</strong> — no spamea con la misma señal dos veces
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Botón escaneo manual
    col_scan1, col_scan2 = st.columns([1, 3])
    with col_scan1:
        if st.button("🔍 Escanear ahora", key="scan_now"):
            if scanner_active:
                with st.spinner("Escaneando todas las acciones..."):
                    results = run_full_scanner(cfg, st.session_state.trades)
                if results:
                    st.success(f"✅ {len(results)} señales detectadas. Correo enviado.")
                else:
                    st.info("Sin señales nuevas en este momento.")
            else:
                st.warning("Configura y activa tu correo primero.")

    # ── Últimas señales detectadas ────────────────────────────────────────────
    if st.session_state.scanner_results:
        st.markdown("<br>**📋 Últimas señales detectadas:**", unsafe_allow_html=False)
        for r in st.session_state.scanner_results[:15]:
            ic = "🟢" if r["type"] == "COMPRAR" else ("🔴" if r["type"] == "VENDER" else ("🎯" if "TP" in r["type"] else "🛑"))
            st.markdown(f"""
            <div style='background:#060a0f;border-left:3px solid {r["color"]};border-radius:0 6px 6px 0;
                        padding:8px 14px;margin-bottom:4px;display:flex;justify-content:space-between;align-items:center;'>
              <div>
                <span style='color:#fff;font-family:Space Mono;font-weight:700;'>{ic} {r["symbol"]}</span>
                <span style='color:{r["color"]};font-family:Space Mono;font-size:11px;margin-left:10px;'>{r["type"]}</span>
                <span style='color:#4b5563;font-size:10px;margin-left:8px;'>${r["price"]:,.2f} · fuerza {r["strength"]}%</span>
                <div style='color:#6b7280;font-size:10px;margin-top:2px;'>{r["reason"]}</div>
              </div>
              <span style='color:#374151;font-family:Space Mono;font-size:10px;'>{r["time"]}</span>
            </div>
            """, unsafe_allow_html=True)
        if st.button("🗑️ Limpiar historial de señales", key="clear_scan"):
            st.session_state.scanner_results = []; st.rerun()

# ── TAB 7: BROKERS ────────────────────────────────────────────────────────────
with t7:
    st.markdown("### 🏦 Brokers Recomendados — Empieza con poco, crece seguro")
    st.markdown("<br>", unsafe_allow_html=True)

    # Card principal — Recomendación para principiantes Colombia
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#00ff9d10,#0ea5e910);border:2px solid #00ff9d50;border-radius:12px;padding:20px;margin-bottom:20px;'>
      <div style='color:#00ff9d;font-size:11px;letter-spacing:2px;font-weight:700;margin-bottom:8px;'>⭐ RECOMENDACIÓN PARA EMPEZAR DESDE COLOMBIA</div>
      <div style='display:flex;gap:16px;flex-wrap:wrap;align-items:center;'>
        <div style='flex:1;min-width:200px;'>
          <div style='color:#fff;font-size:20px;font-weight:700;margin-bottom:4px;'>XTB + SPY ETF</div>
          <div style='color:#9ca3af;font-size:12px;line-height:1.7;'>
            Abre cuenta en XTB (gratis, sin mínimo), compra fracciones del ETF <strong style='color:#00ff9d;'>SPY</strong> que replica las 500 mejores empresas de EEUU.<br>
            Con solo <strong style='color:#ffd60a;'>$10–$50 USD</strong> al mes, en 10 años habrás construido un patrimonio real.<br>
            Rendimiento histórico SPY: <strong style='color:#00ff9d;'>~10% anual promedio</strong> en los últimos 30 años.
          </div>
        </div>
        <div style='text-align:center;min-width:140px;'>
          <div style='color:#4b5563;font-size:10px;'>$50/mes durante 10 años</div>
          <div style='color:#00ff9d;font-family:Space Mono;font-size:28px;font-weight:700;'>~$10,200</div>
          <div style='color:#4b5563;font-size:10px;'>invertidos → <span style='color:#ffd60a;'>~$14,000+ USD</span></div>
          <div style='color:#4b5563;font-size:9px;margin-top:4px;'>(asumiendo 10% anual)</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Grid de brokers
    col_left, col_right = st.columns(2)
    pal=["#00ff9d","#0ea5e9","#a78bfa","#ffd60a","#f97316","#ec4899"]

    for i, b in enumerate(BROKERS_INFO):
        col = col_left if i % 2 == 0 else col_right
        c   = pal[i]
        acc_badge = f"<span style='background:#00ff9d20;color:#00ff9d;padding:2px 8px;border-radius:3px;font-size:10px;'>✅ Disponible en Colombia</span>" if b["acceso_colombia"] else "<span style='background:#ff4d6d20;color:#ff4d6d;padding:2px 8px;border-radius:3px;font-size:10px;'>⚠️ Disponibilidad limitada Colombia</span>"
        frac_badge = "<span style='background:#0ea5e920;color:#0ea5e9;padding:2px 8px;border-radius:3px;font-size:10px;'>🔢 Acciones fraccionadas</span>" if b["acepta_fraccion"] else ""
        ventajas_html = "".join([f"<div style='color:#6b7280;font-size:11px;'>{v}</div>" for v in b["ventajas"]])
        stars = "".join([f'<span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:{""+c if j<int(b["rating"]) else "#1f2937"};margin-right:2px;"></span>' for j in range(10)])

        with col:
            st.markdown(f"""
            <div style='background:#0d1117;border:1px solid #1f2937;border-top:3px solid {c};border-radius:10px;padding:18px;margin-bottom:16px;'>
              <div style='display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;'>
                <div>
                  <div style='color:#fff;font-weight:700;font-size:15px;'>{b["name"]}</div>
                  <div style='color:#4b5563;font-size:10px;margin-top:2px;'>{b["url"]}</div>
                </div>
                <div style='color:{c};font-family:Space Mono;font-size:20px;font-weight:700;'>{b["rating"]}</div>
              </div>
              <div style='margin-bottom:8px;'>{acc_badge} {frac_badge}</div>
              <div style='background:{c}15;border:1px solid {c}40;border-radius:4px;padding:6px 10px;margin-bottom:10px;font-size:11px;color:{c};font-weight:600;'>{b["ideal_para"]}</div>
              <div style='color:#9ca3af;font-size:11px;margin-bottom:10px;line-height:1.6;'>{b["descripcion"]}</div>
              <div style='margin-bottom:10px;'>{ventajas_html}</div>
              <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;'>
                <span style='color:#00ff9d;font-family:Space Mono;font-size:11px;'>💰 Comisión: {b["fee"]}</span>
                <span style='color:#4b5563;font-family:Space Mono;font-size:11px;'>Mín: {b["min_deposit"]}</span>
              </div>
              <div>{stars}</div>
              <div style='background:#0ea5e910;border:1px solid #0ea5e930;border-radius:4px;padding:6px 10px;margin-top:10px;font-size:11px;color:#0ea5e9;'>{b["para_empezar"]}</div>
            </div>
            """, unsafe_allow_html=True)

    # Estrategia para principiante
    st.markdown("""
    <div style='background:#0d1117;border:1px solid #1f2937;border-radius:12px;padding:24px;margin-top:8px;'>
      <div style='color:#ffd60a;font-size:14px;font-weight:700;margin-bottom:16px;'>📚 Estrategia recomendada para empezar lento pero seguro</div>
      <div style='display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:16px;'>
        <div style='background:#060a0f;border:1px solid #00ff9d30;border-radius:8px;padding:14px;text-align:center;'>
          <div style='font-size:24px;margin-bottom:6px;'>1️⃣</div>
          <div style='color:#00ff9d;font-weight:700;font-size:12px;margin-bottom:6px;'>Meses 1–3</div>
          <div style='color:#6b7280;font-size:11px;line-height:1.7;'>Abre cuenta XTB. Invierte $10–$20 en SPY cada semana. Aprende a leer la app sin presión.</div>
        </div>
        <div style='background:#060a0f;border:1px solid #0ea5e930;border-radius:8px;padding:14px;text-align:center;'>
          <div style='font-size:24px;margin-bottom:6px;'>2️⃣</div>
          <div style='color:#0ea5e9;font-weight:700;font-size:12px;margin-bottom:6px;'>Meses 4–12</div>
          <div style='color:#6b7280;font-size:11px;line-height:1.7;'>Agrega 1 o 2 acciones individuales de bajo riesgo (AAPL, MSFT, V). Usa esta app para señales.</div>
        </div>
        <div style='background:#060a0f;border:1px solid #ffd60a30;border-radius:8px;padding:14px;text-align:center;'>
          <div style='font-size:24px;margin-bottom:6px;'>3️⃣</div>
          <div style='color:#ffd60a;font-weight:700;font-size:12px;margin-bottom:6px;'>Año 2+</div>
          <div style='color:#6b7280;font-size:11px;line-height:1.7;'>Diversifica más sectores. Activa las alertas automáticas. Considera IBKR para mejores herramientas.</div>
        </div>
      </div>
      <div style='color:#4b5563;font-size:11px;line-height:1.8;'>
        💡 <strong style='color:#9ca3af;'>La regla más importante:</strong> Nunca inviertas dinero que necesites en los próximos 12 meses. 
        Las inversiones en el mercado de valores son para largo plazo (3+ años). La paciencia es tu mayor ventaja competitiva.
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='background:#0d1117;border:1px solid #ffd60a40;border-radius:10px;padding:16px;margin-top:12px;'>
      <div style='color:#ffd60a;font-size:12px;font-weight:600;margin-bottom:8px;'>⚠️ Aviso Legal</div>
      <div style='color:#6b7280;font-size:11px;line-height:1.8;'>Este dashboard es una <strong style='color:#9ca3af;'>herramienta educativa de análisis técnico</strong>.
      Las señales son generadas por algoritmos y <strong style='color:#ff4d6d;'>no garantizan rentabilidad ni constituyen asesoría financiera certificada</strong>.
      Toda inversión conlleva riesgo de pérdida. Consulta con un asesor financiero antes de invertir montos significativos.</div>
    </div>
    """, unsafe_allow_html=True)

# ─── AUTO REFRESH ─────────────────────────────────────────────────────────────
# Refresca cada 30s para actualizar el contador del escáner y detectar señales
if auto_ref:
    time.sleep(30)
    st.rerun()
