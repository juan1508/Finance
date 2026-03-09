# 📈 Quantum Trade — AI Stock Analytics Dashboard

Dashboard profesional de análisis técnico bursátil con IA, construido con Streamlit y datos en tiempo real de Yahoo Finance.

## 🚀 Despliegue en Streamlit Cloud (gratis)

### Paso 1: Sube a GitHub
```bash
git init
git add .
git commit -m "Initial commit — Quantum Trade Dashboard"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/quantum-trade.git
git push -u origin main
```

### Paso 2: Despliega en Streamlit Cloud
1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Inicia sesión con GitHub
3. Click **"New app"**
4. Selecciona tu repo `quantum-trade`
5. Main file: `app.py`
6. Click **"Deploy!"**

¡Listo! Tu app estará en: `https://TU_USUARIO-quantum-trade-app-XXXX.streamlit.app`

---

## 📊 Funcionalidades

| Feature | Descripción |
|---|---|
| 📊 Gráfica Principal | Candlestick + MA7/20/50 + Bollinger + MACD + Volumen |
| 📅 Multi-Período | 4 vistas: 5d·1m·6m·5y simultáneas |
| ⚡ RSI & Bollinger | Gauge RSI + bandas interactivas |
| 🧮 Análisis & Señal | Score 0-100 con razones detalladas |
| 🏦 Brokers | 6 brokers recomendados con ratings |

## 🧠 Modelos de Análisis Técnico

- **Medias Móviles**: MA7, MA20, MA50, MA200 con detección de cruces
- **RSI (14)**: Índice de Fuerza Relativa — sobrecomprado/sobrevendido
- **MACD**: Moving Average Convergence Divergence
- **Bandas de Bollinger**: Volatilidad y reversión a la media
- **ATR**: Average True Range — medida de volatilidad
- **Criterio de Kelly**: f* = W − (1−W)/B — fracción óptima a invertir

## 📦 Estructura del Proyecto

```
quantum-trade/
├── app.py              ← Aplicación principal
├── requirements.txt    ← Dependencias Python
├── .streamlit/
│   └── config.toml     ← Configuración tema oscuro
└── README.md
```

## ⚠️ Aviso Legal

Este dashboard es una herramienta educativa de análisis técnico. Las señales generadas **no constituyen asesoría financiera** ni garantizan rentabilidad. Toda inversión conlleva riesgo de pérdida.

---
Desarrollado con ❤️ usando Python · Streamlit · Plotly · yfinance
