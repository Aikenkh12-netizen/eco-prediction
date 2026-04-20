import streamlit as st
import plotly.graph_objects as go
import numpy as np
import folium
from streamlit_folium import st_folium
import requests

# --- КОНФИГУРАЦИЯ ---
# Вставь сюда свой токен Hugging Face (начинается на hf_...)
HF_TOKEN = "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"
API_URL = "https://api-inference.huggingface.co/models/Mistralai/Mistral-7B-Instruct-v0.3"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

st.set_page_config(page_title="SuVision Global AI", layout="wide")

# --- БАЗА ДАННЫХ ---
LAKES_DB = {
    "Каспийское море": {"coords": [43.6500, 51.1500], "type": "Морской", "risk": "Нефтяные загрязнения"},
    "Озеро Балхаш": {"coords": [46.5400, 74.8700], "type": "Бессточный", "risk": "Тяжелые металлы"},
    "БАО (Алматы)": {"coords": [43.0506, 76.9849], "type": "Высокогорный", "risk": "Бактериальное загрязнение"},
    "Озеро Алаколь": {"coords": [46.1200, 81.7400], "type": "Соленое", "risk": "Антропогенная нагрузка"},
    "Боровое": {"coords": [53.0800, 70.3000], "type": "Пресноводный", "risk": "Эвтрофикация"},
    "Река Иртыш": {"coords": [49.9500, 82.6100], "type": "Речной", "risk": "Промышленные стоки"},
    "Озеро Маркаколь": {"coords": [48.5100, 85.8000], "type": "Заповедный", "risk": "Изменение климата"},
    "Озеро Сайран": {"coords": [43.2389, 76.8897], "type": "Городской", "risk": "Ливневые стоки"},
    "Шардаринское вдхр.": {"coords": [41.2500, 67.9800], "type": "Ирригационный", "risk": "Пестициды"},
    "Озеро Тенгиз": {"coords": [50.4000, 68.9000], "type": "Соленое", "risk": "Гидрология"}
}

# --- БОКОВАЯ ПАНЕЛЬ ---
with st.sidebar:
    st.title("🚀 SuVision Core")
    selected_name = st.selectbox("🎯 Станция мониторинга", list(LAKES_DB.keys()))
    lake = LAKES_DB[selected_name]
    
    st.divider()
    ph = st.slider("pH", 0.0, 14.0, 7.2, 0.1)
    temp = st.slider("Температура (°C)", 0.0, 40.0, 18.0, 0.5)
    turb = st.slider("Мутность (NTU)", 0.0, 100.0, 4.0, 1.0)

def calculate_sri(p, t, tr):
    return max(round(10 - (abs(p-7)*1.5 + (t/10)*0.8 + (tr/20)*1.2), 2), 0.0)

sri = calculate_sri(ph, temp, turb)

# --- ФУНКЦИЯ ИИ (Hugging Face) ---
def get_ai_report(lake_name, ph, temp, turb, sri, risk):
    # Промпт оптимизирован под Mistral-7B
    prompt = f"<s>[INST] Ты эколог. Кратко проанализируй: {lake_name}, pH {ph}, Temp {temp}C, Мутность {turb}. SRI {sri}/10. Риск: {risk}. Дай 2 предложения на русском. [/INST]"
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 100, "temperature": 0.5}}
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            full_text = result[0]['generated_text']
            return full_text.split("[/INST]")[-1].strip()
        else:
            return f"Ошибка API: {response.status_code}. Проверьте токен."
    except Exception as e:
        return "ИИ временно не отвечает. Проверьте подключение."

# --- ИНТЕРФЕЙС ---
st.title("🌊 SuVision: Глобальный мониторинг")
st.markdown(f"**Объект:** {selected_name} | **Риск:** {lake['risk']}")

c1, c2 = st.columns([2, 1])

with c1:
    m = folium.Map(location=lake["coords"], zoom_start=7, tiles="CartoDB dark_matter")
    for name, info in LAKES_DB.items():
        is_target = (name == selected_name)
        folium.CircleMarker(
            location=info["coords"],
            radius=12 if is_target else 6,
            color="cyan" if not is_target else ("green" if sri > 7 else "orange" if sri > 4 else "red"),
            fill=True
        ).add_to(m)
    st_folium(m, width="100%", height=450, key=f"map_{selected_name}")

with c2:
    st.subheader("🤖 ИИ-Анализ")
    if st.button("Запустить диагностику"):
        with st.spinner("Mistral-7B анализирует данные..."):
            report = get_ai_report(selected_name, ph, temp, turb, sri, lake['risk'])
            st.write(report)
    
    st.divider()
    st.metric("Индекс SRI", f"{sri}/10", delta=round(sri-7, 2))
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=sri,
        gauge={'axis': {'range': [0, 10]}, 'bar': {'color': "#00f2fe"},
               'steps': [{'range': [0, 4], 'color': "#330000"}, {'range': [7, 10], 'color': "#003311"}]}
    ))
    fig.update_layout(height=200, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="rgba(0,0,0,0)", font={'color':"white"})
    st.plotly_chart(fig, use_container_width=True)

st.caption("SuVision Global | Open Source AI Model: Mistral-7B-v0.3")
