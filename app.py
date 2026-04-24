import streamlit as st
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import requests
from datetime import datetime
import pandas as pd
import base64
import serial
import time
import os

# ====================== КОНФИГУРАЦИЯ ======================
st.set_page_config(
    page_title="SuVision Global AI",
    layout="wide",
    page_icon="🌊",
    initial_sidebar_state="expanded"
)

# ====================== КАСТОМНЫЙ ДИЗАЙН ======================
st.markdown("""
<style>
    /* ====================== ГЛОБАЛЬНАЯ ТЕМА ====================== */
    .stApp {
        background: linear-gradient(180deg, #0a1428 0%, #0f253f 100%);
        color: #e0f7ff;
    }
 
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }
    /* ====================== ЗАГОЛОВОК ====================== */
    .main-header {
        background: linear-gradient(90deg, #00d4ff, #0099cc);
        color: white;
        padding: 2rem 2.5rem;
        border-radius: 24px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 15px 35px rgba(0, 212, 255, 0.25);
        position: relative;
        overflow: hidden;
    }
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 40%;
        height: 300%;
        background: linear-gradient(120deg, transparent, rgba(255,255,255,0.3), transparent);
        transform: skewX(-25deg);
        animation: shine 6s linear infinite;
    }
    @keyframes shine {
        100% { transform: translateX(200%); }
    }
    /* ====================== СТАТУС ====================== */
    .status-container {
        background: rgba(255,255,255,0.08);
        backdrop-filter: blur(12px);
        border-radius: 20px;
        padding: 18px 24px;
        margin-bottom: 2rem;
        border: 1px solid rgba(255,255,255,0.1);
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    /* ====================== МЕТРИКИ ====================== */
    .stMetric {
        background: rgba(255,255,255,0.09) !important;
        border-radius: 18px !important;
        padding: 14px 18px !important;
        border: 1px solid rgba(0, 212, 255, 0.15) !important;
        box-shadow: 0 6px 20px rgba(0, 212, 255, 0.1) !important;
        transition: transform 0.2s ease;
    }
    .stMetric:hover {
        transform: translateY(-3px);
    }
    .stMetric label {
        color: #a0d8ff !important;
        font-size: 0.95rem !important;
    }
    .stMetric .metric-value {
        color: #00f2fe !important;
        font-size: 1.65rem !important;
        font-weight: 700;
    }
    /* ====================== КНОПКИ ====================== */
    .stButton button {
        background: linear-gradient(90deg, #00d4ff, #00aaff) !important;
        color: white !important;
        border: none !important;
        border-radius: 16px !important;
        height: 52px !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        box-shadow: 0 8px 20px rgba(0, 212, 255, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    .stButton button:hover {
        transform: translateY(-3px) scale(1.03);
        box-shadow: 0 12px 28px rgba(0, 212, 255, 0.45) !important;
    }
    /* ====================== САЙДБАР ====================== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a1f35, #0f2a45) !important;
        border-right: 4px solid #00d4ff;
    }
</style>
""", unsafe_allow_html=True)

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

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

# ====================== СОХРАНЕНИЕ ПАРАМЕТРОВ ======================
if 'lake_params' not in st.session_state:
    st.session_state.lake_params = {
        name: {"ph": 7.2, "temp": 18.0, "turb": 4.0} for name in LAKES_DB.keys()
    }
if 'ser' not in st.session_state:
    st.session_state.ser = None
if 'live_mode' not in st.session_state:
    st.session_state.live_mode = False
if 'history' not in st.session_state:
    st.session_state.history = []
if 'last_live_values' not in st.session_state:
    st.session_state.last_live_values = {}

