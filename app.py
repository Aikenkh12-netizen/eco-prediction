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
    "Озеро Борли": {"coords": [53.0800, 70.3000], "type": "Пресноводный", "risk": "Эвтрофикация"},  # Боровое / Борли
    "Озеро Иссык": {"coords": [43.2500, 77.4800], "type": "Горное", "risk": "Селевые риски"},
    "Озеро Кольсай": {"coords": [42.9300, 78.3300], "type": "Горное", "risk": "Туризм и экология"},
    "Озеро Кайынды": {"coords": [42.9800, 78.4500], "type": "Горное", "risk": "Туризм"},
    "Малое Аральское море": {"coords": [46.0000, 59.5000], "type": "Соленое", "risk": "Усыхание и экокатастрофа"},
    "Озеро Тузколь": {"coords": [43.0000, 74.5000], "type": "Соленое", "risk": "Минерализация"}
}

# ====================== БОКОВАЯ ПАНЕЛЬ ======================
with st.sidebar:
    st.title("🚀 SuVision Core")
    selected_name = st.selectbox("🎯 Станция мониторинга", list(LAKES_DB.keys()))
    lake = LAKES_DB[selected_name]
   
    st.divider()
    st.header("🔹 Параметры воды")
    ph = st.slider("pH", 0.0, 14.0, 7.2, 0.1)
    temp = st.slider("Температура (°C)", 0.0, 40.0, 18.0, 0.5)
    turb = st.slider("Мутность (NTU)", 0.0, 100.0, 4.0, 1.0)
   
    if st.button("🔄 Симулировать новые измерения", use_container_width=True):
        st.rerun()

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
    
    prompt = f"""Ты — эксперт-гидролог и эколог по водоёмам Казахстана, особенно {lake_name}.
    
Проанализируй это фото воды внимательно:
- Оценка мутности (низкая / средняя / высокая) + примерное значение в NTU
- Цвет воды и возможные причины
- Признаки загрязнения (нефтяная плёнка, водоросли, пена, мусор, масляные пятна и т.д.)
- Общая оценка качества воды (1–10)
- Главная рекомендация, что делать сейчас

Отвечай на русском языке чётко, по делу, используй эмодзи где уместно."""

    payload = {
        "model": "llama-4-scout-17b-16e-instruct",   # Vision-модель
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        "max_tokens": 400,
        "temperature": 0.5
    }
    
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    try:
        with st.spinner("🤖 Groq Vision анализирует фото... (3–8 сек)"):
            response = requests.post(url, json=payload, headers=headers, timeout=25)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content'].strip()
            else:
                return f"Ошибка Groq Vision ({response.status_code})"
    except Exception as e:
        return f"Ошибка анализа фото: {str(e)}"

# ====================== ОСНОВНОЙ ИНТЕРФЕЙС ======================
st.title("🌊 SuVision: Глобальный мониторинг водоёмов")
st.markdown(f"**Объект:** `{selected_name}` | **Основной риск:** {lake['risk']}")
st.markdown(f"### Состояние водоёма: **:{status_type}[{status_text}]**")

# Метрики
col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("pH", f"{ph:.2f}")
with col2: st.metric("Температура", f"{temp:.1f} °C")
with col3: st.metric("Мутность", f"{turb:.1f} NTU")
with col4: st.metric("Индекс SRI", f"{sri}/10", delta=round(sri - 7.0, 2))

# Вкладки
tab1, tab2, tab3 = st.tabs(["🗺️ Карта & ИИ", "📷 Анализ по фото", "📈 История"])

with tab1:
    col_map, col_ai = st.columns([2, 1])
    
    with col_map:
        st.subheader("🗺️ Карта мониторинга")
        m = folium.Map(location=lake["coords"], zoom_start=5, tiles="CartoDB dark_matter")
        
        for name, info in LAKES_DB.items():
            is_target = (name == selected_name)
            color = "green" if sri > 7 else "orange" if sri > 4 else "red"
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
        st.subheader("🤖 ИИ-Анализ (Groq)")
        if st.button("🚀 Запустить диагностику", type="primary", use_container_width=True):
            with st.spinner("Анализирую данные..."):
                report = get_ai_report(selected_name, ph, temp, turb, sri, lake['risk'])
                st.success("Анализ завершён")
                st.info(report)

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=sri,
            title={"text": "Состояние водоёма"},
            gauge={'axis': {'range': [0, 10]},
                   'bar': {'color': "#00f2fe"},
                   'steps': [
                       {'range': [0, 4], 'color': "#440000"},
                       {'range': [4, 7], 'color': "#663300"},
                       {'range': [7, 10], 'color': "#003311"}
                   ]}
        ))
        fig.update_layout(height=260, paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"})
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("📷 Анализ качества воды по фотографии")
    uploaded_file = st.file_uploader("Загрузите фото воды", type=["jpg", "jpeg", "png"])
    camera_file = st.camera_input("Или сделайте фото через камеру")
   
    photo = uploaded_file or camera_file
    if photo:
        st.image(photo, caption="Фото для анализа", use_container_width=True)
       
        if st.button("🔍 Запустить профессиональный анализ фото", type="primary"):
            analysis = analyze_photo_with_groq(photo, selected_name)
            st.success("✅ Анализ фото завершён")
            st.markdown(analysis)

with tab3:
    st.subheader("📈 История измерений")
    if 'history' not in st.session_state:
        st.session_state.history = []
   
    if st.button("📌 Сохранить текущие показания"):
        st.session_state.history.append({
            "Время": datetime.now().strftime("%H:%M"),
            "pH": ph,
            "Температура": temp,
            "Мутность": turb,
            "SRI": sri
        })
        st.success("Показания сохранены!")
   
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Пока нет сохранённых измерений.")

st.caption("SuVision Global AI • Работает на Groq • Мониторинг водоёмов Казахстана 💧")
