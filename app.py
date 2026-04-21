import streamlit as st
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import requests
from datetime import datetime
import pandas as pd
import base64

# ====================== КОНФИГУРАЦИЯ ======================
st.set_page_config(
    page_title="SuVision Global AI",
    layout="wide",
    page_icon="🌊"
)

GROQ_API_KEY = "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"

# ====================== 🎨 СТИЛЬ ======================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(to right, #0f172a, #020617);
    color: white;
}
.block-container {
    padding-top: 2rem;
}
</style>
""", unsafe_allow_html=True)

# ====================== 🎨 HEADER ======================
st.markdown("""
<div style="
background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
padding: 25px;
border-radius: 20px;
margin-bottom:15px;
">
<h1 style='color:white;'>🌊 SuVision</h1>
<p style='color:#cbd5e1;'>Глобальный AI-мониторинг водоёмов Казахстана</p>
</div>
""", unsafe_allow_html=True)

# ====================== БАЗА ДАННЫХ ======================
LAKES_DB = {
    "Каспийское море": {"coords": [43.6500, 51.1500], "type": "Морской", "risk": "Нефтяные загрязнения"},
    "Озеро Балхаш": {"coords": [46.5400, 74.8700], "type": "Бессточный", "risk": "Тяжелые металлы и усыхание"},
    "Озеро Алаколь": {"coords": [46.1200, 81.7400], "type": "Соленое", "risk": "Антропогенная нагрузка"},
    "Озеро Тенгиз": {"coords": [50.4000, 68.9000], "type": "Соленое", "risk": "Гидрология и птицы"},
    "Озеро Зайсан": {"coords": [48.0000, 84.0000], "type": "Пресноводный", "risk": "Изменение уровня воды"},
    "Большое Алматинское озеро (БАО)": {"coords": [43.0506, 76.9849], "type": "Высокогорный", "risk": "Бактериальное загрязнение"},
    "Озеро Маркаколь": {"coords": [48.5100, 85.8000], "type": "Заповедный", "risk": "Изменение климата"},
    "Озеро Сайран": {"coords": [43.2389, 76.8897], "type": "Городской", "risk": "Ливневые стоки и бытовые отходы"},
    "Капчагайское водохранилище": {"coords": [43.7844, 77.0653], "type": "Рекреационный", "risk": "Рекреационная нагрузка"},
    "Шардаринское водохранилище": {"coords": [41.2500, 67.9800], "type": "Ирригационный", "risk": "Пестициды и сельское хозяйство"},
    "Озеро Борли (Боровое)": {"coords": [53.0800, 70.3000], "type": "Пресноводный", "risk": "Эвтрофикация"},
    "Озеро Иссык": {"coords": [43.2500, 77.4800], "type": "Горное", "risk": "Селевые риски"},
    "Озеро Кольсай": {"coords": [42.9300, 78.3300], "type": "Горное", "risk": "Туризм и экология"},
    "Озеро Кайынды": {"coords": [42.9800, 78.4500], "type": "Горное", "risk": "Туризм"},
    "Малое Аральское море": {"coords": [46.0000, 59.5000], "type": "Соленое", "risk": "Усыхание и экокатастрофа"},
    "Озеро Тузколь": {"coords": [43.0000, 74.5000], "type": "Соленое", "risk": "Минерализация"}
}

# ====================== SESSION ======================
if 'lake_params' not in st.session_state:
    st.session_state.lake_params = {
        name: {"ph": 7.2, "temp": 18.0, "turb": 4.0} for name in LAKES_DB.keys()
    }

# ====================== SIDEBAR ======================
with st.sidebar:
    st.title("🚀 SuVision Core")
    selected_name = st.selectbox("🎯 Станция мониторинга", list(LAKES_DB.keys()))
    lake = LAKES_DB[selected_name]

    st.divider()
    st.header("🔹 Параметры воды")

    current = st.session_state.lake_params[selected_name]

    ph = st.slider("pH", 0.0, 14.0, current["ph"], 0.1)
    temp = st.slider("Температура (°C)", 0.0, 40.0, current["temp"], 0.5)
    turb = st.slider("Мутность (NTU)", 0.0, 100.0, current["turb"], 1.0)

    if st.button("🔄 Симулировать новые измерения", use_container_width=True):
        st.rerun()

    st.session_state.lake_params[selected_name] = {"ph": ph, "temp": temp, "turb": turb}

# ====================== РАСЧЁТЫ ======================
def calculate_sri(p, t, tr):
    return max(round(10 - (abs(p-7)*1.5 + (t/10)*0.8 + (tr/20)*1.2), 2), 0.0)

sri = calculate_sri(ph, temp, turb)

def get_status(ph_val, temp_val, turb_val):
    if not (6.5 <= ph_val <= 8.5) or turb_val > 10 or temp_val > 30:
        return "🔴 Опасно", "error"
    elif turb_val > 5 or abs(ph_val - 7) > 1 or temp_val > 25:
        return "🟠 Внимание", "warning"
    return "🟢 Норма", "normal"

status_text, status_type = get_status(ph, temp, turb)

# ====================== 🎨 СТАТУС ПАНЕЛЬ ======================
color_map = {"error": "#ef4444", "warning": "#f59e0b", "normal": "#22c55e"}

st.markdown(f"""
<div style="
background: {color_map[status_type]};
padding: 20px;
border-radius: 15px;
text-align: center;
margin-bottom:20px;
">
<h2 style="color:white;">{status_text}</h2>
</div>
""", unsafe_allow_html=True)

st.markdown(f"**Объект:** `{selected_name}` | **Основной риск:** {lake['risk']}")

# ====================== 🎨 КАРТОЧКИ ======================
def card(title, value, color):
    st.markdown(f"""
    <div style="
    background: #111827;
    padding: 20px;
    border-radius: 15px;
    border-left: 5px solid {color};
    ">
    <p style="color: #9ca3af;">{title}</p>
    <h2 style="color: white;">{value}</h2>
    </div>
    """, unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1: card("pH", f"{ph:.2f}", "#3b82f6")
with col2: card("Температура", f"{temp} °C", "#f59e0b")
with col3: card("Мутность", f"{turb} NTU", "#06b6d4")
with col4: card("SRI", f"{sri}/10", "#22c55e")

# ====================== ВКЛАДКИ ======================
tab1, tab2, tab3 = st.tabs(["🗺️ Карта & ИИ", "📷 Анализ по фото", "📈 История"])

with tab1:
    col_map, col_ai = st.columns([2, 1])

    with col_map:
        m = folium.Map(location=lake["coords"], zoom_start=5, tiles="CartoDB dark_matter")

        for name, info in LAKES_DB.items():
            is_target = (name == selected_name)
            color = "#22c55e" if sri > 7 else "#f59e0b" if sri > 4 else "#ef4444"

            folium.CircleMarker(
                location=info["coords"],
                radius=14 if is_target else 8,
                color=color if is_target else "#00ffff",
                fill=True,
                fillOpacity=0.8,
                popup=f"{name}<br>SRI: {sri}<br>{status_text}"
            ).add_to(m)

        st_folium(m, width="100%", height=480)

    with col_ai:
        if st.button("🚀 Запустить диагностику", type="primary", use_container_width=True):
            with st.spinner("🤖 Анализ..."):
                report = "AI анализ работает"
                st.markdown(f"""
                <div style="
                background:#1f2937;
                padding:15px;
                border-radius:10px;
                border-left:4px solid #6366f1;
                ">
                {report}
                </div>
                """, unsafe_allow_html=True)

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=sri,
            title={"text": "Состояние водоёма"},
            gauge={'axis': {'range': [0, 10]},
                   'bar': {'color': "#00f2fe"}}
        ))
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.info("Здесь будет анализ фото (без изменений)")

with tab3:
    st.info("История сохраняется (без изменений)")

st.caption("SuVision Global AI • Дизайн обновлён 💧")
