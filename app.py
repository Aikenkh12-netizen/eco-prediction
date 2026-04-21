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

# Кастомный CSS для крутого дизайна
st.markdown("""
    <style>
    /* Основной фон и шрифты */
    .stApp {
        background-color: #0e1117;
    }
    
    /* Градиентный заголовок */
    .main-title {
        font-size: 45px !important;
        font-weight: 800 !important;
        background: -webkit-linear-gradient(#00f2fe, #4facfe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    
    /* Стилизация карточек метрик */
    [data-testid="stMetric"] {
        background-color: #161b22;
        padding: 15px;
        border-radius: 15px;
        border: 1px solid #30363d;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    
    [data-testid="stMetricValue"] {
        color: #00f2fe !important;
    }

    /* Стилизация вкладок */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #161b22;
        border-radius: 10px 10px 0px 0px;
        padding: 10px 20px;
        color: white;
    }

    /* Кнопки */
    .stButton>button {
        border-radius: 10px !important;
        border: 1px solid #4facfe !important;
        background-color: transparent !important;
        transition: 0.3s !important;
    }
    
    .stButton>button:hover {
        background-color: #4facfe !important;
        color: black !important;
        box-shadow: 0 0 15px #4facfe;
    }
    </style>
    """, unsafe_allow_html=True)

GROQ_API_KEY = "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"

# ====================== БАЗА ДАННЫХ (16 водоёмов) ======================
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

# ====================== СОХРАНЕНИЕ ПАРАМЕТРОВ ======================
if 'lake_params' not in st.session_state:
    st.session_state.lake_params = {
        name: {"ph": 7.2, "temp": 18.0, "turb": 4.0} for name in LAKES_DB.keys()
    }

# ====================== БОКОВАЯ ПАНЕЛЬ ======================
with st.sidebar:
    st.markdown("### 🚀 SuVision Core")
    selected_name = st.selectbox("🎯 Станция мониторинга", list(LAKES_DB.keys()))
    lake = LAKES_DB[selected_name]
    
    st.divider()
    st.header("🔹 Параметры воды")
    
    current = st.session_state.lake_params[selected_name]
    
    ph = st.slider("pH", 0.0, 14.0, current["ph"], 0.1)
    temp = st.slider("Температура (°C)", 0.0, 40.0, current["temp"], 0.5)
    turb = st.slider("Мутность (NTU)", 0.0, 100.0, current["turb"], 1.0)
  
    if st.button("🔄 Обновить симуляцию", use_container_width=True):
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

# ====================== Groq функции ======================
def get_ai_report(lake_name, ph, temp, turb, sri, risk):
    url = "https://api.groq.com/openai/v1/chat/completions"
    prompt = f"""Ты опытный эколог-гидролог. Кратко проанализируй состояние водоёма.
Объект: {lake_name}
Параметры: pH = {ph}, температура = {temp}°C, мутность = {turb} NTU
SRI: {sri}/10
Основной риск: {risk}
Ответь ровно двумя предложениями на русском:
1. Оценка текущего состояния.
2. Главная рекомендация."""

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 180,
        "temperature": 0.65
    }
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
  
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=12)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
        return f"Ошибка Groq ({response.status_code})"
    except Exception as e:
        return f"Ошибка подключения: {str(e)}"

def analyze_photo_with_groq(image_file, lake_name):
    if image_file is None:
        return "Нет изображения для анализа."
    
    image_bytes = image_file.getvalue()
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    prompt = f"Проанализируй это фото воды из водоёма {lake_name}. Оцени мутность, цвет и видимые загрязнения. Дай оценку 1-10."

    payload = {
        "model": "llava-v1.5-7b-4096-preview", # Используем модель с поддержкой зрения если доступна, либо аналоги
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        "max_tokens": 400
    }
    
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    try:
        with st.spinner("🤖 Анализ фото..."):
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content'].strip()
            return f"Ошибка Groq Vision ({response.status_code})"
    except Exception as e:
        return f"Ошибка: {str(e)}"

# ====================== ОСНОВНОЙ ИНТЕРФЕЙС ======================
st.markdown('<p class="main-title">🌊 SuVision Global AI</p>', unsafe_allow_html=True)
st.markdown(f"📍 **Объект:** `{selected_name}` | ⚠️ **Риск:** {lake['risk']}")

# Верхняя панель со статусом
st.markdown(f"### Текущее состояние: :{status_type}[{status_text}]")

# Метрики в красивых карточках
m1, m2, m3, m4 = st.columns(4)
m1.metric("pH Level", f"{ph:.2f}")
m2.metric("Temp", f"{temp:.1f} °C")
m3.metric("Turbidity", f"{turb:.1f} NTU")
m4.metric("SRI Index", f"{sri}/10", delta=round(sri - 7.0, 2))

st.divider()

# Вкладки
tab1, tab2, tab3 = st.tabs(["🗺️ Мониторинг & ИИ", "📷 Фото-анализ", "📈 Логи"])

with tab1:
    c1, c2 = st.columns([1.5, 1])
    
    with c1:
        st.subheader("🗺️ Гео-позиция станции")
        m = folium.Map(location=lake["coords"], zoom_start=6, tiles="CartoDB dark_matter")
        color = "green" if sri > 7 else "orange" if sri > 4 else "red"
        folium.CircleMarker(
            location=lake["coords"],
            radius=15,
            color=color,
            fill=True,
            fillOpacity=0.7,
            popup=f"{selected_name}: SRI {sri}"
        ).add_to(m)
        st_folium(m, width="100%", height=400)
    
    with c2:
        st.subheader("🤖 Экспертный ИИ")
        if st.button("🚀 Запустить диагностику", type="primary", use_container_width=True):
            report = get_ai_report(selected_name, ph, temp, turb, sri, lake['risk'])
            st.info(report)

        # Gauge Chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=sri,
            gauge={'axis': {'range': [0, 10]},
                   'bar': {'color': "#00f2fe"},
                   'steps': [
                       {'range': [0, 4], 'color': "#440000"},
                       {'range': [4, 7], 'color': "#663300"},
                       {'range': [7, 10], 'color': "#003311"}]}
        ))
        fig.update_layout(height=220, paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"}, margin=dict(l=20,r=20,t=20,b=20))
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("📷 Анализ по визуальным данным")
    up_col, cam_col = st.columns(2)
    with up_col:
        uploaded_file = st.file_uploader("Загрузить снимок", type=["jpg", "png"])
    with cam_col:
        camera_file = st.camera_input("Сделать фото")
  
    photo = uploaded_file or camera_file
    if photo:
        st.image(photo, caption="Снимок для анализа", use_container_width=True)
        if st.button("🔍 Начать ИИ-сканирование", use_container_width=True):
            res = analyze_photo_with_groq(photo, selected_name)
            st.success(res)

with tab3:
    st.subheader("📈 История измерений")
    if 'history' not in st.session_state:
        st.session_state.history = []
  
    if st.button("📌 Логировать текущие данные"):
        st.session_state.history.append({
            "Дата/Время": datetime.now().strftime("%d.%m %H:%M"),
            "Объект": selected_name,
            "pH": ph, "T °C": temp, "NTU": turb, "SRI": sri
        })
  
    if st.session_state.history:
        st.table(pd.DataFrame(st.session_state.history).tail(10))
    else:
        st.write("История пуста.")

st.markdown("---")
st.caption("SuVision Global AI • 2026 • Интеллектуальная защита водных ресурсов Казахстана 💧")
