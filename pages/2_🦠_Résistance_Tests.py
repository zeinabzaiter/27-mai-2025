import streamlit as st
import pandas as pd
import plotly.express as px

#st.set_page_config(page_title="Résistance Tests", layout="wide")

st.title("🦠 Résistance - Tests antibiotiques")

# Chargement des données
df = pd.read_csv("tests_par_semaine_antibiotiques_2024.csv")

# Sidebar interactive
semaines_selectionnees = st.sidebar.multiselect(
    "Filtrer par semaines :",
    options=df['semaine'].unique(),
    default=df['semaine'].unique()
)

# Filtrer les données selon les semaines sélectionnées
df_filtre = df[df['semaine'].isin(semaines_selectionnees)]

# Calcul IC95% avec moyenne mobile sur 8 semaines
df_filtre['moyenne_mobile'] = df_filtre.groupby('antibiotique')['resistance'].transform(lambda x: x.rolling(window=8, min_periods=1).mean())
df_filtre['std_mobile'] = df_filtre.groupby('antibiotique')['resistance'].transform(lambda x: x.rolling(window=8, min_periods=1).std())
df_filtre['upper_IC95'] = df_filtre['moyenne_mobile'] + 1.96 * df_filtre['std_mobile']

# Visualisation interactive claire et lisible
fig = px.line(
    df_filtre, 
    x="semaine", 
    y="moyenne_mobile", 
    color='antibiotique', 
    markers=True, 
    title="Évolution des résistances antibiotiques avec seuil d'alerte IC95%"
)

# Ajouter le seuil d'alerte IC95%
for ab in df_filtre['antibiotique'].unique():
    seuil = df_filtre[df_filtre['antibiotique'] == ab]['upper_IC95'].mean()
    fig.add_hline(y=seuil, line_dash="dash", line_color="red", annotation_text=f"Seuil alerte {ab}", annotation_position="top left")

st.plotly_chart(fig, use_container_width=True)

# Affichage clair d'alertes
st.subheader("🚨 Alertes en cours :")
for ab in df_filtre['antibiotique'].unique():
    dernier_point = df_filtre[df_filtre['antibiotique'] == ab].iloc[-1]
    if dernier_point['moyenne_mobile'] > dernier_point['upper_IC95']:
        st.error(f"Alerte : Résistance élevée pour {ab} à la semaine {dernier_point['semaine']} 🚩")
