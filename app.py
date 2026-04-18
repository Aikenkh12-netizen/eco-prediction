import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="SuVision 🌊", layout="centered")

# --- Заголовок ---
st.title("SuVision 🌊 Экологический прогноз водоёма")

# --- 1. Ввод параметров ---
st.header("🔹 Ввод параметров воды")
ph = st.slider("💧 pH воды", 0.0, 14.0, 7.0, 0.1)
temperature = st.slider("🌡️ Температура воды (°C)", 0.0, 40.0, 20.0, 0.5)
turbidity = st.slider("⚪ Мутность воды (NTU)", 0.0, 100.0, 5.0, 1.0) 

# --- 2. Модели ---
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

# --- Упрощенная формула SRI для 8 класса ---
def sri_index(ph_val, temp_val, turb_val):
    # Штрафы: за отклонение pH, за высокую температуру и за мутность
    penalty_ph = abs(ph_val - 7)
    penalty_temp = temp_val / 10
    penalty_turb = turb_val / 20
    
    sri = 10 - (penalty_ph + penalty_temp + penalty_turb)
    return max(round(sri, 1), 0.0)

# --- расчёты ---
bloom_prob = bloom_probability(ph, temperature, turbidity)
pollution_prob = pollution_probability(ph, temperature, turbidity)
sri = sri_index(ph, temperature, turbidity)

# --- 3. Прогнозы ---
st.header("📊 Прогнозы")
st.success(f"Вероятность цветения: {bloom_prob:.1f}%")
st.success(f"Вероятность загрязнения: {pollution_prob:.1f}%")
st.info(f"Индекс устойчивости (SRI): {sri:.1f}")

# --- 4. Рекомендации ---
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
    if "✅" in tip:
        st.success(tip)
    elif "⚠️" in tip:
        st.warning(tip)
    else:
        st.error(tip)

# --- 5. Авторская формула ---
st.header("📐 Наша авторская формула SRI")
st.markdown(r"""
Мы используем нашу авторскую систему оценки, адаптированную для экологического мониторинга:

$$ SRI = 10 - (|pH - 7| + \frac{T_{water}}{10} + \frac{Tur}{20}) $$

Эта модель оценивает "запас прочности" водоема, вычитая штрафные баллы за каждое отклонение от идеальных условий.
""")

# --- 6. Подробный разбор состояния водоёма ---
st.header("🔎 Подробный разбор состояния водоёма")
if sri > 7.0:
    st.success(f"SRI = {sri} → Норма. Экосистема устойчива, вода в хорошем состоянии.")
elif 4.0 <= sri <= 7.0:
    st.warning(f"SRI = {sri} → Риск. Есть отклонения, возможны проблемы. Требуется мониторинг.")
else:
    st.error(f"SRI = {sri} → Критическое состояние. Экосистема под угрозой, параметры значительно отклонены от нормы.")

# --- 7. Графики ---
st.header("📈 Визуализация данных")

water_quality_index = 100 - ((bloom_prob + pollution_prob) / 2)
fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=water_quality_index,
    title={'text': "Индекс качества воды"},
    gauge={'axis': {'range': [0, 100]},
           'bar': {'color': "green" if water_quality_index > 70 else "orange" if water_quality_index > 40 else "red"},
           'steps': [
               {'range': [0, 40], 'color': "red"},
               {'range': [40, 70], 'color': "orange"},
               {'range': [70, 100], 'color': "green"}]}
))
st.plotly_chart(fig_gauge, use_container_width=True)

fig_bar = go.Figure(data=[
    go.Bar(name="pH", x=["pH"], y=[ph], marker_color="blue"),
    go.Bar(name="Температура", x=["Температура"], y=[temperature], marker_color="orange"),
    go.Bar(name="Мутность", x=["Мутность"], y=[turbidity], marker_color="gray"),
])
fig_bar.update_layout(title="Текущие параметры воды", yaxis_title="Значение", barmode="group")
st.plotly_chart(fig_bar, use_container_width=True)

if "history" not in st.session_state:
    st.session_state["history"] = []

st.session_state["history"].append({
    "pH": ph,
    "Температура": temperature,
    "Мутность": turbidity,
    "Цветение": bloom_prob,
    "Загрязнение": pollution_prob,
    "Индекс качества": water_quality_index,
    "SRI": sri
})
history_data = st.session_state["history"]

fig_history = go.Figure()
fig_history.add_trace(go.Scatter(y=[h["Цветение"] for h in history_data], mode="lines+markers", name="Цветение (%)", line=dict(color="red")))
fig_history.add_trace(go.Scatter(y=[h["Загрязнение"] for h in history_data], mode="lines+markers", name="Загрязнение (%)", line=dict(color="brown")))
fig_history.add_trace(go.Scatter(y=[h["Индекс качества"] for h in history_data], mode="lines+markers", name="Качество воды", line=dict(color="green")))
fig_history.add_trace(go.Scatter(y=[h["SRI"] for h in history_data], mode="lines+markers", name="SRI", line=dict(color="blue")))

fig_history.update_layout(title="История изменений прогнозов", xaxis_title="Изменения (шаги)", yaxis_title="Значение (%)")
st.plotly_chart(fig_history, use_container_width=True)

# --- 8. Контакты ---
st.header("📩 Контакты")
st.markdown("""
**SuVision Project** 📞 Телефон: +7 (747) 193-93-37  
✉️ Email: aikenkhairulla32@gmail.com  
""")
