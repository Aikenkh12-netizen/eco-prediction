import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.title("SuVision 🌊 ")

# --- Ползунки ---
ph = st.slider("pH воды", 0.0, 14.0, 7.0, 0.1)
temperature = st.slider("Температура воды (°C)", 0.0, 40.0, 20.0, 0.5)
turbidity = st.slider("Мутность воды (NTU)", 0.0, 10.0, 5.0, 0.1)

# --- Модели ---
def bloom_probability(ph_val, temp_val, turb_val):
    prob = (
        (0.4 * (7 - np.abs(ph_val - 7))) +
        (0.3 * (temp_val / 40 * 10)) +
        (0.3 * turb_val)
    ) * 10
    return np.clip(prob, 0, 100)

def pollution_probability(ph_val, temp_val, turb_val):
    prob = (
        (0.3 * np.abs(ph_val - 7)) +
        (0.3 * (temp_val / 40 * 10)) +
        (0.4 * turb_val)
    ) * 10
    return np.clip(prob, 0, 100)

bloom_prob = bloom_probability(ph, temperature, turbidity)
pollution_prob = pollution_probability(ph, temperature, turbidity)

# --- Прогнозы ---
if bloom_prob >= 50:
    st.markdown(f"<h3 style='color:red'>Цветение микроводорослей вероятно — {bloom_prob:.1f}%</h3>", unsafe_allow_html=True)
else:
    st.markdown(f"<h3 style='color:green'>Цветение микроводорослей маловероятно — {bloom_prob:.1f}%</h3>", unsafe_allow_html=True)

if pollution_prob >= 50:
    st.markdown(f"<h3 style='color:red'>Загрязнение водоёма вероятно — {pollution_prob:.1f}%</h3>", unsafe_allow_html=True)
else:
    st.markdown(f"<h3 style='color:green'>Загрязнение водоёма маловероятно — {pollution_prob:.1f}%</h3>", unsafe_allow_html=True)

# --- (2) Индикатор качества воды ---
water_quality_index = 100 - ((bloom_prob + pollution_prob) / 2)
st.subheader("Индекс качества воды")
if water_quality_index > 70:
    quality_color = "green"
elif water_quality_index > 40:
    quality_color = "orange"
else:
    quality_color = "red"
st.markdown(f"<h3 style='color:{quality_color}'>Качество воды: {water_quality_index:.1f}/100</h3>", unsafe_allow_html=True)

# --- (6) Gauge Chart ---
fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=water_quality_index,
    title={'text': "Индекс качества воды"},
    gauge={'axis': {'range': [0, 100]},
           'bar': {'color': quality_color},
           'steps': [
               {'range': [0, 40], 'color': "red"},
               {'range': [40, 70], 'color': "orange"},
               {'range': [70, 100], 'color': "green"}]}
))
st.plotly_chart(fig_gauge, width="stretch")

# --- Bar Chart параметров ---
fig_bar = go.Figure(data=[
    go.Bar(name="pH", x=["pH"], y=[ph], marker_color="blue"),
    go.Bar(name="Температура", x=["Температура"], y=[temperature], marker_color="orange"),
    go.Bar(name="Мутность", x=["Мутность"], y=[turbidity], marker_color="gray"),
])
fig_bar.update_layout(title="Текущие параметры воды", yaxis_title="Значение", width=800, height=500, barmode="group")
st.plotly_chart(fig_bar, width="stretch")

# --- (3) История изменений ---
if "history" not in st.session_state:
    st.session_state["history"] = []

st.session_state["history"].append({
    "pH": ph,
    "Температура": temperature,
    "Мутность": turbidity,
    "Цветение": bloom_prob,
    "Загрязнение": pollution_prob,
    "Индекс качества": water_quality_index
})

history_data = st.session_state["history"]

fig_history = go.Figure()
fig_history.add_trace(go.Scatter(y=[h["Цветение"] for h in history_data], mode="lines+markers", name="Цветение (%)", line=dict(color="red")))
fig_history.add_trace(go.Scatter(y=[h["Загрязнение"] for h in history_data], mode="lines+markers", name="Загрязнение (%)", line=dict(color="brown")))
fig_history.add_trace(go.Scatter(y=[h["Индекс качества"] for h in history_data], mode="lines+markers", name="Качество воды", line=dict(color="green")))

fig_history.update_layout(title="История изменений прогнозов", xaxis_title="Изменения (шаги)", yaxis_title="Значение (%)", width=800, height=500)
st.plotly_chart(fig_history, width="stretch")


