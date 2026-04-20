import streamlit as st
import plotly.graph_objects as go
import numpy as np
import folium
from streamlit_folium import st_folium
import requests

# ====================== КОНФИГУРАЦИЯ ======================
st.set_page_config(page_title="SuVision Global AI", layout="wide")

# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
GROQ_API_KEY = "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"   # ← ВСТАВЬ СВОЙ КЛЮЧ С GROQ СЮДА
# Получить ключ: https://console.groq.com/keys
# ====================== БАЗА ДАННЫХ ======================

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
    "Озеро Тенгиз": {"coords": [50.4000, 68.9000], "type": "Соленое", "risk": "Гидрология"},
    "Капчагайское вдхр.": {"coords": [43.7844, 77.0653], "type": "Рекреационный", "risk": "Рекреационная нагрузка"},
    "Первомайские пруды": {"coords": [43.3711, 76.9455], "type": "Городской", "risk": "Бытовые стоки"}
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

# ====================== РАСЧЁТ SRI ======================
def calculate_sri(p, t, tr):
    return max(round(10 - (abs(p-7)*1.5 + (t/10)*0.8 + (tr/20)*1.2), 2), 0.0)

sri = calculate_sri(ph, temp, turb)

# ====================== ИИ-АНАЛИЗ НА GROQ ======================
def get_ai_report(lake_name, ph, temp, turb, sri, risk):
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    prompt = f"""Ты опытный эколог-гидролог. Кратко проанализируй состояние водоёма.

Объект: {lake_name}
Параметры: pH = {ph}, температура = {temp}°C, мутность = {turb} NTU
Индекс SRI: {sri}/10
Основной риск: {risk}

Ответь **ровно двумя предложениями** на русском языке:
1. Оценка текущего состояния.
2. Главный вывод или рекомендация."""

    payload = {
        "model": "llama-3.3-70b-versatile",   # Можно поменять на "llama-3.1-8b-instant" — быстрее
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 180,
        "temperature": 0.65
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=12)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        else:
            return f"Ошибка Groq ({response.status_code}). Проверьте API-ключ или лимиты."
            
    except requests.exceptions.Timeout:
        return "⏳ Время ожидания истекло. Попробуйте позже."
    except Exception as e:
        return f"Ошибка подключения к ИИ: {str(e)}"

# ====================== ОСНОВНОЙ ИНТЕРФЕЙС ======================
st.title("🌊 SuVision: Глобальный мониторинг водоёмов")

st.markdown(f"**Объект:** `{selected_name}` | **Основной риск:** {lake['risk']}")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🗺️ Карта мониторинга")
    m = folium.Map(location=lake["coords"], zoom_start=7, tiles="CartoDB dark_matter")
    
    for name, info in LAKES_DB.items():
        is_target = (name == selected_name)
        color = "green" if sri > 7 else "orange" if sri > 4 else "red"
        
        folium.CircleMarker(
            location=info["coords"],
            radius=14 if is_target else 7,
            color=color if is_target else "cyan",
            fill=True,
            fillOpacity=0.8,
            popup=f"{name}<br>SRI: {sri}",
            tooltip=name
        ).add_to(m)
    
    st_folium(m, width="100%", height=480, key=f"map_{selected_name}")

with col2:
    st.subheader("🤖 ИИ-Анализ (Groq)")
    
    if st.button("🚀 Запустить диагностику", type="primary"):
        with st.spinner("Llama-3.3 анализирует данные..."):
            report = get_ai_report(selected_name, ph, temp, turb, sri, lake['risk'])
            st.success("Анализ завершён")
            st.write(report)
    
    st.divider()
    
    st.metric("Индекс SRI", f"{sri}/10", delta=round(sri - 7, 2))
    
    # Красивый gauge
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=sri,
        title={"text": "Состояние водоёма"},
        gauge={
            'axis': {'range': [0, 10]},
            'bar': {'color': "#00f2fe"},
            'steps': [
                {'range': [0, 4], 'color': "#440000"},
                {'range': [4, 7], 'color': "#663300"},
                {'range': [7, 10], 'color': "#003311"}
            ]
        }
    ))
    fig.update_layout(height=220, margin=dict(l=10, r=10, t=20, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"})
    st.plotly_chart(fig, use_container_width=True)

# Подвал
st.caption("SuVision Global AI • Работает на Groq (Llama-3.3-70B) • Бесплатный tier")