# ====================== БОКОВАЯ ПАНЕЛЬ ======================
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
    
    # ====================== ARDUINO ======================
    st.divider()
    st.subheader("🔌 Arduino Uno (датчики)")
 
    col_p, col_b = st.columns(2)
    with col_p:
        default_port = "COM5" if os.name == "nt" else "/dev/ttyUSB0"
        com_port = st.text_input("COM-порт / tty", value=default_port)
    with col_b:
        baud_rate = st.selectbox("Скорость (baud)", [9600, 115200], index=0)
 
    if st.button("🔌 Подключить Arduino", use_container_width=True, type="primary"):
        try:
            if st.session_state.ser is None or not st.session_state.ser.is_open:
                st.session_state.ser = serial.Serial(com_port, baud_rate, timeout=1.5)
                st.success(f"✅ Подключено к {com_port}")
                st.rerun()
        except Exception as e:
            st.error(f"❌ Не удалось подключиться к {com_port}")
            st.caption("💡 **Подсказка**: Запусти приложение **локально** (`streamlit run app.py`) и подключи Arduino.")
    
    if st.session_state.ser and st.session_state.ser.is_open:
        st.markdown('<div class="arduino-connected">🟢 Arduino подключён • Данные поступают</div>', unsafe_allow_html=True)
     
        if st.button("📡 Прочитать данные с датчиков СЕЙЧАС", use_container_width=True, type="primary"):
            try:
                line = st.session_state.ser.readline().decode('utf-8').strip()
                if line and "ph:" in line and "temp:" in line and "turb:" in line:
                    data = {}
                    for item in line.split(","):
                        if ":" in item:
                            k, v = item.split(":")
                            data[k.strip().lower()] = float(v.strip())
                    
                    st.session_state.lake_params[selected_name] = {
                        "ph": round(data.get("ph", ph), 2),
                        "temp": round(data.get("temp", temp), 1),
                        "turb": round(data.get("turb", turb), 1)
                    }
                    st.toast("✅ Данные с Arduino успешно получены!", icon="📡")
                    st.rerun()
            except Exception as e:
                st.error(f"Ошибка чтения: {e}")
     
        if st.button("🔌 Отключить Arduino", use_container_width=True):
            st.session_state.ser.close()
            st.session_state.ser = None
            st.success("Arduino отключён")
            st.rerun()
        
        live_mode = st.checkbox("🔴 Включить non-stop поток данных с Arduino (автообновление каждые 5 сек)",
                                value=st.session_state.live_mode,
                                key="live_mode_checkbox")
        st.session_state.live_mode = live_mode

    st.caption("Ожидаемый формат от Arduino:\n`ph:7.45,temp:23.1,turb:4.2`")

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
    payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}], "max_tokens": 180, "temperature": 0.65}
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=12)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
        return f"Ошибка Groq ({response.status_code})"
    except Exception as e:
        return f"Ошибка подключения: {str(e)}"

