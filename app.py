import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from pathlib import Path

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="SEA COLORS",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# PATHS
# =====================================================

BASE_DIR = Path(__file__).parent
LOGO_PATH = BASE_DIR / "logo_seacolors.png"

# =====================================================
# STYLE
# =====================================================

st.markdown("""
<style>

body {
    background-color: #F5F7FA;
}

[data-testid="stSidebar"] {
    background-color: white;
    border-right: 1px solid #E5E7EB;
}

.stButton > button {
    width: 100%;
    border-radius: 10px;
    border: 1px solid #D1D5DB;
    background-color: white;
    color: #102A43;
    padding: 10px;
    font-weight: 500;
}

.stButton > button:hover {
    background-color: #102A43;
    color: white;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# LANGUAGES
# =====================================================

LANGUAGES = {

    "Français": {
        "subtitle": "Prévisions marines",
        "weather_model": "Modèle météo",
        "expeditions": "Expéditions",
        "forecast": "Prévisions",
        "previous_day": "Jour précédent",
        "next_day": "Jour suivant",
        "waves": "Houle",
        "wind": "Vent",
        "visibility": "Visibilité",
        "clouds": "Nuages",
        "no_data": "Aucune donnée disponible",
        "api_error": "Erreur API météo"
    },

    "English": {
        "subtitle": "Marine Forecast",
        "weather_model": "Weather model",
        "expeditions": "Expeditions",
        "forecast": "Forecast",
        "previous_day": "Previous day",
        "next_day": "Next day",
        "waves": "Waves",
        "wind": "Wind",
        "visibility": "Visibility",
        "clouds": "Clouds",
        "no_data": "No data available",
        "api_error": "Weather API error"
    },

    "Português": {
        "subtitle": "Previsão marítima",
        "weather_model": "Modelo meteorológico",
        "expeditions": "Expedições",
        "forecast": "Previsão",
        "previous_day": "Dia anterior",
        "next_day": "Próximo dia",
        "waves": "Ondas",
        "wind": "Vento",
        "visibility": "Visibilidade",
        "clouds": "Nuvens",
        "no_data": "Nenhum dado disponível",
        "api_error": "Erro API meteorológica"
    }
}

# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), use_container_width=True)

    st.markdown("## SEA COLORS")

    selected_language = st.selectbox(
        "Language",
        ["Français", "English", "Português"]
    )

    txt = LANGUAGES[selected_language]

    weather_model = st.selectbox(
        txt["weather_model"],
        [
            "best_match",
            "gfs_seamless"
        ]
    )

# =====================================================
# HEADER
# =====================================================

col_logo, col_title = st.columns([1, 5])

with col_logo:

    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=110)

with col_title:

    st.title("SEA COLORS")
    st.caption(txt["subtitle"])

# =====================================================
# SESSION STATE
# =====================================================

if "day_offset" not in st.session_state:
    st.session_state.day_offset = 0

# =====================================================
# SCORE FUNCTION
# =====================================================

def calculate_score(waves, wind_kmh, visibility_m, clouds):

    try:

        wind_knots = wind_kmh / 1.852
        visibility_km = visibility_m / 1000

        if waves > 2:
            return 0

        if wind_knots > 22:
            return 0

        if visibility_km < 2:
            return 0

        wave_score = max(0, 100 - waves * 40)
        wind_score = max(0, 100 - wind_knots * 4)
        visibility_score = min(100, visibility_km * 10)
        cloud_score = 100 - (clouds * 0.5)

        final_score = (
            wave_score * 0.4 +
            wind_score * 0.35 +
            visibility_score * 0.15 +
            cloud_score * 0.10
        )

        return round(final_score, 1)

    except:
        return 0

# =====================================================
# WEATHER API
# =====================================================

@st.cache_data(ttl=1800)
def load_weather_data(model):

    latitude = 37.74
    longitude = -25.67

    weather_url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}"
        f"&longitude={longitude}"
        "&hourly=wind_speed_10m,visibility,cloud_cover"
        "&timezone=Atlantic/Azores"
        f"&models={model}"
    )

    marine_url = (
        "https://marine-api.open-meteo.com/v1/marine"
        f"?latitude={latitude}"
        f"&longitude={longitude}"
        "&hourly=wave_height"
        "&timezone=Atlantic/Azores"
    )

    try:

        weather_response = requests.get(weather_url, timeout=20)
        marine_response = requests.get(marine_url, timeout=20)

        weather_response.raise_for_status()
        marine_response.raise_for_status()

        weather_json = weather_response.json()
        marine_json = marine_response.json()

        weather_df = pd.DataFrame(weather_json["hourly"])
        marine_df = pd.DataFrame(marine_json["hourly"])

        df = pd.merge(weather_df, marine_df, on="time")

        df["Date"] = pd.to_datetime(df["time"])

        df.rename(columns={
            "wind_speed_10m": "Wind",
            "visibility": "Visibility",
            "cloud_cover": "Clouds",
            "wave_height": "Waves"
        }, inplace=True)

        df["Score"] = df.apply(
            lambda row: calculate_score(
                row["Waves"],
                row["Wind"],
                row["Visibility"],
                row["Clouds"]
            ),
            axis=1
        )

        return df

    except:
        return pd.DataFrame()

# =====================================================
# LOAD DATA
# =====================================================

df = load_weather_data(weather_model)

if df.empty:
    st.error(txt["api_error"])
    st.stop()

# =====================================================
# REMOVE PAST + NIGHT HOURS
# =====================================================

current_time = datetime.now()

df = df[df["Date"] >= current_time]

df = df[
    (df["Date"].dt.hour >= 8) &
    (df["Date"].dt.hour <= 20)
]

# =====================================================
# TABS
# =====================================================

tab1, tab2 = st.tabs([
    txt["expeditions"],
    txt["forecast"]
])

# =====================================================
# TAB 1
# =====================================================

with tab1:

    if df.empty:
        st.info(txt["no_data"])
        st.stop()

    current_day = df["Date"].dt.date.iloc[0]

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:

        if st.button(txt["previous_day"]):
            st.session_state.day_offset -= 1

    with col3:

        if st.button(txt["next_day"]):
            st.session_state.day_offset += 1

    selected_day = current_day + timedelta(days=st.session_state.day_offset)

    st.subheader(selected_day.strftime("%d / %m / %Y"))

    day_df = df[df["Date"].dt.date == selected_day]

    expeditions = [

        ("Morning", "08:30 - 12:30", [9,10,11,12]),
        ("Afternoon", "12:30 - 16:30", [13,14,15,16]),
        ("Evening", "16:30 - 20:30", [17,18,19,20])

    ]

    cols = st.columns(3)

    for i, (period, label, hours) in enumerate(expeditions):

        expedition_df = day_df[
            day_df["Date"].dt.hour.isin(hours)
        ]

        with cols[i]:

            st.markdown(f"### {period}")
            st.caption(f"({label})")

            if expedition_df.empty:
                st.info(txt["no_data"])
                continue

            avg_score = round(expedition_df["Score"].mean())
            avg_waves = round(expedition_df["Waves"].mean(), 1)
            avg_wind = round(expedition_df["Wind"].mean() / 1.852, 1)
            avg_visibility = round(expedition_df["Visibility"].mean() / 1000, 1)
            avg_clouds = round(expedition_df["Clouds"].mean())

            # SCORE COLORS

            if avg_score >= 90:
                color = "#15803D"

            elif avg_score >= 75:
                color = "#22C55E"

            elif avg_score >= 60:
                color = "#84CC16"

            elif avg_score >= 45:
                color = "#EAB308"

            elif avg_score >= 30:
                color = "#F97316"

            else:
                color = "#DC2626"

            with st.container(border=True):

                st.markdown(
                    f"<h1 style='color:{color};'>{avg_score}%</h1>",
                    unsafe_allow_html=True
                )

                st.write(f"{txt['waves']} : {avg_waves} m")
                st.write(f"{txt['wind']} : {avg_wind} kn")
                st.write(f"{txt['visibility']} : {avg_visibility} km")
                st.write(f"{txt['clouds']} : {avg_clouds}%")

# =====================================================
# TAB 2
# =====================================================

with tab2:

    st.subheader(txt["forecast"])

    fig = px.bar(
        df,
        x="Date",
        y="Score",
        color="Score",
        color_continuous_scale="RdYlGn"
    )

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=20, r=20, t=20, b=20),
        coloraxis_showscale=False
    )

    fig.update_xaxes(showgrid=False)

    fig.update_yaxes(
        gridcolor="#E5E7EB"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    display_df = df.copy()

    display_df["Date"] = display_df["Date"].dt.strftime(
        "%d/%m/%Y %H:%M"
    )

    display_df["Wind"] = round(
        display_df["Wind"] / 1.852,
        1
    )

    display_df["Visibility"] = round(
        display_df["Visibility"] / 1000,
        1
    )

    st.dataframe(

        display_df[[
            "Date",
            "Score",
            "Waves",
            "Wind",
            "Visibility",
            "Clouds"
        ]],

        use_container_width=True,
        hide_index=True
    )