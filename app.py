import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
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
# PATHS & LOGO DETECTION
# =====================================================

BASE_DIR = Path(__file__).parent

# Mise à jour avec le nom de fichier exact
LOGO_PATH = BASE_DIR / "logo_seacolors.png"

# =====================================================
# STYLE PREMIUM MINIMALISTE (CSS)
# =====================================================

st.markdown("""
<style>
/* Arrière-plan global doux */
body, .stApp {
    background-color: #F8FAFC !important;
    font-family: 'Inter', 'Helvetica Neue', sans-serif !important;
}

/* Sidebar épurée */
[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid #E2E8F0;
}

/* Boutons stylisés et sobres */
.stButton > button {
    width: 100%;
    border-radius: 8px;
    border: 1px solid #E2E8F0;
    background-color: #FFFFFF;
    color: #0F172A;
    padding: 10px;
    font-weight: 500;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    background-color: #0F172A;
    color: #FFFFFF;
    border-color: #0F172A;
}

/* Style des cartes Minimalistes */
.premium-card {
    background-color: #FFFFFF;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    border: 1px solid #F1F5F9;
    transition: transform 0.2s ease;
    margin-bottom: 15px;
}
.premium-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04);
}

/* Typographie stricte */
h1, h2, h3, h4 {
    color: #0F172A !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em;
}
p, span {
    color: #475569;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# LANGUAGES (Stricte et Professionnel)
# =====================================================

LANGUAGES = {
    "Français": {
        "subtitle": "Prévisions marines • Zone 35km",
        "weather_model": "Modèle météo",
        "expeditions": "Expéditions",
        "forecast": "Prévisions Détaillées",
        "previous_day": "Campagne précédente",
        "next_day": "Campagne suivante",
        "waves": "Houle",
        "wind": "Vent",
        "visibility": "Visibilité",
        "clouds": "Nuages",
        "no_data": "Aucune donnée disponible",
        "api_error": "Erreur de synchronisation avec l'API météo."
    },
    "English": {
        "subtitle": "Marine Forecast • 35km Radius",
        "weather_model": "Weather model",
        "expeditions": "Expeditions",
        "forecast": "Detailed Forecast",
        "previous_day": "Previous day",
        "next_day": "Next day",
        "waves": "Waves",
        "wind": "Wind",
        "visibility": "Visibility",
        "clouds": "Clouds",
        "no_data": "No data available",
        "api_error": "Weather API synchronization error."
    },
    "Português": {
        "subtitle": "Previsão marítima • Raio de 35km",
        "weather_model": "Modelo meteorológico",
        "expeditions": "Expedições",
        "forecast": "Previsão Detalhada",
        "previous_day": "Dia anterior",
        "next_day": "Próximo dia",
        "waves": "Ondas",
        "wind": "Vento",
        "visibility": "Visibilidade",
        "clouds": "Nuvens",
        "no_data": "Nenhum dado disponible",
        "api_error": "Erro de sincronização com a API."
    }
}

# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), use_container_width=True)
    else:
        st.markdown("<h2 style='text-align:center; margin-top:20px;'>SEA COLORS</h2>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    selected_language = st.selectbox("Language", ["Français", "English", "Português"])
    txt = LANGUAGES[selected_language]

    st.markdown("<br>", unsafe_allow_html=True)
    weather_model = st.selectbox(
        txt['weather_model'],
        ["best_match", "gfs_seamless", "ecmwf_ifs04"]
    )

# =====================================================
# HEADER
# =====================================================

if LOGO_PATH.exists():
    col_logo, col_title = st.columns([1, 8])
    with col_logo:
        st.image(str(LOGO_PATH), width=90)
    with col_title:
        st.markdown("<h1 style='margin-bottom:-15px;'>SEA COLORS</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 1.1rem; color: #64748B; font-weight: 500;'>{txt['subtitle']}</p>", unsafe_allow_html=True)
else:
    st.markdown("<h1 style='margin-bottom:-5px;'>SEA COLORS</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size: 1.1rem; color: #64748B; font-weight: 500;'>{txt['subtitle']}</p>", unsafe_allow_html=True)

st.markdown("<hr style='border: 1px solid #E2E8F0; margin-top: 5px; margin-bottom: 25px;'>", unsafe_allow_html=True)

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

        if waves > 2.5: return 0.0
        if wind_knots > 25.0: return 0.0
        if visibility_km < 1.5: return 0.0

        wave_score = 100 if waves <= 0.5 else max(0, 100 - ((waves - 0.5) * 30))
        wind_score = 100 if wind_knots <= 5 else max(0, 100 - ((wind_knots - 5) * 3))
        visibility_score = min(100, visibility_km * 20)
        cloud_score = 100 - (clouds * 0.3)

        final_score = (wave_score * 0.4 + wind_score * 0.35 + visibility_score * 0.15 + cloud_score * 0.10)
        return round(final_score, 1)
    except:
        return 0.0

# =====================================================
# WEATHER API
# =====================================================

@st.cache_data(ttl=1800)
def load_weather_data(model):
    latitudes = "37.74,38.055,37.425,37.74,37.74"
    longitudes = "-25.67,-25.67,-25.67,-25.273,-26.067"

    weather_url = (f"https://api.open-meteo.com/v1/forecast?latitude={latitudes}&longitude={longitudes}&hourly=wind_speed_10m,visibility,cloud_cover&timezone=Atlantic/Azores&models={model}")
    marine_url = (f"https://marine-api.open-meteo.com/v1/marine?latitude={latitudes}&longitude={longitudes}&hourly=wave_height&timezone=Atlantic/Azores")

    try:
        weather_response = requests.get(weather_url, timeout=20).json()
        marine_response = requests.get(marine_url, timeout=20).json()

        if isinstance(weather_response, dict): weather_response = [weather_response]
        if isinstance(marine_response, dict): marine_response = [marine_response]

        weather_dfs = [pd.DataFrame(loc["hourly"]) for loc in weather_response]
        weather_df = pd.concat(weather_dfs).groupby("time").mean().reset_index()

        marine_dfs = [pd.DataFrame(loc["hourly"]) for loc in marine_response if "hourly" in loc]
        if not marine_dfs: 
            marine_df = pd.DataFrame({'time': weather_df['time'], 'wave_height': 0.5})
        else:
            marine_df = pd.concat(marine_dfs).groupby("time").mean().reset_index()

        df = pd.merge(weather_df, marine_df, on="time")
        df["Date"] = pd.to_datetime(df["time"])

        df.rename(columns={"wind_speed_10m": "Wind", "visibility": "Visibility", "cloud_cover": "Clouds", "wave_height": "Waves"}, inplace=True)
        df["Score"] = df.apply(lambda row: calculate_score(row["Waves"], row["Wind"], row["Visibility"], row["Clouds"]), axis=1)
        return df
    except Exception as e:
        return pd.DataFrame()

# =====================================================
# LOAD DATA & CLEANUP
# =====================================================

df = load_weather_data(weather_model)

if df.empty:
    st.error(txt["api_error"])
    st.stop()

current_time = datetime.now()
df = df[df["Date"] >= current_time]
df = df[(df["Date"].dt.hour >= 8) & (df["Date"].dt.hour <= 20)]

# =====================================================
# TABS
# =====================================================

tab1, tab2 = st.tabs([txt["expeditions"], txt["forecast"]])

# =====================================================
# TAB 1 : EXPEDITIONS
# =====================================================

with tab1:
    if df.empty:
        st.info(txt["no_data"])
        st.stop()

    current_day = df["Date"].dt.date.iloc[0]
    col1, col2, col3 = st.columns([1, 3, 1])

    with col1:
        if st.button(txt["previous_day"], disabled=(st.session_state.day_offset <= 0)):
            st.session_state.day_offset -= 1
            st.rerun()

    with col2:
        selected_day = current_day + timedelta(days=st.session_state.day_offset)
        st.markdown(f"<h2 style='text-align:center; color:#0F172A; margin-top:0;'>{selected_day.strftime('%d / %m / %Y')}</h2>", unsafe_allow_html=True)

    with col3:
        if st.button(txt["next_day"], disabled=(st.session_state.day_offset >= 5)):
            st.session_state.day_offset += 1
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    day_df = df[df["Date"].dt.date == selected_day]

    expeditions = [
        ("Matin", "08h30 - 12h30", [9, 10, 11, 12]),
        ("Après-midi", "12h30 - 16h30", [13, 14, 15, 16]),
        ("Soirée", "16h30 - 20h30", [17, 18, 19, 20])
    ]

    cols = st.columns(3)

    for i, (period, label, hours) in enumerate(expeditions):
        expedition_df = day_df[day_df["Date"].dt.hour.isin(hours)]

        with cols[i]:
            if expedition_df.empty:
                st.info(txt["no_data"])
                continue

            avg_score = round(expedition_df["Score"].mean())
            avg_waves = round(expedition_df["Waves"].mean(), 1)
            avg_wind = round(expedition_df["Wind"].mean() / 1.852, 1)
            avg_visibility = round(expedition_df["Visibility"].mean() / 1000, 1)
            avg_clouds = round(expedition_df["Clouds"].mean())

            if avg_score >= 90: color, bg_color = "#166534", "#DCFCE7" 
            elif avg_score >= 75: color, bg_color = "#15803D", "#DCFCE7" 
            elif avg_score >= 60: color, bg_color = "#65A30D", "#ECFCCB" 
            elif avg_score >= 45: color, bg_color = "#D97706", "#FEF3C7" 
            elif avg_score >= 30: color, bg_color = "#EA580C", "#FFEDD5" 
            else: color, bg_color = "#DC2626", "#FEE2E2"                 

            st.markdown(f"""
            <div class="premium-card" style="border-top: 4px solid {color};">
                <div style="text-align:center; margin-bottom:15px;">
                    <h3 style="margin:0; font-size:1.2rem; color:#0F172A;">{period}</h3>
                    <p style="margin:0; font-size:0.85rem; color:#64748B;">{label}</p>
                </div>
                <div style="background-color:{bg_color}; border-radius:8px; padding:15px; text-align:center; margin-bottom:20px;">
                    <h1 style="margin:0; font-size:2.8rem; color:{color};">{avg_score}%</h1>
                    <span style="color:{color}; font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing: 0.05em;">Faisabilité</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:10px; padding-bottom:10px; border-bottom:1px solid #F1F5F9;">
                    <span style="color:#64748B; font-size:0.9rem;">{txt['waves']}</span>
                    <strong style="color:#0F172A; font-size:0.9rem;">{avg_waves} m</strong>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:10px; padding-bottom:10px; border-bottom:1px solid #F1F5F9;">
                    <span style="color:#64748B; font-size:0.9rem;">{txt['wind']}</span>
                    <strong style="color:#0F172A; font-size:0.9rem;">{avg_wind} kn</strong>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:10px; padding-bottom:10px; border-bottom:1px solid #F1F5F9;">
                    <span style="color:#64748B; font-size:0.9rem;">{txt['visibility']}</span>
                    <strong style="color:#0F172A; font-size:0.9rem;">{avg_visibility} km</strong>
                </div>
                <div style="display:flex; justify-content:space-between;">
                    <span style="color:#64748B; font-size:0.9rem;">{txt['clouds']}</span>
                    <strong style="color:#0F172A; font-size:0.9rem;">{avg_clouds}%</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

# =====================================================
# TAB 2 : FORECAST (DESIGN PREMIUM MINIMALISTE)
# =====================================================

with tab2:
    st.markdown(f"<h3 style='margin-top:10px; color:#0F172A;'>{txt['forecast']}</h3>", unsafe_allow_html=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Date"],
        y=df["Score"],
        mode="lines+markers",
        name="Score",
        line=dict(shape="spline", width=2, color="#CBD5E1"), 
        fill="tozeroy",
        fillcolor="rgba(241, 245, 249, 0.4)", 
        marker=dict(
            size=10,
            color=df["Score"],
            colorscale="RdYlGn",
            cmin=0,
            cmax=100,
            line=dict(width=1.5, color="white") 
        )
    ))

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=20, t=30, b=20),
        yaxis=dict(
            showgrid=True, 
            gridcolor="#F1F5F9", 
            zeroline=False, 
            range=[-5, 105],
            title="Score (%)",
            title_font=dict(color="#64748B", size=12)
        ),
        xaxis=dict(
            showgrid=False, 
            zeroline=False,
            title="",
            tickformat="%d/%m\n%H:%M",
            tickfont=dict(color="#64748B", size=11)
        ),
        hovermode="x unified",
        height=350
    )
    
    st.markdown("<div class='premium-card' style='padding:15px;'>", unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    display_df = df.copy()
    display_df["Date"] = display_df["Date"].dt.strftime("%d/%m/%Y %H:%M")
    display_df["Wind"] = round(display_df["Wind"] / 1.852, 1)
    display_df["Visibility"] = round(display_df["Visibility"] / 1000, 1)
    display_df["Waves"] = round(display_df["Waves"], 1)
    display_df["Clouds"] = round(display_df["Clouds"], 0)

    styled_df = display_df[["Date", "Score", "Waves", "Wind", "Visibility", "Clouds"]].style\
        .background_gradient(subset=['Score'], cmap='RdYlGn', vmin=0, vmax=100)\
        .format({
            "Waves": "{:.1f}", 
            "Wind": "{:.1f}", 
            "Visibility": "{:.1f}", 
            "Clouds": "{:.0f}"
        })

    st.markdown("<div class='premium-card' style='padding:0px; overflow:hidden;'>", unsafe_allow_html=True)
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    st.markdown("</div>", unsafe_allow_html=True)
    