def get_ai_forecast(lake_name, ph, temp, turb, sri, risk, history=None):
    url = "https://api.groq.com/openai/v1/chat/completions"
    history_str = ""
    if history and len(history) > 0:
        history_str = "Последние измерения: " + ", ".join([f"{h['Время']}: pH={h['pH']}, T={h['Температура']}, Turb={h['Мутность']}" for h in history[-3:]])
    prompt = f"""Ты опытный эколог-гидролог, специализирующийся на водоёмах Казахстана.
Анализируй текущие данные и сделай прогноз риска загрязнения или цветения (эвтрофикации) водоёма.
Объект: {lake_name}
Параметры сейчас: pH = {ph}, температура = {temp}°C, мутность = {turb} NTU, SRI = {sri}/10
Основной риск: {risk}
{history_str}
Ответь **ровно двумя предложениями** на русском языке:
1. Краткий прогноз на 3–7 дней (низкий/средний/высокий риск загрязнения или цветения водорослей).
2. Действия: если риск высокий — **ПРЕДУПРЕЖДЕНИЕ** с рекомендациями."""
    payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}], "max_tokens": 200, "temperature": 0.6}
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=12)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
        return f"Ошибка Groq ({response.status_code})"
    except Exception as e:
        return f"Ошибка прогноза: {str(e)}"

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
- Признаки загрязнения (нефтяная плёнка, водоросли, пена, мусор, масляные пятна, цветение и т.д.)
- Общая оценка качества воды (1–10)
- Главная рекомендация, что делать сейчас
Отвечай на русском языке чётко, по делу, используй эмодзи где уместно."""
    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]}],
        "max_tokens": 400,
        "temperature": 0.5
    }
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    try:
        with st.spinner("🤖 Groq Vision анализирует фото..."):
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content'].strip()
            else:
                return f"Ошибка Groq Vision ({response.status_code})"
    except Exception as e:
        return f"Ошибка анализа фото: {str(e)}"

# ====================== ОСНОВНОЙ ИНТЕРФЕЙС ======================
st.markdown('<div class="main-header"><h1 style="margin:0;font-size:3em;font-weight:800;">🌊 SuVision Global AI</h1><p style="margin:8px 0 0 0;font-size:1.35em;opacity:0.95;">Глобальный мониторинг водоёмов Казахстана • Работает на Groq</p></div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="status-container">
    <div style="font-size:1.4em;font-weight:700;">Объект: <span style="color:#00f2fe;font-family:monospace">{selected_name}</span></div>
    <div style="font-size:1.1em;">Основной риск: <strong>{lake['risk']}</strong></div>
    <div style="background:{'#ff4444' if status_text=='🔴 Опасно' else '#ffaa00' if status_text=='🟠 Внимание' else '#00cc66'}; color:white; padding:10px 26px; border-radius:50px; font-size:1.45em; font-weight:800; box-shadow:0 4px 15px rgba(0,0,0,0.25);">{status_text}</div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("pH", f"{ph:.2f}")
with col2: st.metric("Температура", f"{temp:.1f} °C")
with col3: st.metric("Мутность", f"{turb:.1f} NTU")
with col4: st.metric("Индекс SRI", f"{sri}/10", delta=round(sri - 7.0, 2))

tab1, tab2, tab3 = st.tabs(["🗺️ Карта & ИИ", "📷 Анализ по фото", "📈 История"])

with tab1:
    col_map, col_ai = st.columns([2.2, 1])
    with col_map:
        st.subheader("🗺️ Карта мониторинга")
        m = folium.Map(location=lake["coords"], zoom_start=6, tiles="CartoDB dark_matter")
        for name, info in LAKES_DB.items():
            is_target = (name == selected_name)
            color = "green" if sri > 7 else "orange" if sri > 4 else "red"
            folium.CircleMarker(location=info["coords"], radius=14 if is_target else 8,
                                color=color if is_target else "#00ffff", fill=True, fillOpacity=0.9,
                                popup=f"{name}<br>SRI: {sri}<br>{status_text}").add_to(m)
        st_folium(m, width="100%", height=520)
    with col_ai:
        st.subheader("🤖 ИИ-Анализ (Groq)")
        if st.button("🚀 Запустить диагностику", type="primary", use_container_width=True):
            with st.spinner("Анализирую данные..."):
                report = get_ai_report(selected_name, ph, temp, turb, sri, lake['risk'])
                st.success("Анализ завершён")
                st.info(report)
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=sri,
            title={"text": "Состояние водоёма", "font": {"size": 22, "color": "#e0f7ff"}},
            gauge={'axis': {'range': [0, 10]}, 'bar': {'color': "#00f2fe"},
                   'steps': [{'range': [0, 4], 'color': "#ff4444"}, {'range': [4, 7], 'color': "#ffaa00"}, {'range': [7, 10], 'color': "#00cc88"}],
                   'bgcolor': "rgba(255,255,255,0.05)"}))
        fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", font={'color': "#e0f7ff"}, margin=dict(l=20,r=20,t=30,b=10))
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("🔮 ИИ-Прогноз загрязнения и цветения")
        if st.button("🚀 Запустить прогноз на 7 дней", type="primary", use_container_width=True):
            with st.spinner("Прогнозирую..."):
                forecast = get_ai_forecast(
                    selected_name, ph, temp, turb, sri, lake['risk'],
                    st.session_state.history
                )
                st.success("Прогноз готов")
                st.info(forecast)
                if "ПРЕДУПРЕЖДЕНИЕ" in forecast or "высокий риск" in forecast.lower() or "цветение" in forecast.lower():
                    st.error("⚠️ ВЫСОКИЙ РИСК! Срочно проверьте водоём!")

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
    if st.button("📌 Сохранить текущие показания"):
        st.session_state.history.append({
            "Время": datetime.now().strftime("%H:%M"),
            "pH": ph, "Температура": temp, "Мутность": turb, "SRI": sri, "Водоём": selected_name
        })
        st.success("Показания сохранены!")
    
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Пока нет сохранённых измерений.")

st.caption("SuVision Global AI • Работает на Groq + Arduino Uno • Параметры сохраняются отдельно для каждого водоёма 💧")

# ====================== NON-STOP ПОТОК С АВТОСОХРАНЕНИЕМ ======================
if st.session_state.get("live_mode", False) and st.session_state.get('ser') and st.session_state.ser and st.session_state.ser.is_open:
    try:
        line = st.session_state.ser.readline().decode('utf-8').strip()
        if line and "ph:" in line and "temp:" in line and "turb:" in line:
            data = {}
            for item in line.split(","):
                if ":" in item:
                    k, v = item.split(":")
                    data[k.strip().lower()] = float(v.strip())
            
            new_ph = round(data.get("ph", ph), 2)
            new_temp = round(data.get("temp", temp), 1)
            new_turb = round(data.get("turb", turb), 1)
            
            # Обновляем текущие параметры
            st.session_state.lake_params[selected_name] = {
                "ph": new_ph, "temp": new_temp, "turb": new_turb
            }
            
            # === АВТОМАТИЧЕСКОЕ СОХРАНЕНИЕ В ИСТОРИЮ ПРИ ИЗМЕНЕНИИ ===
            current_values = (new_ph, new_temp, new_turb)
            last_values = st.session_state.last_live_values.get(selected_name)
            
            if last_values != current_values:  # сохраняем только если данные изменились
                st.session_state.history.append({
                    "Время": datetime.now().strftime("%H:%M"),
                    "pH": new_ph,
                    "Температура": new_temp,
                    "Мутность": new_turb,
                    "SRI": calculate_sri(new_ph, new_temp, new_turb),
                    "Водоём": selected_name
                })
                st.session_state.last_live_values[selected_name] = current_values
                st.toast("📡 Non-stop: новые данные получены и сохранены в историю!", icon="📊")
                
    except:
        pass
    
    time.sleep(5)
    st.rerun()
