import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Azores Whale Watching Forecaster", page_icon="🐋", layout="wide")

# --- MOTEUR DE PRÉVISION ---
class WhaleWatchingPredictor:
    def __init__(self):
        self.poids = {'vagues': 40, 'vent': 35, 'visibilite': 15, 'soleil': 10}
        self.max_vagues_m = 2.0      
        self.max_vent_noeuds = 22.0  
        self.min_visibilite_km = 2.0 

    def calculer_probabilite(self, vagues, vent_kmh, vent_deg, visi_m, nuages):
        # Conversion des unités de l'API
        vent_noeuds = vent_kmh / 1.852
        visi_km = visi_m / 1000

        # Kill switches
        if vagues > self.max_vagues_m or vent_noeuds > self.max_vent_noeuds or visi_km < self.min_visibilite_km:
            return 0.0

        # Scores
        score_vagues = 100 if vagues <= 0.5 else max(0, 100 - ((vagues - 0.5) / 1.5) * 100)
        
        vent_effectif = vent_noeuds
        if 270 <= vent_deg <= 360 or 0 <= vent_deg <= 90:
            vent_effectif = vent_noeuds * 0.8 # Protection de l'île
            
        score_vent = 100 if vent_noeuds <= 5 else max(0, 100 - ((vent_effectif - 5) / 17) * 100)
        score_visibilite = 100 if visi_km >= 10 else max(0, ((visi_km - 2) / 8) * 100)
        score_soleil = 100 - (nuages * 0.5)

        score_final = (
            (score_vagues * self.poids['vagues'] / 100) +
            (score_vent * self.poids['vent'] / 100) +
            (score_visibilite * self.poids['visibilite'] / 100) +
            (score_soleil * self.poids['soleil'] / 100)
        )
        return round(score_final, 1)

# --- FONCTION DE RÉCUPÉRATION DES DONNÉES (API) ---
@st.cache_data(ttl=3600) # Met en cache pendant 1h pour ne pas surcharger l'API
def fetch_weather_data():
    # Coordonnées de Ponta Delgada
    lat, lon = 37.74, -25.67
    
    # Appel API Météo Classique (Vent, Visi, Nuages)
    url_weather = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=windspeed_10m,winddirection_10m,visibility,cloudcover&timezone=auto"
    # Appel API Marine (Vagues)
    url_marine = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&hourly=wave_height&timezone=auto"

    res_weather = requests.get(url_weather).json()
    res_marine = requests.get(url_marine).json()

    # Création du DataFrame
    df = pd.DataFrame({
        'Date': pd.to_datetime(res_weather['hourly']['time']),
        'Vent_kmh': res_weather['hourly']['windspeed_10m'],
        'Direction_Vent': res_weather['hourly']['winddirection_10m'],
        'Visibilite_m': res_weather['hourly']['visibility'],
        'Nuages_pct': res_weather['hourly']['cloudcover'],
        'Vagues_m': res_marine['hourly']['wave_height']
    })
    
    # Filtrer uniquement les heures de jour (8h à 19h)
    df = df[(df['Date'].dt.hour >= 8) & (df['Date'].dt.hour <= 19)]
    
    # Calcul des probabilités
    predictor = WhaleWatchingPredictor()
    df['Score (%)'] = df.apply(lambda row: predictor.calculer_probabilite(
        row['Vagues_m'], row['Vent_kmh'], row['Direction_Vent'], 
        row['Visibilite_m'], row['Nuages_pct']
    ), axis=1)

    return df

# --- INTERFACE UTILISATEUR ---
st.title("🐋 Azores Whale Watching - Prévisions de Sortie")
st.markdown("Basé sur les conditions météo au départ de **Ponta Delgada (Embarcation 9m)**. Les données sont récupérées en temps réel et prévoient les 7 prochains jours.")

# Récupération des données
with st.spinner('Récupération des données météo en cours...'):
    df = fetch_weather_data()

# Conditions actuelles (ou la plus proche)
now = datetime.now()
future_df = df[df['Date'] >= now]
if not future_df.empty:
    current = future_df.iloc[0]
    st.header("📍 Conditions Actuelles (Prochain créneau)")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Couleur du score
    score_color = "🟢" if current['Score (%)'] > 75 else "🟠" if current['Score (%)'] > 40 else "🔴"
    
    col1.metric("Faisabilité", f"{score_color} {current['Score (%)']}%")
    col2.metric("Vagues", f"{current['Vagues_m']} m")
    col3.metric("Vent", f"{round(current['Vent_kmh'] / 1.852, 1)} nds")
    col4.metric("Visibilité", f"{round(current['Visibilite_m'] / 1000, 1)} km")
    col5.metric("Nuages", f"{current['Nuages_pct']} %")

st.markdown("---")

# Graphique de prévisions sur 7 jours
st.header("📅 Prévisions sur 7 Jours (Horaires de jour: 8h - 19h)")
fig = px.bar(
    df, x='Date', y='Score (%)', 
    color='Score (%)', 
    color_continuous_scale=[(0, "red"), (0.5, "orange"), (1, "green")],
    title="Évolution des chances de sortie (100% = Conditions Parfaites)",
    labels={'Date': 'Date et Heure', 'Score (%)': 'Probabilité de Sortie (%)'}
)
fig.update_layout(xaxis_tickformat='%A %d - %H:%M')
st.plotly_chart(fig, use_container_width=True)

# Tableau détaillé pour choisir l'horaire
st.header("🕒 Choisir le meilleur horaire de départ")
st.markdown("Clique sur l'entête des colonnes pour trier (ex: pour trouver les scores les plus hauts).")

# Formatage pour un tableau plus lisible
df_display = df.copy()
df_display['Date'] = df_display['Date'].dt.strftime('%d/%m/%Y à %H:%M')
df_display['Vent (Noeuds)'] = round(df_display['Vent_kmh'] / 1.852, 1)
df_display['Visibilité (km)'] = round(df_display['Visibilite_m'] / 1000, 1)

# Sélection des colonnes à afficher
cols_to_show = ['Date', 'Score (%)', 'Vagues_m', 'Vent (Noeuds)', 'Direction_Vent', 'Visibilité (km)', 'Nuages_pct']
st.dataframe(
    df_display[cols_to_show].style.background_gradient(cmap='RdYlGn', subset=['Score (%)']),
    use_container_width=True,
    hide_index=True
)