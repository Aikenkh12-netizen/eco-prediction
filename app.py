import streamlit as st
import plotly.graph_objects as go
import numpy as np
import folium
from streamlit_folium import st_folium

# Настройка страницы (layout="wide" лучше подходит для карты)
st.set_page_config(page_title="SuVision 🌊", layout="wide")

# --- Заголовок ---
st.title("SuVision 🌊 Экологический прогноз водоёма")

# --- 1. Ввод параметров (ПЕРЕНЕСЕНО В SIDEBAR) ---
st.sidebar.header("🔹 Ввод параметров воды")
ph = st.sidebar.slider("💧 pH воды", 0.0, 14.0, 7.0, 0.1)
temperature = st.sidebar.slider("🌡️ Температура воды (°C)", 0.0, 40.0, 20.0, 0.5)
turbidity = st.sidebar.slider("⚪ Мутность воды (NTU)", 0.0, 100.0, 5.0, 1.0) 

# --- 2. Модели (БЕЗ ИЗМЕНЕНИЙ) ---
def bloom_probability(ph_val, temp_val, turb_val):
    prob = (
        (0.4 * (7 - np.abs(ph_val - 7))) +
        (0.3 * (temp_val / 40 * 10)) +
        (0.3 * (turb_val / 10))
    ) * 10
    return np.clip(prob, 0, 100)

def pollution_probability(ph_val, temp_val, turb_val):
    prob = (
        (0.3 * np.abs(ph_val - 7)) +
        (0.3 * (temp_val / 40 * 10)) +
        (0.4 * (turb_val / 10))
    ) * 10
    return np.clip(prob, 0, 100)

def sri_index(ph_val, temp_val, turb_val):
    penalty_ph = abs(ph_val - 7)
    penalty_temp = temp_val / 10
    penalty_turb = turb_val / 20
    sri = 10 - (penalty_ph + penalty_temp + penalty_turb)
    return max(round(sri, 1), 0.0)

# --- расчёты ---
bloom_prob = bloom_probability(ph, temperature, turbidity)
pollution_prob = pollution_probability(ph, temperature, turbidity)
sri = sri_index(ph, temperature, turbidity)

# --- НОВЫЙ БЛОК: КАРТА (Интерактивный мониторинг) ---
st.header("📍 Карта мониторинга")
col_map, col_info = st.columns([2, 1])

with col_map:
    # Создаем карту (центр - Алматы)
    m = folium.Map(location=[43.2389, 76.8897], zoom_start=12)
    # Цвет точки зависит от индекса SRI
    marker_color = "green" if sri > 7.0 else "orange" if sri >= 4.0 else "red"
    folium.Marker(
        [43.2389, 76.8897], 
        popup=f"SRI: {sri}",
        tooltip="Центральная станция",
        icon=folium.Icon(color=marker_color, icon='info-sign')
    ).add_to(m)
    st_folium(m, width=700, height=400)

with col_info:
    st.write("### Статус станции")
    st.write(f"**Координаты:** 43.2389, 76.8897")
    st.write(f"**Текущее состояние:** {'Стабильно' if sri > 7.0 else 'Требует внимания' if sri >= 4.0 else 'Критично'}")
    st.info("Карта позволяет отслеживать экологическую ситуацию в конкретных точках забора воды.")

# --- 3. Прогнозы (БЕЗ ИЗМЕНЕНИЙ) ---
st.header("📊 Прогнозы")
st.success(f"Вероятность цветения: {bloom_prob:.1f}%")
st.success(f"Вероятность загрязнения: {pollution_prob:.1f}%")
st.info(f"Индекс устойчивости (SRI): {sri:.1f}")

# --- 4. Рекомендации (БЕЗ ИЗМЕНЕНИЙ) ---
def give_advice(ph_val, temp_val, turb_val, bloom_prob, pollution_prob):
    advice = []
    if ph_val < 6.5:
        advice.append("🔴 Вода кислая — риск коррозии труб, вымывание металлов, угнетение рыб. Совет: провести известкование, использовать нейтрализующие фильтры.")
    elif ph_val > 8.5:
        advice.append("🔴 Вода щелочная — возможны сточные воды, избыток минералов. Совет: контроль источников, обратный осмос.")
    else:
        advice.append("✅ pH в норме. Экосистема стабильна.")
    if temp_val > 25:
        advice.append("⚠️ Высокая температура — ускоренный рост водорослей, риск цветения. Совет: аэрация, биофильтрация.")
    elif temp_val < 10:
        advice.append("⚠️ Низкая температура — замедление биопроцессов, снижение самоочищения. Совет: мониторинг.")
    else:
        advice.append("✅ Температура в норме.")
    if turb_val > 5:
        advice.append("⚠️ Мутность повышена — загрязнение взвешенными частицами. Совет: песчаная/угольная фильтрация, контроль источников.")
    elif turb_val <= 1:
        advice.append("✅ Мутность низкая — вода прозрачная и безопасная.")
    else:
        advice.append("⚠️ Мутность умеренная — допустима, но требует контроля.")
    if bloom_prob >= 50:
        advice.append("⚠️ Цветение вероятно — примите меры по снижению температуры и мутности.")
    if pollution_prob >= 50:
        advice.append("⚠️ Загрязнение вероятно — проверьте сточные воды и проведите очистку.")
    return advice

st.header("💡 Рекомендации")
for tip in give_advice(ph, temperature, turbidity, bloom_prob, pollution_prob):
    if "✅" in tip: st.success(tip)
    elif "⚠️" in tip: st.warning(tip)
    else: st.error(tip)

# --- 5. Авторская формула (БЕЗ ИЗМЕНЕНИЙ) ---
st.header("📐 Наша авторская формула SRI")
st.markdown(r"""
$$ SRI = 10 - (|pH - 7| + \frac{T_{water}}{10} + \frac{Tur}{20}) $$
""")

# --- 6. Подробный разбор (БЕЗ ИЗМЕНЕНИЙ) ---
st.header("🔎 Подробный разбор состояния водоёма")
if sri > 7.0:
    st.success(f"SRI = {sri} → Норма. Экосистема устойчива, вода в хорошем состоянии.")
elif 4.0 <= sri <= 7.0:
    st.warning(f"SRI = {sri} → Риск. Есть отклонения, возможны проблемы. Требуется мониторинг.")
else:
    st.error(f"SRI = {sri} → Критическое состояние. Экосистема под угрозой, параметры значительно отклонены от нормы.")

# --- 7. Графики (БЕЗ ИЗМЕНЕНИЙ) ---
st.header("📈 Визуализация данных")
water_quality_index = 100 - ((bloom_prob + pollution_prob) / 2)
fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=water_quality_index,
    title={'text': "Индекс качества воды"},
    gauge={'axis': {'range': [0, 100]},
           'bar': {'color': "green" if water_quality_index > 70 else "orange" if water_quality_index > 40 else "red"},
           'steps': [{'range': [0, 40], 'color': "red"},
                     {'range': [40, 70], 'color': "orange"},
                     {'range': [70, 100], 'color': "green"}]}
))
st.plotly_chart(fig_gauge, use_container_width=True)

if "history" not in st.session_state: st.session_state["history"] = []
st.session_state["history"].append({"pH": ph, "T": temperature, "Tur": turbidity, "SRI": sri, "Quality": water_quality_index})

# --- 8. Контакты (БЕЗ ИЗМЕНЕНИЙ) ---
st.header("📩 Контакты")
st.markdown("""
**SuVision Project** 📞 Телефон: +7 (747) 193-93-37  
✉️ Email: aikenkhairulla32@gmail.com  
""")
