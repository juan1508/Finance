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

st.set_page_config(page_title="Quantum Trade | AI Analytics", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

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
.stTabs [data-baseweb="tab"]{background:transparent!important;color:#4b5563!important;font-family:'Space Mono',monospace!important;font-size:10px!important;letter-spacing:1px;border-bottom:2px solid transparent!important;}
.stTabs [aria-selected="true"]{color:#00ff9d!important;border-bottom:2px solid #00ff9d!important;}
div[data-testid="stExpander"]{background:#0d1117!important;border:1px solid #1f2937!important;border-radius:8px!important;}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# UNIVERSO COMPLETO — 120+ ACTIVOS
# ═══════════════════════════════════════════════════════════════════════════════
ALL_ASSETS = {
    # ── ACCIONES USA — TECNOLOGÍA ──────────────────────────────────────────
    "AAPL":  {"name":"Apple",              "tipo":"Acción","sector":"Tecnología",   "riesgo":"Bajo",   "div":True,  "broker":"XTB / IBKR",   "min_usd":1,  "desc":"La empresa más grande del mundo."},
    "MSFT":  {"name":"Microsoft",          "tipo":"Acción","sector":"Tecnología",   "riesgo":"Bajo",   "div":True,  "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Nube Azure + IA. Crecimiento constante."},
    "GOOGL": {"name":"Alphabet (Google)",  "tipo":"Acción","sector":"Tecnología",   "riesgo":"Bajo",   "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Dominio en búsquedas y publicidad."},
    "NVDA":  {"name":"NVIDIA",             "tipo":"Acción","sector":"Tecnología",   "riesgo":"Medio",  "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Chips de IA. Alto potencial."},
    "META":  {"name":"Meta Platforms",     "tipo":"Acción","sector":"Tecnología",   "riesgo":"Medio",  "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Facebook+Instagram+WhatsApp."},
    "AMZN":  {"name":"Amazon",             "tipo":"Acción","sector":"Tecnología",   "riesgo":"Medio",  "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"E-commerce + AWS cloud líder."},
    "TSLA":  {"name":"Tesla",              "tipo":"Acción","sector":"Automotriz",   "riesgo":"Alto",   "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Eléctricos. Muy volátil."},
    "ORCL":  {"name":"Oracle",             "tipo":"Acción","sector":"Tecnología",   "riesgo":"Bajo",   "div":True,  "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Bases de datos y nube empresarial."},
    "ADBE":  {"name":"Adobe",              "tipo":"Acción","sector":"Tecnología",   "riesgo":"Medio",  "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Software creativo por suscripción."},
    "CRM":   {"name":"Salesforce",         "tipo":"Acción","sector":"Tecnología",   "riesgo":"Medio",  "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"CRM empresarial #1 del mundo."},
    "NFLX":  {"name":"Netflix",            "tipo":"Acción","sector":"Tecnología",   "riesgo":"Medio",  "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Streaming dominante global."},
    "AMD":   {"name":"AMD",                "tipo":"Acción","sector":"Tecnología",   "riesgo":"Alto",   "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Competidor de NVIDIA en chips IA."},
    "INTC":  {"name":"Intel",              "tipo":"Acción","sector":"Tecnología",   "riesgo":"Medio",  "div":True,  "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Semiconductores. Precio castigado."},
    "PYPL":  {"name":"PayPal",             "tipo":"Acción","sector":"Tecnología",   "riesgo":"Medio",  "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Pagos digitales globales."},
    "UBER":  {"name":"Uber",               "tipo":"Acción","sector":"Tecnología",   "riesgo":"Medio",  "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Movilidad y delivery global."},
    "SHOP":  {"name":"Shopify",            "tipo":"Acción","sector":"Tecnología",   "riesgo":"Alto",   "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"E-commerce para PYMES. Alto crecimiento."},
    "SNOW":  {"name":"Snowflake",          "tipo":"Acción","sector":"Tecnología",   "riesgo":"Alto",   "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Data cloud. Alto potencial."},
    "PLTR":  {"name":"Palantir",           "tipo":"Acción","sector":"Tecnología",   "riesgo":"Alto",   "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"IA para gobiernos y empresas."},
    # ── ACCIONES USA — FINANZAS ────────────────────────────────────────────
    "JPM":   {"name":"JPMorgan Chase",     "tipo":"Acción","sector":"Finanzas",     "riesgo":"Bajo",   "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Banco más grande de EEUU."},
    "V":     {"name":"Visa",               "tipo":"Acción","sector":"Finanzas",     "riesgo":"Bajo",   "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Red de pagos global. Muy estable."},
    "MA":    {"name":"Mastercard",         "tipo":"Acción","sector":"Finanzas",     "riesgo":"Bajo",   "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Igual de estable que Visa."},
    "BRK-B": {"name":"Berkshire Hathaway", "tipo":"Acción","sector":"Finanzas",     "riesgo":"Bajo",   "div":False, "broker":"XTB / Schwab", "min_usd":1,  "desc":"El portafolio de Warren Buffett."},
    "GS":    {"name":"Goldman Sachs",      "tipo":"Acción","sector":"Finanzas",     "riesgo":"Medio",  "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Banco de inversión élite."},
    "BAC":   {"name":"Bank of America",    "tipo":"Acción","sector":"Finanzas",     "riesgo":"Bajo",   "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Segundo banco más grande de EEUU."},
    "AXP":   {"name":"American Express",   "tipo":"Acción","sector":"Finanzas",     "riesgo":"Bajo",   "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Tarjetas premium. Clientes fieles."},
    "BLK":   {"name":"BlackRock",          "tipo":"Acción","sector":"Finanzas",     "riesgo":"Bajo",   "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Gestora de activos más grande del mundo."},
    # ── ACCIONES USA — SALUD ──────────────────────────────────────────────
    "JNJ":   {"name":"Johnson & Johnson",  "tipo":"Acción","sector":"Salud",        "riesgo":"Bajo",   "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"60+ años aumentando dividendo."},
    "UNH":   {"name":"UnitedHealth",       "tipo":"Acción","sector":"Salud",        "riesgo":"Bajo",   "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Seguro médico más grande de EEUU."},
    "PFE":   {"name":"Pfizer",             "tipo":"Acción","sector":"Salud",        "riesgo":"Medio",  "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Farmacéutica gigante. Precio bajo."},
    "ABBV":  {"name":"AbbVie",             "tipo":"Acción","sector":"Salud",        "riesgo":"Bajo",   "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Farmacéutica con dividendo alto."},
    "MRK":   {"name":"Merck",              "tipo":"Acción","sector":"Salud",        "riesgo":"Bajo",   "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Keytruda anti-cáncer. Muy sólida."},
    "LLY":   {"name":"Eli Lilly",          "tipo":"Acción","sector":"Salud",        "riesgo":"Medio",  "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Medicamentos para diabetes y obesidad."},
    # ── ACCIONES USA — CONSUMO ─────────────────────────────────────────────
    "WMT":   {"name":"Walmart",            "tipo":"Acción","sector":"Consumo",      "riesgo":"Bajo",   "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Retailer #1 del mundo. Resiste crisis."},
    "COST":  {"name":"Costco",             "tipo":"Acción","sector":"Consumo",      "riesgo":"Bajo",   "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Membresías = ingresos recurrentes."},
    "KO":    {"name":"Coca-Cola",          "tipo":"Acción","sector":"Consumo",      "riesgo":"Bajo",   "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"60+ años aumentando dividendo."},
    "MCD":   {"name":"McDonald's",         "tipo":"Acción","sector":"Consumo",      "riesgo":"Bajo",   "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Franquicias. Modelo casi perfecto."},
    "PEP":   {"name":"PepsiCo",            "tipo":"Acción","sector":"Consumo",      "riesgo":"Bajo",   "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Bebidas + snacks. Muy defensiva."},
    "PG":    {"name":"Procter & Gamble",   "tipo":"Acción","sector":"Consumo",      "riesgo":"Bajo",   "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Productos del hogar. Ultra estable."},
    "NKE":   {"name":"Nike",               "tipo":"Acción","sector":"Consumo",      "riesgo":"Bajo",   "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Marca deportiva global #1."},
    "SBUX":  {"name":"Starbucks",          "tipo":"Acción","sector":"Consumo",      "riesgo":"Medio",  "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Café premium global."},
    # ── ACCIONES USA — ENERGÍA ─────────────────────────────────────────────
    "XOM":   {"name":"ExxonMobil",         "tipo":"Acción","sector":"Energía",      "riesgo":"Medio",  "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Petróleo gigante. Dividendo histórico."},
    "CVX":   {"name":"Chevron",            "tipo":"Acción","sector":"Energía",      "riesgo":"Medio",  "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Petróleo y gas. Muy sólida."},
    "NEE":   {"name":"NextEra Energy",     "tipo":"Acción","sector":"Energía",      "riesgo":"Bajo",   "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Energía renovable #1 del mundo."},
    "ENPH":  {"name":"Enphase Energy",     "tipo":"Acción","sector":"Energía",      "riesgo":"Alto",   "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Solar. Alto potencial largo plazo."},
    # ── ACCIONES INTERNACIONALES ──────────────────────────────────────────
    "ASML":  {"name":"ASML Holding",       "tipo":"Acción","sector":"Tecnología",   "riesgo":"Medio",  "div":True,  "broker":"IBKR / Saxo",  "min_usd":1,  "desc":"Máquinas para chips. Monopolio total."},
    "TSM":   {"name":"Taiwan Semiconductor","tipo":"Acción","sector":"Tecnología",  "riesgo":"Medio",  "div":True,  "broker":"IBKR / Saxo",  "min_usd":1,  "desc":"Fabrica los chips de NVDA y AAPL."},
    "BABA":  {"name":"Alibaba",            "tipo":"Acción","sector":"Tecnología",   "riesgo":"Alto",   "div":False, "broker":"IBKR / Saxo",  "min_usd":1,  "desc":"Amazon de China. Precio muy castigado."},
    "SAP":   {"name":"SAP SE",             "tipo":"Acción","sector":"Tecnología",   "riesgo":"Bajo",   "div":True,  "broker":"IBKR / Saxo",  "min_usd":1,  "desc":"Software empresarial #1 Europa."},
    "TM":    {"name":"Toyota",             "tipo":"Acción","sector":"Automotriz",   "riesgo":"Bajo",   "div":True,  "broker":"IBKR / Saxo",  "min_usd":1,  "desc":"Mayor fabricante de autos del mundo."},
    "SONY":  {"name":"Sony Group",         "tipo":"Acción","sector":"Tecnología",   "riesgo":"Medio",  "div":True,  "broker":"IBKR / Saxo",  "min_usd":1,  "desc":"Gaming + entretenimiento + sensores."},
    "NVO":   {"name":"Novo Nordisk",       "tipo":"Acción","sector":"Salud",        "riesgo":"Bajo",   "div":True,  "broker":"IBKR / Saxo",  "min_usd":1,  "desc":"Ozempic (diabetes/obesidad). Líder."},
    # ── COLOMBIA EN NYSE ──────────────────────────────────────────────────
    "EC":    {"name":"Ecopetrol",          "tipo":"Acción","sector":"Energía",      "riesgo":"Medio",  "div":True,  "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Petrolera colombiana en NYSE. Dividendo alto."},
    "CIB":   {"name":"Bancolombia",        "tipo":"Acción","sector":"Finanzas",     "riesgo":"Bajo",   "div":True,  "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Banco más grande de Colombia en NYSE."},
    "GXO":   {"name":"GXO Logistics",      "tipo":"Acción","sector":"Logística",    "riesgo":"Medio",  "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Logística global en crecimiento."},
    # ── ETFs ──────────────────────────────────────────────────────────────
    "SPY":   {"name":"S&P 500 ETF",        "tipo":"ETF",   "sector":"ETF Broad",   "riesgo":"Bajo",   "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Las 500 mejores empresas de EEUU. IDEAL PRINCIPIANTES."},
    "QQQ":   {"name":"Nasdaq 100 ETF",     "tipo":"ETF",   "sector":"ETF Broad",   "riesgo":"Medio",  "div":False, "broker":"XTB / Schwab", "min_usd":1,  "desc":"Top 100 tecnológicas. Alto crecimiento."},
    "VTI":   {"name":"Total Market ETF",   "tipo":"ETF",   "sector":"ETF Broad",   "riesgo":"Bajo",   "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Todo el mercado americano."},
    "VYM":   {"name":"High Dividend ETF",  "tipo":"ETF",   "sector":"ETF Dividend","riesgo":"Bajo",   "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Ingreso pasivo por dividendos."},
    "GLD":   {"name":"Gold ETF (SPDR)",    "tipo":"ETF",   "sector":"ETF Commodity","riesgo":"Bajo",  "div":False, "broker":"XTB / Schwab", "min_usd":1,  "desc":"Oro sin tener lingotes físicos."},
    "SLV":   {"name":"Silver ETF",         "tipo":"ETF",   "sector":"ETF Commodity","riesgo":"Medio", "div":False, "broker":"XTB / Schwab", "min_usd":1,  "desc":"Plata. Mayor volatilidad que el oro."},
    "USO":   {"name":"Oil ETF",            "tipo":"ETF",   "sector":"ETF Commodity","riesgo":"Alto",  "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Petróleo crudo WTI."},
    "TLT":   {"name":"Bonos USA 20Y ETF",  "tipo":"ETF",   "sector":"ETF Bonds",   "riesgo":"Bajo",  "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Bonos del gobierno EEUU largo plazo."},
    "EEM":   {"name":"Emerging Markets ETF","tipo":"ETF",  "sector":"ETF Global",  "riesgo":"Medio", "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Mercados emergentes incluyendo LATAM."},
    "IWM":   {"name":"Russell 2000 ETF",   "tipo":"ETF",   "sector":"ETF Broad",   "riesgo":"Medio", "div":True,  "broker":"XTB / Schwab", "min_usd":1,  "desc":"Pequeñas empresas USA. Mayor potencial."},
    "ARKK":  {"name":"ARK Innovation ETF", "tipo":"ETF",   "sector":"ETF Tech",    "riesgo":"Alto",  "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Innovación disruptiva. Alto riesgo/retorno."},
    # ── CRIPTOMONEDAS ─────────────────────────────────────────────────────
    "BTC-USD":  {"name":"Bitcoin",         "tipo":"Cripto","sector":"Cripto L1",   "riesgo":"Alto",   "div":False, "broker":"Binance / Coinbase","min_usd":1,"desc":"La cripto original. Reserva de valor digital."},
    "ETH-USD":  {"name":"Ethereum",        "tipo":"Cripto","sector":"Cripto L1",   "riesgo":"Alto",   "div":False, "broker":"Binance / Coinbase","min_usd":1,"desc":"Smart contracts. Base del ecosistema DeFi."},
    "BNB-USD":  {"name":"BNB",             "tipo":"Cripto","sector":"Cripto L1",   "riesgo":"Alto",   "div":False, "broker":"Binance",           "min_usd":1,"desc":"Token de Binance. Descuentos en comisiones."},
    "SOL-USD":  {"name":"Solana",          "tipo":"Cripto","sector":"Cripto L1",   "riesgo":"Alto",   "div":False, "broker":"Binance / Coinbase","min_usd":1,"desc":"Blockchain rápida y barata. Ecosistema NFT."},
    "ADA-USD":  {"name":"Cardano",         "tipo":"Cripto","sector":"Cripto L1",   "riesgo":"Alto",   "div":False, "broker":"Binance / Coinbase","min_usd":1,"desc":"Blockchain académica. Alta descentralización."},
    "XRP-USD":  {"name":"XRP (Ripple)",    "tipo":"Cripto","sector":"Cripto Pagos","riesgo":"Alto",   "div":False, "broker":"Binance / Coinbase","min_usd":1,"desc":"Pagos internacionales bancarios."},
    "DOGE-USD": {"name":"Dogecoin",        "tipo":"Cripto","sector":"Cripto Meme", "riesgo":"Muy Alto","div":False,"broker":"Binance / Robinhood","min_usd":1,"desc":"Meme coin. Muy especulativo."},
    "MATIC-USD":{"name":"Polygon",         "tipo":"Cripto","sector":"Cripto L2",   "riesgo":"Alto",   "div":False, "broker":"Binance / Coinbase","min_usd":1,"desc":"Escalabilidad de Ethereum. Capa 2."},
    "AVAX-USD": {"name":"Avalanche",       "tipo":"Cripto","sector":"Cripto L1",   "riesgo":"Alto",   "div":False, "broker":"Binance / Coinbase","min_usd":1,"desc":"Blockchain rápida. Compite con Solana."},
    "LINK-USD": {"name":"Chainlink",       "tipo":"Cripto","sector":"Cripto Infra","riesgo":"Alto",   "div":False, "broker":"Binance / Coinbase","min_usd":1,"desc":"Oráculos blockchain. Infraestructura DeFi."},
    # ── DIVISAS / FOREX ───────────────────────────────────────────────────
    "EURUSD=X": {"name":"Euro / Dólar",    "tipo":"Forex", "sector":"Forex Major", "riesgo":"Bajo",   "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"El par más negociado del mundo."},
    "GBPUSD=X": {"name":"Libra / Dólar",   "tipo":"Forex", "sector":"Forex Major", "riesgo":"Bajo",   "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Libra esterlina vs dólar."},
    "JPYUSD=X": {"name":"Yen / Dólar",     "tipo":"Forex", "sector":"Forex Major", "riesgo":"Bajo",   "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Yen japonés. Activo refugio."},
    "USDBRL=X": {"name":"Dólar / Real BR", "tipo":"Forex", "sector":"Forex LATAM", "riesgo":"Medio",  "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Dólar vs Real brasileño."},
    "USDCOP=X": {"name":"Dólar / Peso CO", "tipo":"Forex", "sector":"Forex LATAM", "riesgo":"Medio",  "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Clave para colombianos. ¿Cuándo comprar dólares?"},
    "USDMXN=X": {"name":"Dólar / Peso MX", "tipo":"Forex", "sector":"Forex LATAM", "riesgo":"Medio",  "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Dólar vs Peso mexicano."},
    "USDCHF=X": {"name":"Dólar / Franco CH","tipo":"Forex","sector":"Forex Major", "riesgo":"Bajo",   "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Franco suizo. Activo refugio seguro."},
    "AUDUSD=X": {"name":"AUD / Dólar",     "tipo":"Forex", "sector":"Forex Major", "riesgo":"Medio",  "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Dólar australiano. Ligado a materias primas."},
    # ── MATERIAS PRIMAS ───────────────────────────────────────────────────
    "GC=F":  {"name":"Oro (Gold)",          "tipo":"Commodity","sector":"Metales", "riesgo":"Bajo",   "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Reserva de valor histórica. Refugio en crisis."},
    "SI=F":  {"name":"Plata (Silver)",      "tipo":"Commodity","sector":"Metales", "riesgo":"Medio",  "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Plata. Más volátil que el oro."},
    "CL=F":  {"name":"Petróleo WTI",        "tipo":"Commodity","sector":"Energía", "riesgo":"Alto",   "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Precio del barril de petróleo."},
    "BZ=F":  {"name":"Petróleo Brent",      "tipo":"Commodity","sector":"Energía", "riesgo":"Alto",   "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Referencia europea del petróleo."},
    "NG=F":  {"name":"Gas Natural",         "tipo":"Commodity","sector":"Energía", "riesgo":"Alto",   "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Gas natural. Alta estacionalidad."},
    "HG=F":  {"name":"Cobre (Copper)",      "tipo":"Commodity","sector":"Metales", "riesgo":"Medio",  "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Cobre. Indicador de la economía global."},
    "ZW=F":  {"name":"Trigo (Wheat)",       "tipo":"Commodity","sector":"Agrícola","riesgo":"Alto",   "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Trigo. Afectado por clima y geopolítica."},
    "ZC=F":  {"name":"Maíz (Corn)",         "tipo":"Commodity","sector":"Agrícola","riesgo":"Alto",   "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Maíz. Base de biocombustibles."},
    "KC=F":  {"name":"Café (Coffee)",       "tipo":"Commodity","sector":"Agrícola","riesgo":"Alto",   "div":False, "broker":"XTB / IBKR",   "min_usd":1,  "desc":"Café arábica. Relevante para Colombia."},
    # ── ÍNDICES GLOBALES ──────────────────────────────────────────────────
    "^GSPC": {"name":"S&P 500 Index",       "tipo":"Índice","sector":"Índice USA",  "riesgo":"Bajo",  "div":False, "broker":"Solo referencia","min_usd":0,"desc":"Termómetro de la economía americana."},
    "^IXIC": {"name":"Nasdaq Composite",    "tipo":"Índice","sector":"Índice USA",  "riesgo":"Medio", "div":False, "broker":"Solo referencia","min_usd":0,"desc":"Índice tecnológico principal."},
    "^DJI":  {"name":"Dow Jones",           "tipo":"Índice","sector":"Índice USA",  "riesgo":"Bajo",  "div":False, "broker":"Solo referencia","min_usd":0,"desc":"Las 30 mayores empresas de EEUU."},
    "^VIX":  {"name":"VIX (Fear Index)",    "tipo":"Índice","sector":"Volatilidad", "riesgo":"Ref",   "div":False, "broker":"Solo referencia","min_usd":0,"desc":"Índice de miedo. >30 = pánico = oportunidad."},
    "^FTSE": {"name":"FTSE 100 (UK)",       "tipo":"Índice","sector":"Índice Global","riesgo":"Bajo", "div":False, "broker":"Solo referencia","min_usd":0,"desc":"Las 100 mayores empresas del Reino Unido."},
    "^GDAXI":{"name":"DAX (Alemania)",      "tipo":"Índice","sector":"Índice Global","riesgo":"Bajo", "div":False, "broker":"Solo referencia","min_usd":0,"desc":"Las 40 mayores empresas alemanas."},
}

# ─── BROKERS INFO ─────────────────────────────────────────────────────────────
BROKERS_DETAIL = {
    "XTB": {
        "color":"#00ff9d","rating":9.2,"min":"$0","fee":"$0","colombia":True,"fraccion":True,
        "activos":["Acciones","ETFs","Forex","Materias primas"],
        "url":"xtb.com","ideal":"⭐ MEJOR PARA EMPEZAR EN COLOMBIA",
        "tip":"Sin mínimo. Abre cuenta con tu cédula en 10 minutos."
    },
    "IBKR": {
        "color":"#0ea5e9","rating":9.5,"min":"$0","fee":"$0","colombia":True,"fraccion":True,
        "activos":["Acciones","ETFs","Forex","Opciones","Futuros","Bonos"],
        "url":"interactivebrokers.com","ideal":"🏆 MEJOR PLATAFORMA GLOBAL",
        "tip":"La más completa. Ideal cuando ya tienes experiencia."
    },
    "Binance": {
        "color":"#ffd60a","rating":9.0,"min":"$1","fee":"0.1%","colombia":True,"fraccion":True,
        "activos":["Criptomonedas","Futuros crypto"],
        "url":"binance.com","ideal":"₿ MEJOR PARA CRIPTOMONEDAS",
        "tip":"La exchange más grande del mundo. App muy completa."
    },
    "Coinbase": {
        "color":"#a78bfa","rating":8.5,"min":"$2","fee":"0.5-1.5%","colombia":True,"fraccion":True,
        "activos":["Criptomonedas"],
        "url":"coinbase.com","ideal":"🔒 CRIPTO MÁS SEGURA",
        "tip":"La más regulada. Ideal para principiantes en cripto."
    },
    "Schwab": {
        "color":"#ffd60a","rating":9.0,"min":"$0","fee":"$0","colombia":True,"fraccion":True,
        "activos":["Acciones","ETFs","Fondos indexados","Bonos"],
        "url":"schwab.com","ideal":"📈 MEJOR PARA LARGO PLAZO",
        "tip":"La más antigua y confiable. Perfecta para ETFs."
    },
    "Saxo": {
        "color":"#f97316","rating":8.5,"min":"$2000","fee":"Variable","colombia":True,"fraccion":False,
        "activos":["Acciones globales","ETFs","Forex","Materias primas","Opciones"],
        "url":"home.saxo","ideal":"🌍 MEJOR PARA MERCADOS GLOBALES",
        "tip":"Mínimo más alto pero acceso a todos los mercados del mundo."
    },
}

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
    except: return pd.DataFrame()

@st.cache_data(ttl=120)
def fetch_quick_price(symbol):
    try:
        df = yf.Ticker(symbol).history(period="2d", interval="1h")
        if df.empty: return None, None
        c = df["Close"].iloc[-1]; p = df["Close"].iloc[-2] if len(df)>1 else c
        return round(float(c),4), round((c-p)/p*100,2)
    except: return None, None

def add_indicators(df):
    if df.empty or len(df)<5: return df
    df = df.copy()
    for w in [7,20,50,200]:
        if len(df)>=w: df[f"ma{w}"] = df["close"].rolling(w).mean()
    delta=df["close"].diff(); gain=delta.clip(lower=0).rolling(14).mean(); loss=(-delta.clip(upper=0)).rolling(14).mean()
    df["rsi"]=100-(100/(1+(gain/loss.replace(0,np.nan))))
    df["bb_mid"]=df["close"].rolling(20).mean(); std=df["close"].rolling(20).std()
    df["bb_upper"]=df["bb_mid"]+2*std; df["bb_lower"]=df["bb_mid"]-2*std
    ema12=df["close"].ewm(span=12).mean(); ema26=df["close"].ewm(span=26).mean()
    df["macd"]=ema12-ema26; df["macd_signal"]=df["macd"].ewm(span=9).mean()
    df["macd_hist"]=df["macd"]-df["macd_signal"]
    hl=df["high"]-df["low"]; hpc=abs(df["high"]-df["close"].shift()); lpc=abs(df["low"]-df["close"].shift())
    df["atr"]=pd.concat([hl,hpc,lpc],axis=1).max(axis=1).rolling(14).mean()
    return df

def generate_signal(df):
    if df.empty or len(df)<20:
        return {"signal":"NEUTRAL","strength":50,"reasons":["Datos insuficientes"],"color":"#ffd60a"}
    last=df.iloc[-1]; score=50; reasons=[]
    if pd.notna(last.get("ma7")) and pd.notna(last.get("ma20")):
        if last["ma7"]>last["ma20"]: score+=12; reasons.append("✅ MA7 > MA20 cruce alcista")
        else: score-=12; reasons.append("❌ MA7 < MA20 cruce bajista")
    if pd.notna(last.get("ma50")):
        if last["close"]>last["ma50"]: score+=8; reasons.append("✅ Precio sobre MA50")
        else: score-=8; reasons.append("❌ Precio bajo MA50")
    rsi=last.get("rsi",50)
    if pd.notna(rsi):
        if rsi<30: score+=18; reasons.append(f"✅ RSI {rsi:.0f} — sobrevendido COMPRA")
        elif rsi>70: score-=18; reasons.append(f"❌ RSI {rsi:.0f} — sobrecomprado VENTA")
        else: reasons.append(f"➖ RSI {rsi:.0f} — neutral")
    if pd.notna(last.get("bb_lower")) and pd.notna(last.get("bb_upper")):
        if last["close"]<last["bb_lower"]: score+=10; reasons.append("✅ Bajo banda Bollinger inferior")
        elif last["close"]>last["bb_upper"]: score-=10; reasons.append("❌ Sobre banda Bollinger superior")
    if pd.notna(last.get("macd")) and pd.notna(last.get("macd_signal")):
        if last["macd"]>last["macd_signal"]: score+=8; reasons.append("✅ MACD momentum alcista")
        else: score-=8; reasons.append("❌ MACD momentum bajista")
    score=max(0,min(100,score))
    if score>=65: sig,col="COMPRAR","#00ff9d"
    elif score<=35: sig,col="VENDER","#ff4d6d"
    else: sig,col="NEUTRAL","#ffd60a"
    return {"signal":sig,"strength":score,"reasons":reasons,"color":col}

def kelly_criterion(win_rate=0.55, avg_win=1.5, avg_loss=1.0):
    b=avg_win/avg_loss; k=win_rate-(1-win_rate)/b
    return max(0.0,min(0.25,k))

# ─── EMAIL ────────────────────────────────────────────────────────────────────
def send_email(to, from_addr, pwd, subject, html):
    try:
        msg=MIMEMultipart("alternative"); msg["Subject"]=subject; msg["From"]=from_addr; msg["To"]=to
        msg.attach(MIMEText(html,"html"))
        with smtplib.SMTP_SSL("smtp.gmail.com",465) as s:
            s.login(from_addr,pwd); s.sendmail(from_addr,to,msg.as_string())
        return True,"✅ Correo enviado"
    except smtplib.SMTPAuthenticationError: return False,"❌ Error autenticación Gmail"
    except Exception as e: return False,f"❌ Error: {e}"

def build_alert_email(alerts_buy, alerts_sell, alerts_tp, alerts_sl, portfolio_val):
    now=datetime.now().strftime("%d/%m/%Y %H:%M")
    total=len(alerts_buy)+len(alerts_sell)+len(alerts_tp)+len(alerts_sl)

    def section(title, color, items):
        if not items: return ""
        rows=""
        for a in items:
            broker_html=f"<span style='background:{color}20;color:{color};padding:1px 6px;border-radius:3px;font-size:10px;font-family:monospace;'>🏦 {a.get('broker','')}</span>"
            action_html=f"<span style='background:{color}20;color:{color};padding:2px 8px;border-radius:3px;font-size:11px;font-weight:700;'>{a.get('accion_recomendada','')}</span>"
            rows+=f"""
            <tr style='border-bottom:1px solid #1f2937;'>
              <td style='padding:10px 8px;'>
                <div style='color:#fff;font-family:monospace;font-weight:700;font-size:13px;'>{a['symbol']}</div>
                <div style='color:#4b5563;font-size:10px;'>{a['name']}</div>
              </td>
              <td style='padding:10px 8px;color:{color};font-family:monospace;font-weight:700;'>${a['price']:,.4f}</td>
              <td style='padding:10px 8px;'>{action_html}</td>
              <td style='padding:10px 8px;'>{broker_html}</td>
              <td style='padding:10px 8px;'>
                <div style='color:#6b7280;font-size:10px;line-height:1.6;'>{a['razon']}</div>
                {f"<div style='color:{color};font-size:10px;margin-top:3px;'>TP: ${a['tp']:,.2f} · SL: ${a['sl']:,.2f} · Invertir: ${a['invertir']:,.0f}</div>" if a.get('tp') else ""}
              </td>
            </tr>"""
        return f"""
        <div style='background:#0d1117;border:1px solid #1f2937;border-top:3px solid {color};border-radius:8px;padding:16px;margin-bottom:14px;'>
          <div style='color:{color};font-weight:700;font-size:13px;margin-bottom:12px;'>{title} ({len(items)})</div>
          <table width='100%' cellpadding='0' cellspacing='0' style='border-collapse:collapse;'>
            <tr style='border-bottom:1px solid #374151;'>
              <th style='color:#4b5563;font-size:9px;padding:6px 8px;text-align:left;'>ACTIVO</th>
              <th style='color:#4b5563;font-size:9px;padding:6px 8px;text-align:left;'>PRECIO</th>
              <th style='color:#4b5563;font-size:9px;padding:6px 8px;text-align:left;'>ACCIÓN</th>
              <th style='color:#4b5563;font-size:9px;padding:6px 8px;text-align:left;'>BROKER</th>
              <th style='color:#4b5563;font-size:9px;padding:6px 8px;text-align:left;'>RAZÓN + NIVELES</th>
            </tr>
            {rows}
          </table>
        </div>"""

    urgente=""
    if alerts_tp or alerts_sl:
        urgente=f"""
        <div style='background:#ff4d6d15;border:2px solid #ff4d6d;border-radius:8px;padding:14px;margin-bottom:14px;'>
          <div style='color:#ff4d6d;font-weight:700;font-size:14px;margin-bottom:4px;'>⚡ ACCIÓN URGENTE — TUS POSICIONES</div>
          <div style='color:#9ca3af;font-size:11px;'>Las siguientes posiciones requieren tu atención inmediata:</div>
          {section("🎯 TAKE PROFIT ALCANZADO — Considera vender","#00ff9d",alerts_tp)}
          {section("🛑 STOP LOSS ALCANZADO — Sal ahora","#ff4d6d",alerts_sl)}
        </div>"""

    return f"""
    <div style='background:#060a0f;font-family:Arial,sans-serif;padding:28px;max-width:700px;margin:0 auto;border-radius:12px;border:1px solid #1f2937;'>
      <div style='text-align:center;margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid #1f2937;'>
        <div style='font-size:30px;'>📊</div>
        <div style='color:#00ff9d;font-size:18px;font-weight:700;letter-spacing:2px;margin-top:6px;'>QUANTUM TRADE</div>
        <div style='color:#4b5563;font-size:9px;letter-spacing:3px;'>ALERTA AUTOMÁTICA DE MERCADO</div>
        <div style='color:#374151;font-size:11px;margin-top:6px;'>{now} · {total} señal(es) detectada(s)</div>
      </div>
      {urgente}
      {section("🟢 OPORTUNIDADES DE COMPRA — Entra ahora","#00ff9d",alerts_buy)}
      {section("🔴 SEÑALES DE VENTA / SALIDA","#ff4d6d",alerts_sell)}
      <div style='background:#0d1117;border:1px solid #1f2937;border-radius:6px;padding:12px;margin-top:8px;font-size:10px;color:#4b5563;line-height:1.8;'>
        💡 Los precios de TP y SL son sugerencias basadas en ATR(14). Ajústalos según tu tolerancia al riesgo.<br>
        ⚠️ Las alertas son generadas por análisis técnico automático y <strong style='color:#6b7280;'>no constituyen asesoría financiera certificada</strong>.
      </div>
    </div>"""

# ─── ESCÁNER COMPLETO ─────────────────────────────────────────────────────────
SCAN_INTERVAL = 300  # 5 minutos

def get_broker_for_asset(asset_info, action):
    """Retorna broker específico según tipo de activo y acción."""
    tipo  = asset_info.get("tipo","Acción")
    broker_raw = asset_info.get("broker","XTB / IBKR")
    primary = broker_raw.split("/")[0].strip()

    if tipo == "Cripto":
        return "Binance" if action == "COMPRAR" else "Binance (vender spot)"
    elif tipo == "Forex":
        return "XTB (Forex sin comisión)"
    elif tipo == "Commodity":
        return "XTB (CFD materias primas)"
    elif tipo == "ETF":
        return "XTB / Schwab (ETF sin comisión)"
    elif tipo == "Índice":
        return "Solo referencia — no invertible directo"
    else:
        return f"{primary} (acciones fraccionadas desde $1)"

def run_scanner(cfg, trades):
    """Escanea todos los activos y genera alertas con broker y niveles específicos."""
    results_buy, results_sell, results_tp, results_sl = [], [], [], []
    prev = st.session_state.get("scanned_signals", {})
    kelly = kelly_criterion()
    portfolio_val = st.session_state.get("portfolio_val", 100)

    # ── 1. Escanear todos los activos (excepto índices de referencia) ─────────
    scannable = {k:v for k,v in ALL_ASSETS.items() if v["tipo"] != "Índice"}
    for sym, info in scannable.items():
        try:
            df = fetch_data(sym, "3mo", "1d")
            if df.empty or len(df) < 20: continue
            df  = add_indicators(df)
            sig = generate_signal(df)
            cp  = float(df["close"].iloc[-1])
            atr = float(df["atr"].iloc[-1]) if "atr" in df.columns and pd.notna(df["atr"].iloc[-1]) else cp*0.02
            tp  = round(cp + atr*2.5, 4)
            sl  = round(cp - atr*1.5, 4)
            inv = round(portfolio_val * kelly, 2)
            broker = get_broker_for_asset(info, sig["signal"])
            prev_sig = prev.get(sym, "NEUTRAL")
            razon = " · ".join([r.replace("✅ ","").replace("❌ ","").replace("➖ ","") for r in sig["reasons"][:3]])

            entry = {
                "symbol":sym,"name":info["name"],"price":cp,"strength":sig["strength"],
                "razon":razon,"broker":broker,"tipo":info["tipo"],
                "tp":tp,"sl":sl,"invertir":inv,
                "color":"#00ff9d","time":datetime.now().strftime("%H:%M"),
                "accion_recomendada": f"COMPRAR en {broker.split('(')[0].strip()}" if sig["signal"]=="COMPRAR" else f"VENDER en {broker.split('(')[0].strip()}"
            }

            if sig["signal"] == "COMPRAR" and sig["strength"] >= 65 and prev_sig != "COMPRAR":
                entry["color"] = "#00ff9d"
                entry["type"]  = "COMPRAR"
                results_buy.append(entry)
            elif sig["signal"] == "VENDER" and sig["strength"] <= 35 and prev_sig != "VENDER":
                entry["color"] = "#ff4d6d"
                entry["type"]  = "VENDER"
                results_sell.append(entry)

            st.session_state.scanned_signals[sym] = sig["signal"]
        except: continue

    # ── 2. Posiciones abiertas ─────────────────────────────────────────────────
    for t in trades:
        if t["status"] != "ABIERTA": continue
        try:
            cp, _ = fetch_quick_price(t["symbol"])
            if cp is None: continue
            upct = (cp - t["buy_price"]) / t["buy_price"] * 100
            pnl  = (cp - t["buy_price"]) * t["shares"]
            info = ALL_ASSETS.get(t["symbol"], {})
            broker = get_broker_for_asset(info, "VENDER")
            if cp >= t["tp_price"] and not t.get("alert_sell_sent"):
                results_tp.append({"symbol":t["symbol"],"name":info.get("name",t["symbol"]),"price":cp,
                    "strength":round(upct,1),"razon":f"TP alcanzado · Ganancia +${pnl:,.2f}",
                    "broker":broker,"tp":None,"sl":None,"invertir":0,
                    "accion_recomendada":"VENDER — tomar ganancias","color":"#00ff9d","time":datetime.now().strftime("%H:%M"),"type":"TP"})
                t["alert_sell_sent"]=True
            elif cp <= t["sl_price"] and not t.get("alert_sell_sent"):
                results_sl.append({"symbol":t["symbol"],"name":info.get("name",t["symbol"]),"price":cp,
                    "strength":round(upct,1),"razon":f"SL alcanzado · Pérdida ${pnl:,.2f}",
                    "broker":broker,"tp":None,"sl":None,"invertir":0,
                    "accion_recomendada":"VENDER — limitar pérdidas","color":"#ff4d6d","time":datetime.now().strftime("%H:%M"),"type":"SL"})
                t["alert_sell_sent"]=True
        except: continue

    # ── 3. Guardar en historial ────────────────────────────────────────────────
    all_new = results_buy + results_sell + results_tp + results_sl
    if all_new:
        st.session_state.scanner_results = all_new + st.session_state.get("scanner_results",[])
        st.session_state.scanner_results = st.session_state.scanner_results[:100]

    # ── 4. Enviar correo si hay señales ───────────────────────────────────────
    total_new = len(all_new)
    if total_new > 0 and cfg.get("active") and cfg.get("to") and cfg.get("from") and cfg.get("pass"):
        html = build_alert_email(results_buy, results_sell, results_tp, results_sl, portfolio_val)
        subj = f"📊 Quantum Trade — {total_new} señal(es) · {datetime.now().strftime('%H:%M')} · {len(results_buy)} compra / {len(results_sell)} venta"
        ok, msg = send_email(cfg["to"], cfg["from"], cfg["pass"], subj, html)
        log_msg = f"📧 {total_new} señales enviadas ({len(results_buy)}🟢 {len(results_sell)}🔴 {len(results_tp)}🎯 {len(results_sl)}🛑)"
        st.session_state.alert_log = [{"time":datetime.now().strftime("%H:%M"),"msg":log_msg,"color":"#00ff9d" if ok else "#ff4d6d"}] + st.session_state.get("alert_log",[])

    st.session_state.last_scan_time = time.time()
    return all_new

# ─── SESSION STATE ─────────────────────────────────────────────────────────────
for key, val in [("trades",[]),("alert_log",[]),("scanner_results",[]),
                 ("scanned_signals",{}),("last_scan_time",0),
                 ("email_config",{"to":"","from":"","pass":"","active":False})]:
    if key not in st.session_state: st.session_state[key]=val

def add_trade(sym, buy_price, shares, buy_date, tp_pct, sl_pct, notes):
    st.session_state.trades.append({
        "id":len(st.session_state.trades),"symbol":sym,"buy_price":buy_price,
        "shares":shares,"invested":round(buy_price*shares,2),"buy_date":str(buy_date),
        "tp_price":round(buy_price*(1+tp_pct/100),2),"sl_price":round(buy_price*(1-sl_pct/100),2),
        "tp_pct":tp_pct,"sl_pct":sl_pct,"notes":notes,"status":"ABIERTA",
        "sell_price":None,"sell_date":None,"alert_sell_sent":False,
    })

def close_trade(idx, sell_price, sell_date):
    t=st.session_state.trades[idx]; t["sell_price"]=sell_price; t["sell_date"]=str(sell_date)
    pnl=(sell_price-t["buy_price"])*t["shares"]
    t["status"]="GANANCIA ✅" if pnl>=0 else "PÉRDIDA ❌"
    t["pnl"]=round(pnl,2); t["pnl_pct"]=round((sell_price-t["buy_price"])/t["buy_price"]*100,2)

# ─── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:12px 0 8px;'>
      <div style='font-size:32px;'>📈</div>
      <div style='color:#fff;font-family:Space Mono;font-weight:700;font-size:15px;letter-spacing:2px;'>QUANTUM TRADE</div>
      <div style='color:#4b5563;font-size:9px;letter-spacing:3px;'>120+ ACTIVOS · AI ANALYTICS</div>
    </div><hr style='border-color:#1f2937;margin:8px 0 12px;'>
    """, unsafe_allow_html=True)

    tipo_filter   = st.selectbox("📦 Tipo de activo", ["Todos","Acción","ETF","Cripto","Forex","Commodity","Índice"])
    sector_filter = st.selectbox("🏭 Sector", ["Todos","Tecnología","Finanzas","Salud","Consumo","Energía","ETF Broad","ETF Dividend","ETF Commodity","Cripto L1","Cripto Pagos","Forex Major","Forex LATAM","Metales","Agrícola","Automotriz","Logística"])
    riesgo_filter = st.selectbox("⚡ Riesgo", ["Todos","Bajo","Medio","Alto","Muy Alto"])

    filtered = {k:v for k,v in ALL_ASSETS.items()
                if (tipo_filter=="Todos"   or v["tipo"]==tipo_filter)
                and (sector_filter=="Todos" or v["sector"]==sector_filter)
                and (riesgo_filter=="Todos" or v["riesgo"]==riesgo_filter)}
    if not filtered: filtered=ALL_ASSETS

    symbol = st.selectbox("🎯 Activo", list(filtered.keys()),
        format_func=lambda x: f"{x} — {ALL_ASSETS[x]['name']}")

    info = ALL_ASSETS[symbol]
    tipo_color = {"Acción":"#0ea5e9","ETF":"#00ff9d","Cripto":"#ffd60a","Forex":"#a78bfa","Commodity":"#f97316","Índice":"#6b7280"}.get(info["tipo"],"#6b7280")
    riesgo_color = {"Bajo":"#00ff9d","Medio":"#ffd60a","Alto":"#f97316","Muy Alto":"#ff4d6d"}.get(info["riesgo"],"#6b7280")
    st.markdown(f"""
    <div style='background:#0d1117;border:1px solid #1f2937;border-radius:6px;padding:10px;margin:4px 0 12px;'>
      <div style='display:flex;gap:6px;margin-bottom:6px;flex-wrap:wrap;'>
        <span style='background:{tipo_color}20;color:{tipo_color};padding:2px 7px;border-radius:3px;font-size:10px;'>{info["tipo"]}</span>
        <span style='background:{riesgo_color}20;color:{riesgo_color};padding:2px 7px;border-radius:3px;font-size:10px;'>Riesgo {info["riesgo"]}</span>
        {"<span style='background:#00ff9d20;color:#00ff9d;padding:2px 7px;border-radius:3px;font-size:10px;'>💵 Div</span>" if info.get("div") else ""}
      </div>
      <div style='color:#6b7280;font-size:10px;line-height:1.5;'>{info["desc"]}</div>
      <div style='color:#4b5563;font-size:10px;margin-top:4px;'>🏦 {info["broker"]}</div>
    </div>
    """, unsafe_allow_html=True)

    portfolio = st.number_input("💰 Capital disponible (USD)", min_value=1, max_value=10_000_000, value=100, step=10)
    st.session_state["portfolio_val"] = portfolio
    st.markdown("<div style='color:#4b5563;font-size:10px;margin-top:-8px;'>Desde $1 USD en acciones fraccionadas</div>", unsafe_allow_html=True)

    st.markdown("<div style='color:#4b5563;font-size:9px;letter-spacing:2px;margin-top:10px;'>KELLY CRITERION</div>", unsafe_allow_html=True)
    win_rate = st.slider("Win Rate %", 40, 70, 55) / 100
    avg_win  = st.slider("Ganancia promedio (x)", 1.0, 3.0, 1.5, 0.1)
    avg_loss = st.slider("Pérdida promedio (x)", 0.5, 2.0, 1.0, 0.1)
    auto_ref = st.checkbox("🔄 Auto-refresh (30s)", value=True)
    if st.button("↻ Actualizar"):
        st.cache_data.clear(); st.rerun()

    # Mini contador escáner
    secs_left = max(0, SCAN_INTERVAL - (time.time()-st.session_state.last_scan_time))
    pct = int((1-secs_left/SCAN_INTERVAL)*100)
    st.markdown(f"""
    <div style='margin-top:12px;background:#0d1117;border:1px solid #1f2937;border-radius:6px;padding:8px 10px;'>
      <div style='display:flex;justify-content:space-between;font-size:10px;color:#4b5563;margin-bottom:4px;'>
        <span>🔍 Escáner ({len(ALL_ASSETS)} activos)</span>
        <span style='color:#00ff9d;font-family:Space Mono;'>{int(secs_left//60):02d}:{int(secs_left%60):02d}</span>
      </div>
      <div style='background:#1f2937;border-radius:3px;height:4px;'>
        <div style='background:#00ff9d;border-radius:3px;height:4px;width:{pct}%;'></div>
      </div>
    </div>
    <div style='color:#4b5563;font-size:9px;margin-top:8px;'>Yahoo Finance · Datos cada 60s<br>Indicadores: MA·RSI·MACD·Bollinger·ATR·Kelly</div>
    """, unsafe_allow_html=True)

# ─── CARGAR DATOS ──────────────────────────────────────────────────────────────
with st.spinner(f"Cargando {symbol}..."):
    df_1d = fetch_data(symbol, "1y", "1d")
    df_1h = fetch_data(symbol, "5d", "1h")
if df_1d.empty: st.error("No se pudo cargar el dato. Verifica conexión."); st.stop()

df_1d = add_indicators(df_1d)
df_1h = add_indicators(df_1h) if not df_1h.empty else df_1d
sig   = generate_signal(df_1d)
kelly_pct  = kelly_criterion(win_rate, avg_win, avg_loss)
invest_amt = portfolio * kelly_pct
last=df_1d.iloc[-1]; prev=df_1d.iloc[-2]
price_now=float(last["close"]); price_chg=((price_now-float(prev["close"]))/float(prev["close"]))*100
atr_val=float(last.get("atr", price_now*0.02)) if pd.notna(last.get("atr")) else price_now*0.02
proj_tp=round(price_now+atr_val*2.5,4); proj_sl=round(price_now-atr_val*1.5,4)

# ─── ESCÁNER AUTOMÁTICO ────────────────────────────────────────────────────────
cfg = st.session_state.email_config
if (time.time()-st.session_state.last_scan_time) >= SCAN_INTERVAL and cfg.get("active") and cfg.get("to") and cfg.get("from") and cfg.get("pass"):
    with st.spinner("🔍 Escaneando 120+ activos..."):
        run_scanner(cfg, st.session_state.trades)

# ─── HEADER ────────────────────────────────────────────────────────────────────
sc=sig["color"]; sl=sig["signal"]
sig_emoji   = "🟢" if sl=="COMPRAR" else ("🔴" if sl=="VENDER" else "🟡")
price_arrow = "▲" if price_chg>=0 else "▼"
price_color = "#00ff9d" if price_chg>=0 else "#ff4d6d"
broker_recom = get_broker_for_asset(info, sl) if 'get_broker_for_asset' in dir() else info["broker"]

st.markdown(f"""
<div style='background:#0d1117;border:1px solid #1f2937;border-radius:10px;padding:18px 22px;margin-bottom:12px;'>
  <div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;'>
    <div>
      <div style='display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:4px;'>
        <span style='color:#fff;font-family:Space Mono;font-weight:700;font-size:22px;'>{symbol}</span>
        <span style='color:#6b7280;font-size:13px;'>{info["name"]}</span>
        <span style='background:{tipo_color}20;color:{tipo_color};padding:2px 7px;border-radius:3px;font-size:10px;'>{info["tipo"]}</span>
        <span style='background:{riesgo_color}20;color:{riesgo_color};padding:2px 7px;border-radius:3px;font-size:10px;'>Riesgo {info["riesgo"]}</span>
        {"<span style='background:#00ff9d20;color:#00ff9d;padding:2px 7px;border-radius:3px;font-size:10px;'>💵 Dividendo</span>" if info.get("div") else ""}
      </div>
      <div style='display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;'>
        <span style='color:#fff;font-family:Space Mono;font-size:32px;font-weight:700;'>${price_now:,.4f}</span>
        <span style='color:{price_color};font-family:Space Mono;font-size:15px;'>{price_arrow} {abs(price_chg):.2f}%</span>
      </div>
      <div style='color:#4b5563;font-size:11px;margin-top:4px;'>🏦 Broker recomendado: <span style='color:#9ca3af;'>{broker_recom}</span></div>
    </div>
    <div style='text-align:right;'>
      <div style='background:{sc}20;border:2px solid {sc};color:{sc};padding:10px 22px;border-radius:8px;
                  font-family:Space Mono;font-size:18px;font-weight:700;letter-spacing:2px;'>
        {sig_emoji} {sl}
      </div>
      <div style='color:#6b7280;font-size:11px;margin-top:5px;'>Fuerza: {sig["strength"]}%</div>
      <div style='color:#4b5563;font-size:10px;margin-top:2px;'>TP: <span style='color:#00ff9d;'>${proj_tp:,.4f}</span> · SL: <span style='color:#ff4d6d;'>${proj_sl:,.4f}</span></div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── MÉTRICAS ──────────────────────────────────────────────────────────────────
rsi_v = float(last.get("rsi",50)) if pd.notna(last.get("rsi")) else 50.0
c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("RSI(14)", f"{rsi_v:.1f}", "Sobrevendido" if rsi_v<30 else ("Sobrecomprado" if rsi_v>70 else "Neutral"))
c2.metric("MA 20", f"${float(last.get('ma20',0)):,.4f}" if pd.notna(last.get("ma20")) else "N/A")
c3.metric("MA 50", f"${float(last.get('ma50',0)):,.4f}" if pd.notna(last.get("ma50")) else "N/A")
c4.metric("ATR(14)", f"${atr_val:,.4f}")
c5.metric("Kelly %", f"{kelly_pct*100:.1f}%")
c6.metric("💰 Invertir", f"${invest_amt:,.2f}", f"de ${portfolio:,.0f}")
st.markdown("<br>", unsafe_allow_html=True)

# ─── TABS ──────────────────────────────────────────────────────────────────────
t1,t2,t3,t4,t5,t6,t7 = st.tabs([
    "📊 Gráfica","📅 Multi-Período","⚡ RSI & Bollinger",
    "🧮 Señal & Conclusiones","💼 Mis Inversiones","🔔 Alertas & Escáner","🏦 Brokers"
])

# ── TAB 1 ──────────────────────────────────────────────────────────────────────
with t1:
    df_show = df_1h if not df_1h.empty else df_1d
    fig=make_subplots(rows=3,cols=1,shared_xaxes=True,row_heights=[0.6,0.2,0.2],vertical_spacing=0.02)
    fig.add_trace(go.Candlestick(x=df_show.index,open=df_show["open"],high=df_show["high"],low=df_show["low"],close=df_show["close"],
        name="Precio",increasing_fillcolor="#00ff9d",decreasing_fillcolor="#ff4d6d",
        increasing_line_color="#00ff9d",decreasing_line_color="#ff4d6d"),row=1,col=1)
    for ma,color in [("ma7","#ffd60a"),("ma20","#0ea5e9"),("ma50","#a78bfa")]:
        if ma in df_show.columns and df_show[ma].notna().any():
            fig.add_trace(go.Scatter(x=df_show.index,y=df_show[ma],name=ma.upper(),line=dict(color=color,width=1.2,dash="dot"),opacity=0.8),row=1,col=1)
    if "bb_upper" in df_show.columns:
        fig.add_trace(go.Scatter(x=df_show.index,y=df_show["bb_upper"],name="BB+",line=dict(color="#0ea5e9",width=1,dash="dash"),opacity=0.5),row=1,col=1)
        fig.add_trace(go.Scatter(x=df_show.index,y=df_show["bb_lower"],name="BB-",line=dict(color="#a78bfa",width=1,dash="dash"),fill="tonexty",fillcolor="rgba(14,165,233,0.05)",opacity=0.5),row=1,col=1)
    cv=["#00ff9d" if c>=o else "#ff4d6d" for c,o in zip(df_show["close"],df_show["open"])]
    fig.add_trace(go.Bar(x=df_show.index,y=df_show["volume"],name="Vol",marker_color=cv,opacity=0.6),row=2,col=1)
    if "macd" in df_show.columns:
        fig.add_trace(go.Scatter(x=df_show.index,y=df_show["macd"],name="MACD",line=dict(color="#0ea5e9",width=1.5)),row=3,col=1)
        fig.add_trace(go.Scatter(x=df_show.index,y=df_show["macd_signal"],name="Signal",line=dict(color="#ffd60a",width=1.5)),row=3,col=1)
        ch=["#00ff9d" if v>=0 else "#ff4d6d" for v in df_show["macd_hist"].fillna(0)]
        fig.add_trace(go.Bar(x=df_show.index,y=df_show["macd_hist"],marker_color=ch,opacity=0.7),row=3,col=1)
    fig.update_layout(template="plotly_dark",plot_bgcolor="#0d1117",paper_bgcolor="#0d1117",
        font=dict(family="Space Mono",color="#9ca3af",size=10),height=540,margin=dict(l=0,r=0,t=30,b=0),
        legend=dict(bgcolor="#0d1117",bordercolor="#1f2937",borderwidth=1,orientation="h",y=1.02),
        xaxis_rangeslider_visible=False)
    for i in [1,2,3]: fig.update_xaxes(gridcolor="#1f2937",row=i,col=1); fig.update_yaxes(gridcolor="#1f2937",row=i,col=1)
    st.plotly_chart(fig,use_container_width=True)

# ── TAB 2 ──────────────────────────────────────────────────────────────────────
with t2:
    configs=[("5d","1h","5 Días"),("1mo","1d","1 Mes"),("6mo","1wk","6 Meses"),("5y","1mo","5 Años")]
    fig2=make_subplots(rows=2,cols=2,subplot_titles=[c[2] for c in configs],vertical_spacing=0.12,horizontal_spacing=0.05)
    pos=[(1,1),(1,2),(2,1),(2,2)]; pal=["#00ff9d","#0ea5e9","#ffd60a","#a78bfa"]
    for idx,(period,interval,label) in enumerate(configs):
        r,c=pos[idx]; df_t=fetch_data(symbol,period,interval)
        if df_t.empty: continue
        df_t=add_indicators(df_t); col2=pal[idx]
        rgb=tuple(int(col2[i:i+2],16) for i in (1,3,5))
        fig2.add_trace(go.Scatter(x=df_t.index,y=df_t["close"],name=label,line=dict(color=col2,width=1.8),
            fill="tozeroy",fillcolor=f"rgba({rgb[0]},{rgb[1]},{rgb[2]},0.08)"),row=r,col=c)
        if "ma20" in df_t.columns and df_t["ma20"].notna().any():
            fig2.add_trace(go.Scatter(x=df_t.index,y=df_t["ma20"],line=dict(color="#ffd60a",width=1,dash="dot"),showlegend=False),row=r,col=c)
        fig2.update_xaxes(gridcolor="#1f2937",row=r,col=c); fig2.update_yaxes(gridcolor="#1f2937",row=r,col=c)
    fig2.update_layout(template="plotly_dark",plot_bgcolor="#0d1117",paper_bgcolor="#0d1117",
        font=dict(family="Space Mono",color="#9ca3af",size=10),height=500,margin=dict(l=0,r=0,t=40,b=0),showlegend=False)
    st.plotly_chart(fig2,use_container_width=True)

# ── TAB 3 ──────────────────────────────────────────────────────────────────────
with t3:
    fig3=make_subplots(rows=2,cols=1,shared_xaxes=True,row_heights=[0.5,0.5],subplot_titles=["RSI (14)","Bollinger Bands"])
    if "rsi" in df_1d.columns:
        fig3.add_trace(go.Scatter(x=df_1d.index,y=df_1d["rsi"],name="RSI",line=dict(color="#ffd60a",width=2)),row=1,col=1)
        fig3.add_hline(y=70,line_dash="dash",line_color="#ff4d6d",opacity=0.7,row=1,col=1)
        fig3.add_hline(y=30,line_dash="dash",line_color="#00ff9d",opacity=0.7,row=1,col=1)
        fig3.add_hrect(y0=0,y1=30,fillcolor="#00ff9d",opacity=0.05,row=1,col=1)
        fig3.add_hrect(y0=70,y1=100,fillcolor="#ff4d6d",opacity=0.05,row=1,col=1)
    if "bb_upper" in df_1d.columns:
        fig3.add_trace(go.Scatter(x=df_1d.index,y=df_1d["close"],name="Precio",line=dict(color="#fff",width=1.5)),row=2,col=1)
        fig3.add_trace(go.Scatter(x=df_1d.index,y=df_1d["bb_upper"],name="BB+",line=dict(color="#0ea5e9",width=1,dash="dot")),row=2,col=1)
        fig3.add_trace(go.Scatter(x=df_1d.index,y=df_1d["bb_mid"],name="BB mid",line=dict(color="#6b7280",width=1,dash="dot")),row=2,col=1)
        fig3.add_trace(go.Scatter(x=df_1d.index,y=df_1d["bb_lower"],name="BB-",line=dict(color="#a78bfa",width=1,dash="dot"),fill="tonexty",fillcolor="rgba(14,165,233,0.06)"),row=2,col=1)
    fig3.update_layout(template="plotly_dark",plot_bgcolor="#0d1117",paper_bgcolor="#0d1117",
        font=dict(family="Space Mono",color="#9ca3af",size=10),height=480,margin=dict(l=0,r=0,t=40,b=0),
        legend=dict(bgcolor="#0d1117",bordercolor="#1f2937",borderwidth=1,orientation="h",y=1.02))
    for i in [1,2]: fig3.update_xaxes(gridcolor="#1f2937",row=i,col=1); fig3.update_yaxes(gridcolor="#1f2937",row=i,col=1)
    st.plotly_chart(fig3,use_container_width=True)

# ── TAB 4: SEÑAL Y CONCLUSIONES ────────────────────────────────────────────────
with t4:
    cl,cr=st.columns(2)
    with cl:
        st.markdown("### 📋 Señales Detectadas")
        for r in sig["reasons"]:
            color="#00ff9d" if "✅" in r else ("#ff4d6d" if "❌" in r else "#9ca3af")
            st.markdown(f"<div style='color:{color};font-size:12px;padding:4px 0;font-family:Space Mono;'>{r}</div>",unsafe_allow_html=True)
        s=sig["strength"]
        st.markdown(f"""<div style='margin-top:14px;'>
        <div style='color:#4b5563;font-size:9px;letter-spacing:2px;margin-bottom:6px;'>FUERZA DE SEÑAL</div>
        <div style='background:#1f2937;border-radius:4px;height:8px;'>
          <div style='background:{sig["color"]};border-radius:4px;height:8px;width:{s}%;'></div>
        </div>
        <div style='color:{sig["color"]};font-family:Space Mono;font-size:22px;font-weight:700;margin-top:6px;'>{s}%</div>
        <div style='color:#4b5563;font-size:11px;margin-top:10px;'>🏦 Broker recomendado:</div>
        <div style='color:#fff;font-size:13px;font-weight:600;margin-top:3px;'>{broker_recom}</div>
        </div>""",unsafe_allow_html=True)
    with cr:
        st.markdown("### 🧮 Kelly Criterion")
        st.markdown(f"""<div style='background:#0d1117;border:1px solid #1f2937;border-radius:10px;padding:18px;'>
        <div style='color:#ffd60a;font-family:Space Mono;font-size:38px;font-weight:700;text-align:center;'>{kelly_pct*100:.1f}%</div>
        <div style='color:#4b5563;font-size:11px;text-align:center;'>del capital a invertir</div>
        <div style='text-align:center;margin-top:14px;padding-top:14px;border-top:1px solid #1f2937;'>
          <div style='color:#6b7280;font-size:11px;'>Monto en {symbol}</div>
          <div style='color:{sig["color"]};font-family:Space Mono;font-size:26px;font-weight:700;'>${invest_amt:,.2f}</div>
          <div style='color:#4b5563;font-size:10px;margin-top:6px;'>TP → <span style='color:#00ff9d;'>${proj_tp:,.4f}</span> · SL → <span style='color:#ff4d6d;'>${proj_sl:,.4f}</span></div>
        </div></div>""",unsafe_allow_html=True)

    # Conclusiones automáticas
    st.markdown("<br>### 🧠 Conclusiones — ¿Cuándo invertir y en qué broker?")
    p52h=df_1d["high"].max(); p52l=df_1d["low"].min()
    ma7_v=float(last.get("ma7",0)) if pd.notna(last.get("ma7")) else 0
    ma20_v=float(last.get("ma20",0)) if pd.notna(last.get("ma20")) else 0
    ma50_v=float(last.get("ma50",0)) if pd.notna(last.get("ma50")) else 0
    bb_low_v=float(last.get("bb_lower",price_now)) if pd.notna(last.get("bb_lower")) else price_now
    bb_up_v=float(last.get("bb_upper",price_now)) if pd.notna(last.get("bb_upper")) else price_now
    bb_mid_v=float(last.get("bb_mid",price_now)) if pd.notna(last.get("bb_mid")) else price_now
    macd_v=float(last.get("macd",0)) if pd.notna(last.get("macd")) else 0
    macd_s_v=float(last.get("macd_signal",0)) if pd.notna(last.get("macd_signal")) else 0

    conclusiones=[]
    if ma7_v>0 and ma20_v>0:
        diff=(ma7_v-ma20_v)/ma20_v*100
        if ma7_v>ma20_v:
            if abs(diff)<0.5: conclusiones.append(("🔀","Cruce MA FRESCO","COMPRA AHORA","#00ff9d",f"MA7 acaba de cruzar sobre MA20 (diferencia {abs(diff):.1f}%). Señal de entrada fresca. Usa {broker_recom}."))
            else: conclusiones.append(("📈","Tendencia alcista activa","POSITIVO","#00ff9d",f"MA7>${ma7_v:,.4f} sobre MA20=${ma20_v:,.4f}. Tendencia de corto plazo alcista confirmada."))
        else: conclusiones.append(("📉","Cruce bajista MA","ESPERAR","#ff4d6d",f"MA7 bajo MA20. Presión vendedora. Espera que MA7 cruce hacia arriba antes de comprar."))
    if rsi_v<30: conclusiones.append(("🟢",f"RSI {rsi_v:.0f} — SOBREVENTA","COMPRA FUERTE","#00ff9d",f"RSI en zona de sobreventa. Alta probabilidad de rebote. Excelente entrada. Broker: {broker_recom}."))
    elif rsi_v>70: conclusiones.append(("🔴",f"RSI {rsi_v:.0f} — SOBRECOMPRA","NO ENTRAR","#ff4d6d","El activo subió demasiado rápido. Espera corrección a zona RSI 40–55 antes de comprar."))
    else: conclusiones.append(("🟡",f"RSI {rsi_v:.0f} — Neutral","OBSERVAR","#ffd60a","RSI en zona central. La entrada depende de otros indicadores."))
    if price_now<=bb_low_v: conclusiones.append(("🎯","Tocando banda Bollinger INFERIOR","ENTRADA IDEAL","#00ff9d",f"Soporte estadístico fuerte en ${bb_low_v:,.4f}. 85% de probabilidad de rebote hacia ${bb_mid_v:,.4f}. Entra en {broker_recom}."))
    elif price_now>=bb_up_v: conclusiones.append(("🚨","Tocando banda Bollinger SUPERIOR","TOMAR GANANCIAS","#ff4d6d",f"Resistencia estadística en ${bb_up_v:,.4f}. Alta probabilidad de retroceso hacia ${bb_mid_v:,.4f}."))
    if macd_v>macd_s_v and macd_v>0: conclusiones.append(("⚡","MACD positivo y creciente","MOMENTUM ALCISTA","#00ff9d","Fuerza compradora acelerando. Confirma señal de compra."))
    elif macd_v<macd_s_v and macd_v<0: conclusiones.append(("💤","MACD negativo","MOMENTUM BAJISTA","#ff4d6d","Fuerza vendedora dominante. Espera cruce del MACD hacia arriba."))

    cols_c=st.columns(2)
    for i,item in enumerate(conclusiones):
        icon,title,label,color,desc=item
        with cols_c[i%2]:
            st.markdown(f"""
            <div style='background:#0d1117;border:1px solid #1f2937;border-left:3px solid {color};border-radius:6px;padding:12px;margin-bottom:10px;'>
              <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;'>
                <span style='color:#fff;font-size:12px;font-weight:600;'>{icon} {title}</span>
                <span style='background:{color}20;color:{color};padding:2px 7px;border-radius:3px;font-size:9px;font-family:Space Mono;font-weight:700;'>{label}</span>
              </div>
              <div style='color:#6b7280;font-size:11px;line-height:1.7;'>{desc}</div>
            </div>""",unsafe_allow_html=True)

    # Conclusión final
    s=sig["strength"]
    if s>=70: fc_title,fc_color,fc_desc="COMPRAR AHORA","#00ff9d",f"Múltiples señales alineadas. Entra con ${invest_amt:,.2f} en {broker_recom}. TP: ${proj_tp:,.4f} · SL: ${proj_sl:,.4f}"
    elif s>=55: fc_title,fc_color,fc_desc="CONDICIONES FAVORABLES","#ffd60a",f"Señales positivas pero no todas confirmadas. Considera 50% del monto Kelly (${invest_amt/2:,.2f}) en {broker_recom}."
    elif s>=40: fc_title,fc_color,fc_desc="ESPERAR MEJOR MOMENTO","#ffd60a","Señales divididas. No hay ventaja estadística clara. Paciencia."
    else: fc_title,fc_color,fc_desc="NO ENTRAR / PROTEGER POSICIÓN","#ff4d6d",f"Presión bajista dominante. Si tienes posición, protege con SL en ${proj_sl:,.4f}."
    st.markdown(f"""
    <div style='background:{fc_color}15;border:2px solid {fc_color};border-radius:8px;padding:16px;margin-top:6px;'>
      <div style='color:{fc_color};font-family:Space Mono;font-size:13px;font-weight:700;margin-bottom:6px;'>{"🚀" if s>=70 else "👍" if s>=55 else "⏸️" if s>=40 else "🛑"} CONCLUSIÓN: {fc_title}</div>
      <div style='color:#9ca3af;font-size:12px;line-height:1.7;'>{fc_desc}</div>
    </div>""",unsafe_allow_html=True)

# ── TAB 5: MIS INVERSIONES ─────────────────────────────────────────────────────
with t5:
    st.markdown("### 💼 Mis Inversiones")
    proj_tp_pct=round((proj_tp-price_now)/price_now*100,2)
    proj_sl_pct=round((price_now-proj_sl)/price_now*100,2)
    rr=round(proj_tp_pct/proj_sl_pct,2) if proj_sl_pct>0 else 0

    st.markdown(f"""
    <div style='background:#0d1117;border:1px solid #1f2937;border-radius:10px;padding:16px;margin-bottom:14px;'>
      <div style='color:#4b5563;font-size:9px;letter-spacing:2px;margin-bottom:12px;'>PROYECCIÓN MODELO — {symbol}</div>
      <div style='display:grid;grid-template-columns:repeat(5,1fr);gap:10px;font-family:Space Mono;text-align:center;'>
        <div style='background:#060a0f;border:1px solid #1f2937;border-radius:6px;padding:10px;'>
          <div style='color:#4b5563;font-size:9px;'>SEÑAL</div>
          <div style='color:{sig["color"]};font-size:16px;font-weight:700;'>{sig["signal"]}</div>
        </div>
        <div style='background:#060a0f;border:1px solid #00ff9d30;border-radius:6px;padding:10px;'>
          <div style='color:#4b5563;font-size:9px;'>TAKE PROFIT</div>
          <div style='color:#00ff9d;font-size:14px;font-weight:700;'>${proj_tp:,.4f}</div>
          <div style='color:#00ff9d;font-size:10px;'>+{proj_tp_pct}%</div>
        </div>
        <div style='background:#060a0f;border:1px solid #ff4d6d30;border-radius:6px;padding:10px;'>
          <div style='color:#4b5563;font-size:9px;'>STOP LOSS</div>
          <div style='color:#ff4d6d;font-size:14px;font-weight:700;'>${proj_sl:,.4f}</div>
          <div style='color:#ff4d6d;font-size:10px;'>-{proj_sl_pct}%</div>
        </div>
        <div style='background:#060a0f;border:1px solid #ffd60a30;border-radius:6px;padding:10px;'>
          <div style='color:#4b5563;font-size:9px;'>R/R RATIO</div>
          <div style='color:#ffd60a;font-size:16px;font-weight:700;'>{rr}:1</div>
          <div style='color:{"#00ff9d" if rr>=1.5 else "#ff4d6d"};font-size:10px;'>{"✅ OK" if rr>=1.5 else "❌ Bajo"}</div>
        </div>
        <div style='background:#060a0f;border:1px solid #0ea5e930;border-radius:6px;padding:10px;'>
          <div style='color:#4b5563;font-size:9px;'>BROKER</div>
          <div style='color:#0ea5e9;font-size:11px;font-weight:700;'>{broker_recom.split("(")[0]}</div>
        </div>
      </div>
    </div>""",unsafe_allow_html=True)

    with st.expander("➕ Registrar inversión",expanded=len(st.session_state.trades)==0):
        fc1,fc2,fc3=st.columns(3)
        with fc1:
            ts=st.selectbox("Activo",list(ALL_ASSETS.keys()),index=list(ALL_ASSETS.keys()).index(symbol),key="ts")
            tsh=st.number_input("Cantidad",min_value=0.0001,max_value=100000.0,value=1.0,step=0.0001,format="%.4f",key="tsh")
        with fc2:
            tbp=st.number_input("Precio compra (USD)",min_value=0.0001,value=float(round(price_now,4)),step=0.0001,format="%.4f",key="tbp")
            tbd=st.date_input("Fecha compra",value=pd.Timestamp.today(),key="tbd")
        with fc3:
            ttp=st.number_input("Take Profit %",min_value=0.5,max_value=500.0,value=float(proj_tp_pct),step=0.5,key="ttp")
            tsl=st.number_input("Stop Loss %",min_value=0.5,max_value=100.0,value=float(proj_sl_pct),step=0.5,key="tsl")
        tnotes=st.text_input("Notas",placeholder="Razón de entrada...",key="tnotes")
        tp_p=round(tbp*(1+ttp/100),4); sl_p=round(tbp*(1-tsl/100),4)
        inv_t=round(tbp*tsh,2); gan=round((tp_p-tbp)*tsh,2); per=round((tbp-sl_p)*tsh,2)
        st.markdown(f"""<div style='background:#060a0f;border:1px solid #1f2937;border-radius:6px;padding:10px;margin:8px 0;
                    display:grid;grid-template-columns:repeat(5,1fr);gap:6px;font-family:Space Mono;font-size:11px;text-align:center;'>
          <div><div style='color:#4b5563;font-size:9px;'>INVERTIDO</div><div style='color:#fff;'>${inv_t:,.2f}</div></div>
          <div><div style='color:#4b5563;font-size:9px;'>TP</div><div style='color:#00ff9d;'>${tp_p:,.4f}</div></div>
          <div><div style='color:#4b5563;font-size:9px;'>SL</div><div style='color:#ff4d6d;'>${sl_p:,.4f}</div></div>
          <div><div style='color:#4b5563;font-size:9px;'>GANANCIA POT.</div><div style='color:#00ff9d;'>+${gan:,.2f}</div></div>
          <div><div style='color:#4b5563;font-size:9px;'>PÉRDIDA POT.</div><div style='color:#ff4d6d;'>-${per:,.2f}</div></div>
        </div>""",unsafe_allow_html=True)
        if st.button("✅ Registrar",key="btn_add"):
            add_trade(ts,tbp,tsh,tbd,ttp,tsl,tnotes); st.success("✅ Registrada."); st.rerun()

    open_t=[t for t in st.session_state.trades if t["status"]=="ABIERTA"]
    closed_t=[t for t in st.session_state.trades if t["status"]!="ABIERTA"]

    if not st.session_state.trades:
        st.markdown("<div style='background:#0d1117;border:1px dashed #1f2937;border-radius:10px;padding:40px;text-align:center;color:#4b5563;'>📂 Sin posiciones registradas.</div>",unsafe_allow_html=True)
    else:
        sm1,sm2,sm3,sm4=st.columns(4)
        sm1.metric("Total Invertido",f"${sum(t['invested'] for t in st.session_state.trades):,.2f}")
        sm2.metric("Abiertas",str(len(open_t)))
        sm3.metric("Cerradas",str(len(closed_t)))
        sm4.metric("P&L Realizado",f"${sum(t.get('pnl',0) for t in closed_t):+,.2f}")

        if open_t:
            st.markdown("#### 🟢 Posiciones Abiertas")
            for trade in open_t:
                oi=st.session_state.trades.index(trade)
                try:
                    cpd=fetch_data(trade["symbol"],"1d","1h"); cp=float(cpd["close"].iloc[-1]) if not cpd.empty else trade["buy_price"]
                except: cp=trade["buy_price"]
                up=round((cp-trade["buy_price"])*trade["shares"],2)
                upc=round((cp-trade["buy_price"])/trade["buy_price"]*100,2)
                pc="#00ff9d" if up>=0 else "#ff4d6d"
                a_info=ALL_ASSETS.get(trade["symbol"],{})
                b_venta=get_broker_for_asset(a_info,"VENDER")
                if cp>=trade["tp_price"]: am,ac=f"🎯 TAKE PROFIT — Vende en {b_venta}","#00ff9d"
                elif cp<=trade["sl_price"]: am,ac=f"🛑 STOP LOSS — Sal ahora en {b_venta}","#ff4d6d"
                elif upc>=trade["tp_pct"]*0.7: am,ac="⚡ Cerca del TP. Monitorea.","#ffd60a"
                else: am,ac=f"⏳ Activa — Broker: {b_venta}","#4b5563"
                rt=trade["tp_price"]-trade["sl_price"]; prog=max(0,min(1,(cp-trade["sl_price"])/rt)) if rt>0 else 0.5
                st.markdown(f"""
                <div style='background:#0d1117;border:1px solid #1f2937;border-radius:10px;padding:16px;margin-bottom:10px;'>
                  <div style='display:flex;justify-content:space-between;margin-bottom:10px;flex-wrap:wrap;gap:8px;'>
                    <div>
                      <span style='color:#fff;font-family:Space Mono;font-weight:700;font-size:15px;'>{trade["symbol"]}</span>
                      <span style='color:#4b5563;font-size:11px;margin-left:8px;'>{trade["shares"]} uds · ${trade["buy_price"]:,.4f} · {trade["buy_date"]}</span>
                      {f'<div style="color:#6b7280;font-size:10px;">{trade["notes"]}</div>' if trade["notes"] else ""}
                    </div>
                    <div style='text-align:right;'>
                      <div style='color:#fff;font-family:Space Mono;font-size:16px;font-weight:700;'>${cp:,.4f}</div>
                      <div style='color:{pc};font-family:Space Mono;'>{upc:+.2f}% ({up:+,.2f} USD)</div>
                    </div>
                  </div>
                  <div style='display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:10px;font-family:Space Mono;font-size:10px;'>
                    <div style='background:#060a0f;border-radius:6px;padding:8px;text-align:center;'><div style='color:#4b5563;font-size:9px;'>COMPRA</div><div style='color:#9ca3af;'>${trade["buy_price"]:,.4f}</div></div>
                    <div style='background:#060a0f;border:1px solid #00ff9d30;border-radius:6px;padding:8px;text-align:center;'><div style='color:#4b5563;font-size:9px;'>TP 🎯</div><div style='color:#00ff9d;'>${trade["tp_price"]:,.4f}</div></div>
                    <div style='background:#060a0f;border:1px solid #ff4d6d30;border-radius:6px;padding:8px;text-align:center;'><div style='color:#4b5563;font-size:9px;'>SL 🛑</div><div style='color:#ff4d6d;'>${trade["sl_price"]:,.4f}</div></div>
                    <div style='background:#060a0f;border:1px solid #1f2937;border-radius:6px;padding:8px;text-align:center;'><div style='color:#4b5563;font-size:9px;'>INVERTIDO</div><div style='color:#9ca3af;'>${trade["invested"]:,.2f}</div></div>
                  </div>
                  <div style='background:#1f2937;border-radius:4px;height:5px;margin-bottom:8px;'>
                    <div style='background:linear-gradient(90deg,#ff4d6d,#ffd60a,#00ff9d);border-radius:4px;height:5px;width:{prog*100:.1f}%;'></div>
                  </div>
                  <div style='background:{ac}15;border:1px solid {ac}40;border-radius:6px;padding:8px 12px;font-size:11px;color:{ac};'>{am}</div>
                </div>""",unsafe_allow_html=True)
                with st.expander(f"Cerrar {trade['symbol']}"):
                    sc1,sc2=st.columns(2)
                    with sc1: sp=st.number_input("Precio venta",min_value=0.0001,value=float(round(cp,4)),step=0.0001,format="%.4f",key=f"sp{oi}")
                    with sc2: sd=st.date_input("Fecha venta",value=pd.Timestamp.today(),key=f"sd{oi}")
                    pp=round((sp-trade["buy_price"])*trade["shares"],2)
                    ppp=round((sp-trade["buy_price"])/trade["buy_price"]*100,2)
                    st.markdown(f"<div style='font-family:Space Mono;text-align:center;padding:10px;color:{'#00ff9d' if pp>=0 else '#ff4d6d'};font-size:16px;font-weight:700;'>{pp:+,.2f} USD ({ppp:+.2f}%)</div>",unsafe_allow_html=True)
                    if st.button("Confirmar cierre",key=f"close{oi}"): close_trade(oi,sp,sd); st.success("Cerrada."); st.rerun()

        if closed_t:
            st.markdown("#### 📋 Historial")
            df_hist=pd.DataFrame([{"Activo":t["symbol"],"Compra":f"${t['buy_price']:,.4f}","Venta":f"${t['sell_price']:,.4f}","Cant":t["shares"],"P&L":f"${t.get('pnl',0):+,.2f}","Rend":f"{t.get('pnl_pct',0):+.2f}%","Estado":t["status"]} for t in closed_t])
            st.dataframe(df_hist,use_container_width=True,hide_index=True)
        if st.button("🗑️ Borrar todo"): st.session_state.trades=[]; st.rerun()

# ── TAB 6: ALERTAS Y ESCÁNER ───────────────────────────────────────────────────
with t6:
    st.markdown("### 🔔 Alertas Automáticas — 120+ activos vigilados")
    cfg2=st.session_state.email_config

    with st.expander("📖 Cómo configurar Gmail",expanded=not cfg2.get("active")):
        st.markdown("""
        <div style='background:#0d1117;border:1px solid #1f2937;border-radius:8px;padding:16px;font-size:12px;color:#9ca3af;line-height:1.9;'>
        <b style='color:#ffd60a;'>Paso 1:</b> gmail.com → Configuración → Seguridad → Verificación en 2 pasos → Activar<br>
        <b style='color:#ffd60a;'>Paso 2:</b> myaccount.google.com/apppasswords → "Otra" → "QuantumTrade" → Generar código 16 letras<br>
        <b style='color:#ffd60a;'>Paso 3:</b> Pega ese código en "Contraseña de aplicación" abajo y activa las alertas
        </div>""",unsafe_allow_html=True)

    col_form, col_status = st.columns([1,1])
    with col_form:
        st.markdown("**⚙️ Configuración**")
        e_to   = st.text_input("📨 Correo destino", value=cfg2.get("to",""), placeholder="tu@correo.com",key="eto")
        e_from = st.text_input("📤 Tu Gmail",       value=cfg2.get("from",""), placeholder="tucorreo@gmail.com",key="efrom")
        e_pass = st.text_input("🔑 Contraseña app (16 letras)", value=cfg2.get("pass",""), type="password",key="epass")
        e_on   = st.toggle("🔔 Alertas automáticas activas", value=cfg2.get("active",False),key="aon")

        c_b1,c_b2=st.columns(2)
        with c_b1:
            if st.button("💾 Guardar"):
                st.session_state.email_config={"to":e_to,"from":e_from,"pass":e_pass,"active":e_on}
                st.success("✅ Guardado.")
        with c_b2:
            if st.button("🧪 Correo prueba"):
                if e_to and e_from and e_pass:
                    test_entry=[{"symbol":symbol,"name":info["name"],"price":price_now,"strength":sig["strength"],
                        "razon":" · ".join(sig["reasons"][:2]),"broker":broker_recom,"tp":proj_tp,"sl":proj_sl,
                        "invertir":invest_amt,"accion_recomendada":f"COMPRAR en {broker_recom}","color":"#00ff9d","time":datetime.now().strftime("%H:%M"),"type":"COMPRAR"}]
                    html=build_alert_email(test_entry,[],[],[],portfolio)
                    ok,msg=send_email(e_to,e_from,e_pass,f"🧪 PRUEBA Quantum Trade — {symbol}",html)
                    st.success(msg) if ok else st.error(msg)
                else: st.warning("Completa los campos.")

        st.markdown("<br>**📤 Alerta manual**")
        a_sym=st.selectbox("Activo",list(ALL_ASSETS.keys()),index=list(ALL_ASSETS.keys()).index(symbol),key="as2")
        a_type=st.radio("Tipo",["🟢 COMPRA","🔴 VENTA"],horizontal=True,key="atype")
        if st.button("📧 Enviar alerta",key="send_manual"):
            if e_to and e_from and e_pass:
                a_info2=ALL_ASSETS.get(a_sym,{}); b2=get_broker_for_asset(a_info2,"COMPRAR" if "COMPRA" in a_type else "VENDER")
                entry=[{"symbol":a_sym,"name":a_info2.get("name",a_sym),"price":price_now,"strength":sig["strength"],
                    "razon":"Señal manual","broker":b2,"tp":proj_tp,"sl":proj_sl,"invertir":invest_amt,
                    "accion_recomendada":f"{'COMPRAR' if 'COMPRA' in a_type else 'VENDER'} en {b2}","color":"#00ff9d","time":datetime.now().strftime("%H:%M")}]
                if "COMPRA" in a_type: html=build_alert_email(entry,[],[],[],portfolio)
                else: html=build_alert_email([],entry,[],[],portfolio)
                ok,msg=send_email(e_to,e_from,e_pass,f"{'🟢' if 'COMPRA' in a_type else '🔴'} Alerta {a_sym}",html)
                st.success(msg) if ok else st.error(msg)
            else: st.warning("Configura el correo primero.")

    with col_status:
        sca=cfg2.get("active") and cfg2.get("to") and cfg2.get("from") and cfg2.get("pass")
        sc_color="#00ff9d" if sca else "#4b5563"
        secs_left2=max(0,SCAN_INTERVAL-(time.time()-st.session_state.last_scan_time))
        pct2=int((1-secs_left2/SCAN_INTERVAL)*100)
        ultimo=datetime.fromtimestamp(st.session_state.last_scan_time).strftime("%H:%M:%S") if st.session_state.last_scan_time>0 else "Nunca"
        st.markdown(f"""
        <div style='background:#0d1117;border:1px solid #1f2937;border-radius:10px;padding:16px;'>
          <div style='display:flex;align-items:center;gap:8px;margin-bottom:14px;'>
            <div style='width:10px;height:10px;border-radius:50%;background:{sc_color};{"box-shadow:0 0 10px "+sc_color if sca else ""};'></div>
            <span style='color:{sc_color};font-family:Space Mono;font-size:12px;font-weight:700;'>ESCÁNER {"ACTIVO" if sca else "INACTIVO"}</span>
          </div>
          <div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:12px;text-align:center;font-family:Space Mono;'>
            <div style='background:#060a0f;border:1px solid #1f2937;border-radius:6px;padding:10px;'>
              <div style='color:#4b5563;font-size:9px;'>ACTIVOS</div>
              <div style='color:#00ff9d;font-size:20px;font-weight:700;'>{len(ALL_ASSETS)}</div>
            </div>
            <div style='background:#060a0f;border:1px solid #1f2937;border-radius:6px;padding:10px;'>
              <div style='color:#4b5563;font-size:9px;'>PRÓXIMO</div>
              <div style='color:#ffd60a;font-size:18px;font-weight:700;'>{int(secs_left2//60):02d}:{int(secs_left2%60):02d}</div>
            </div>
            <div style='background:#060a0f;border:1px solid #1f2937;border-radius:6px;padding:10px;'>
              <div style='color:#4b5563;font-size:9px;'>SEÑALES</div>
              <div style='color:#9ca3af;font-size:20px;font-weight:700;'>{len(st.session_state.scanner_results)}</div>
            </div>
          </div>
          <div style='background:#1f2937;border-radius:4px;height:5px;margin-bottom:6px;'>
            <div style='background:linear-gradient(90deg,#00ff9d,#ffd60a);border-radius:4px;height:5px;width:{pct2}%;'></div>
          </div>
          <div style='color:#4b5563;font-size:9px;text-align:right;margin-bottom:12px;'>Último: {ultimo}</div>
          <div style='font-size:10px;color:#6b7280;line-height:1.9;border-top:1px solid #1f2937;padding-top:10px;'>
            🟢 <b style='color:#00ff9d;'>COMPRA</b> → señal ≥65% + broker específico<br>
            🔴 <b style='color:#ff4d6d;'>VENTA</b> → señal ≤35% + broker para salir<br>
            🎯 <b style='color:#ffd60a;'>TP/SL</b> → tus posiciones con acción urgente<br>
            📧 Solo envía cuando la señal cambia
          </div>
        </div>""",unsafe_allow_html=True)

        c_sc1,c_sc2=st.columns(2)
        with c_sc1:
            if st.button("🔍 Escanear ahora",key="scan_now"):
                if sca:
                    with st.spinner("Escaneando 120+ activos..."): res=run_scanner(cfg2,st.session_state.trades)
                    st.success(f"✅ {len(res)} señales.") if res else st.info("Sin señales nuevas.")
                else: st.warning("Activa alertas primero.")
        with c_sc2:
            if st.button("🗑️ Limpiar log",key="clear_log"): st.session_state.scanner_results=[]; st.session_state.alert_log=[]; st.rerun()

        if st.session_state.alert_log:
            st.markdown("<div style='margin-top:10px;color:#9ca3af;font-size:11px;font-weight:600;'>📋 Log de correos enviados</div>",unsafe_allow_html=True)
            for log in st.session_state.alert_log[:8]:
                st.markdown(f"<div style='background:#060a0f;border-left:3px solid {log['color']};padding:5px 10px;margin-top:4px;font-size:10px;color:#6b7280;font-family:Space Mono;'>[{log['time']}] {log['msg']}</div>",unsafe_allow_html=True)

    # Historial señales
    if st.session_state.scanner_results:
        st.markdown("<br>**📊 Señales detectadas (últimas 20)**")
        for r in st.session_state.scanner_results[:20]:
            ic={"COMPRAR":"🟢","VENDER":"🔴","TP":"🎯","SL":"🛑"}.get(r.get("type",""),"📊")
            b_shown=r.get("broker","").split("(")[0].strip()
            st.markdown(f"""
            <div style='background:#060a0f;border-left:3px solid {r["color"]};border-radius:0 6px 6px 0;
                        padding:8px 14px;margin-bottom:4px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;'>
              <div>
                <span style='color:#fff;font-family:Space Mono;font-weight:700;'>{ic} {r["symbol"]}</span>
                <span style='background:{r["color"]}20;color:{r["color"]};padding:1px 7px;border-radius:3px;font-size:9px;font-family:Space Mono;margin-left:8px;'>{r.get("type","")}</span>
                <span style='color:#4b5563;font-size:10px;margin-left:8px;'>${r["price"]:,.4f} · {r["strength"]}%</span>
                <span style='background:#0ea5e920;color:#0ea5e9;padding:1px 6px;border-radius:3px;font-size:9px;margin-left:6px;'>🏦 {b_shown}</span>
                <div style='color:#6b7280;font-size:10px;margin-top:2px;'>{r["reason"]}</div>
              </div>
              <span style='color:#374151;font-family:Space Mono;font-size:10px;'>{r["time"]}</span>
            </div>""",unsafe_allow_html=True)

# ── TAB 7: BROKERS ─────────────────────────────────────────────────────────────
with t7:
    st.markdown("### 🏦 Brokers — Cuál usar según lo que quieres invertir")
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#00ff9d10,#0ea5e910);border:2px solid #00ff9d50;border-radius:12px;padding:18px;margin-bottom:16px;'>
      <div style='color:#00ff9d;font-size:10px;letter-spacing:2px;font-weight:700;margin-bottom:8px;'>⭐ PARA {symbol} LA APP RECOMIENDA</div>
      <div style='color:#fff;font-size:20px;font-weight:700;margin-bottom:4px;'>{broker_recom}</div>
      <div style='color:#9ca3af;font-size:12px;'>Tipo de activo: {info["tipo"]} · Sector: {info["sector"]} · Riesgo: {info["riesgo"]}</div>
    </div>""",unsafe_allow_html=True)

    cl1,cl2=st.columns(2)
    pal2=["#00ff9d","#0ea5e9","#ffd60a","#a78bfa","#f97316","#ec4899"]
    for i,(bname,binfo) in enumerate(BROKERS_DETAIL.items()):
        with (cl1 if i%2==0 else cl2):
            bc=pal2[i]
            activos_html=" · ".join([f"<span style='color:#9ca3af;'>{a}</span>" for a in binfo["activos"]])
            stars="".join([f'<span style="display:inline-block;width:9px;height:9px;border-radius:2px;background:{""+bc if j<int(binfo["rating"]) else "#1f2937"};margin-right:2px;"></span>' for j in range(10)])
            col_badge="✅ Colombia" if binfo["colombia"] else "⚠️ Limitado"
            col_color="#00ff9d" if binfo["colombia"] else "#ffd60a"
            st.markdown(f"""
            <div style='background:#0d1117;border:1px solid #1f2937;border-top:3px solid {bc};border-radius:10px;padding:16px;margin-bottom:14px;'>
              <div style='display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;'>
                <div>
                  <div style='color:#fff;font-weight:700;font-size:15px;'>{bname}</div>
                  <div style='color:#4b5563;font-size:10px;'>{binfo["url"]}</div>
                </div>
                <div style='color:{bc};font-family:Space Mono;font-size:20px;font-weight:700;'>{binfo["rating"]}</div>
              </div>
              <div style='background:{bc}15;border:1px solid {bc}40;border-radius:4px;padding:6px 10px;margin-bottom:10px;font-size:11px;color:{bc};font-weight:600;'>{binfo["ideal"]}</div>
              <div style='display:flex;gap:6px;margin-bottom:8px;flex-wrap:wrap;'>
                <span style='background:{col_color}20;color:{col_color};padding:2px 7px;border-radius:3px;font-size:10px;'>{col_badge}</span>
                <span style='background:#0ea5e920;color:#0ea5e9;padding:2px 7px;border-radius:3px;font-size:10px;'>Min: {binfo["min"]}</span>
                <span style='background:#1f2937;color:#9ca3af;padding:2px 7px;border-radius:3px;font-size:10px;'>Comisión: {binfo["fee"]}</span>
                {"<span style='background:#00ff9d20;color:#00ff9d;padding:2px 7px;border-radius:3px;font-size:10px;'>Fraccionadas ✅</span>" if binfo["fraccion"] else ""}
              </div>
              <div style='color:#6b7280;font-size:10px;margin-bottom:8px;'>Activos: {activos_html}</div>
              <div style='background:#060a0f;border:1px solid #0ea5e930;border-radius:4px;padding:7px 10px;font-size:11px;color:#0ea5e9;margin-bottom:8px;'>💡 {binfo["tip"]}</div>
              <div>{stars}</div>
            </div>""",unsafe_allow_html=True)

    st.markdown("""
    <div style='background:#0d1117;border:1px solid #1f2937;border-radius:10px;padding:18px;margin-top:4px;'>
      <div style='color:#ffd60a;font-size:13px;font-weight:700;margin-bottom:12px;'>🗺️ Guía rápida: ¿En cuál broker compro cada cosa?</div>
      <table width='100%' style='border-collapse:collapse;font-size:11px;'>
        <tr style='border-bottom:1px solid #1f2937;'>
          <th style='color:#4b5563;padding:8px;text-align:left;font-size:9px;letter-spacing:1px;'>QUIERO INVERTIR EN...</th>
          <th style='color:#4b5563;padding:8px;text-align:left;font-size:9px;letter-spacing:1px;'>BROKER</th>
          <th style='color:#4b5563;padding:8px;text-align:left;font-size:9px;letter-spacing:1px;'>MIN. PARA EMPEZAR</th>
          <th style='color:#4b5563;padding:8px;text-align:left;font-size:9px;letter-spacing:1px;'>COMISIÓN</th>
        </tr>
        <tr style='border-bottom:1px solid #1f2937;'><td style='padding:8px;color:#fff;'>Acciones EEUU (AAPL, NVDA...)</td><td style='padding:8px;color:#00ff9d;font-weight:700;'>XTB</td><td style='padding:8px;color:#9ca3af;'>$1 USD</td><td style='padding:8px;color:#9ca3af;'>$0</td></tr>
        <tr style='border-bottom:1px solid #1f2937;'><td style='padding:8px;color:#fff;'>ETFs (SPY, QQQ, VTI...)</td><td style='padding:8px;color:#00ff9d;font-weight:700;'>XTB / Schwab</td><td style='padding:8px;color:#9ca3af;'>$1 USD</td><td style='padding:8px;color:#9ca3af;'>$0</td></tr>
        <tr style='border-bottom:1px solid #1f2937;'><td style='padding:8px;color:#fff;'>Criptomonedas (BTC, ETH, SOL...)</td><td style='padding:8px;color:#ffd60a;font-weight:700;'>Binance</td><td style='padding:8px;color:#9ca3af;'>$1 USD</td><td style='padding:8px;color:#9ca3af;'>0.1%</td></tr>
        <tr style='border-bottom:1px solid #1f2937;'><td style='padding:8px;color:#fff;'>Forex / Divisas (EUR/USD, USD/COP...)</td><td style='padding:8px;color:#00ff9d;font-weight:700;'>XTB</td><td style='padding:8px;color:#9ca3af;'>$1 USD</td><td style='padding:8px;color:#9ca3af;'>Solo spread</td></tr>
        <tr style='border-bottom:1px solid #1f2937;'><td style='padding:8px;color:#fff;'>Oro, Petróleo, Materias primas</td><td style='padding:8px;color:#00ff9d;font-weight:700;'>XTB / IBKR</td><td style='padding:8px;color:#9ca3af;'>$1 USD</td><td style='padding:8px;color:#9ca3af;'>Variable</td></tr>
        <tr style='border-bottom:1px solid #1f2937;'><td style='padding:8px;color:#fff;'>Acciones internacionales (ASML, TSM...)</td><td style='padding:8px;color:#0ea5e9;font-weight:700;'>IBKR / Saxo</td><td style='padding:8px;color:#9ca3af;'>$0 / $2000</td><td style='padding:8px;color:#9ca3af;'>$0 / Variable</td></tr>
        <tr><td style='padding:8px;color:#fff;'>Ecopetrol, Bancolombia (NYSE)</td><td style='padding:8px;color:#00ff9d;font-weight:700;'>XTB / IBKR</td><td style='padding:8px;color:#9ca3af;'>$1 USD</td><td style='padding:8px;color:#9ca3af;'>$0</td></tr>
      </table>
    </div>
    <div style='background:#ff4d6d10;border:1px solid #ff4d6d30;border-radius:8px;padding:12px;margin-top:10px;font-size:11px;color:#6b7280;'>
      ⚠️ Herramienta educativa. No constituye asesoría financiera certificada. Toda inversión conlleva riesgo.
    </div>""",unsafe_allow_html=True)

# ─── AUTO REFRESH ──────────────────────────────────────────────────────────────
if auto_ref:
    time.sleep(30)
    st.rerun()
