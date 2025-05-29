import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Surveillance S. aureus 2024", layout="wide")

@st.cache_data
def load_all_data():
    df_export = pd.read_csv("Export_StaphAureus_COMPLET.csv")
    df_bact = pd.read_excel("TOUS les bacteries a etudier.xlsx")
    df_tests = pd.read_csv("tests_par_semaine_antibiotiques_2024.csv")
    df_other = pd.read_excel("other Antibiotiques staph aureus.xlsx")
    df_pheno = pd.read_excel("staph_aureus_pheno_final.xlsx")
    return df_export, df_bact, df_tests, df_other, df_pheno

df_export, df_bact, df_tests, df_other, df_pheno = load_all_data()

st.markdown(
    "<h1 style='text-align:center;font-size:3.2em;font-weight:900;'>🦠 DASHBOARD DE SURVEILLANCE BACTÉRIOLOGIQUE 2024</h1>",
    unsafe_allow_html=True
)

tabs = st.tabs([
    "Toutes les bactéries", 
    "Résistance - Tests", 
    "Résistance - Other AB", 
    "Phénotypes", 
    "Tableau Interactif", 
    "Alertes par Service"
])

############## ONGLET 1
with tabs[0]:
    st.markdown("<h2 style='font-size:2.5em;font-weight:900;'>🧫 Répartition des bactéries isolées</h2>", unsafe_allow_html=True)
    semaine_col = next((c for c in df_export.columns if "semaine" in c.lower() or "week" in c.lower()), None)
    germe_col = next((c for c in df_export.columns if "germe" in c.lower()), None)
    if semaine_col and germe_col:
        sem_liste = sorted(df_export[semaine_col].dropna().unique())
        sem_filtre = st.multiselect("Filtrer par semaine :", sem_liste, default=sem_liste)
        df_tmp = df_export[df_export[semaine_col].isin(sem_filtre)]
        counts = df_tmp[germe_col].value_counts().sort_values(ascending=False)
        fig = go.Figure(go.Bar(
            x=counts.values, y=counts.index,
            orientation='h',
            marker=dict(color="black"),
            text=counts.values, textposition='auto'
        ))
        fig.update_layout(
            xaxis_title="Nombre d'isolats",
            yaxis_title="Bactérie",
            font=dict(size=22, color='black', family='Arial'),
            plot_bgcolor="white"
        )
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("<h4 style='margin-top:2em;'>Tableau récapitulatif :</h4>", unsafe_allow_html=True)
    st.dataframe(df_export[[semaine_col, germe_col]].value_counts().reset_index().rename({0:'nb'}, axis=1))

############## ONGLET 2
def plot_resistance(df, titre, onglet_key):
    semaine_col = next((c for c in df.columns if "semaine" in c.lower() or "week" in c.lower()), None)
    ab_cols = [c for c in df.columns if "%" in c or "res" in c.lower()]
    if not ab_cols or not semaine_col:
        st.warning("Colonnes de % résistance ou semaine absentes.")
        return
    selected_ab = st.selectbox("Choisir l'antibiotique :", ab_cols, key=onglet_key)
    # Prépa Data
    d = df[[semaine_col, selected_ab]].copy()
    d = d.dropna()
    d = d.sort_values(semaine_col)
    d["p"] = pd.to_numeric(d[selected_ab], errors='coerce') / 100
    # Rolling
    d["n_last_8"] = 8
    d["event_last_8"] = d["p"].rolling(8, min_periods=1).sum()
    d["p_hat"] = d["event_last_8"] / d["n_last_8"]
    d["se"] = np.sqrt(d["p_hat"] * (1-d["p_hat"]) / d["n_last_8"])
    d["upper"] = d["p_hat"] + 1.96 * d["se"]
    d["outlier"] = d["p"] > d["upper"]
    # Plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=d[semaine_col], y=d["p"], mode="lines+markers",
        name="% Résistance", line=dict(width=6, color='black'),
        marker=dict(size=18, color="black")
    ))
    fig.add_trace(go.Scatter(
        x=d[semaine_col], y=d["upper"], mode="lines",
        name="Seuil d'alerte (IC 95%)", line=dict(width=5, color='red', dash='dot')
    ))
    fig.add_trace(go.Scatter(
        x=d[d["outlier"]][semaine_col], y=d[d["outlier"]]["p"], mode="markers",
        name="Alerte", marker=dict(size=30, color="darkred", symbol="circle"),
        showlegend=True
    ))
    fig.update_layout(
        title=f"<b style='font-size:2em'>{titre} - {selected_ab}</b>",
        xaxis_title="Semaine", yaxis_title="% Résistance (proportion)",
        font=dict(size=26, color='black', family='Arial'),
        plot_bgcolor="white"
    )
    st.plotly_chart(fig, use_container_width=True)
    if d["outlier"].any():
        st.markdown("<b style='color:red;font-size:1.5em;'>🚨 Alerte(s) détectée(s) !</b>", unsafe_allow_html=True)
        st.dataframe(d[d["outlier"]][[semaine_col, selected_ab, "upper"]])
    else:
        st.info("Aucune alerte détectée selon la règle IC + 8 semaines.")

with tabs[1]:
    st.markdown("<h2 style='font-size:2em;font-weight:900;'>💉 Résistance - Tests</h2>", unsafe_allow_html=True)
    plot_resistance(df_tests, "Résistance hebdo (tests)", "res_tests")

############## ONGLET 3
with tabs[2]:
    st.markdown("<h2 style='font-size:2em;font-weight:900;'>💉 Résistance - Other AB</h2>", unsafe_allow_html=True)
    plot_resistance(df_other, "Résistance hebdo (other AB)", "res_other")

############## ONGLET 4
with tabs[3]:
    st.markdown("<h2 style='font-size:2em;font-weight:900;'>Phénotypes (analyse dynamique)</h2>", unsafe_allow_html=True)
    semaine_col = next((c for c in df_pheno.columns if "semaine" in c.lower() or "week" in c.lower()), None)
    pheno_cols = [c for c in df_pheno.columns if c.lower() != semaine_col.lower()]
    selected_pheno = st.selectbox("Choisir un phénotype :", pheno_cols)
    d = df_pheno[[semaine_col, selected_pheno]].copy()
    d = d.dropna().sort_values(semaine_col)
    # Proportion % si c'est en nombre
    if d[selected_pheno].max() > 1.1:
        total = d[selected_pheno].rolling(8, min_periods=1).sum()
        p = d[selected_pheno] / total
    else:
        p = d[selected_pheno]
    d["p"] = p
    # IC
    d["p_hat"] = d["p"].rolling(8, min_periods=1).mean()
    d["se"] = np.sqrt(d["p_hat"] * (1-d["p_hat"]) / 8)
    d["upper"] = d["p_hat"] + 1.96 * d["se"]
    d["outlier"] = d["p"] > d["upper"]
    # Plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=d[semaine_col], y=d["p"], mode="lines+markers",
        name="% Phénotype", line=dict(width=6, color='black'),
        marker=dict(size=18, color="black")
    ))
    fig.add_trace(go.Scatter(
        x=d[semaine_col], y=d["upper"], mode="lines",
        name="Seuil d'alerte (IC 95%)", line=dict(width=5, color='red', dash='dot')
    ))
    fig.add_trace(go.Scatter(
        x=d[d["outlier"]][semaine_col], y=d[d["outlier"]]["p"], mode="markers",
        name="Alerte", marker=dict(size=30, color="darkred", symbol="circle"),
        showlegend=True
    ))
    fig.update_layout(
        title=f"<b style='font-size:2em'>{selected_pheno}</b>",
        xaxis_title="Semaine", yaxis_title="% ou nb (rolling)",
        font=dict(size=26, color='black', family='Arial'),
        plot_bgcolor="white"
    )
    st.plotly_chart(fig, use_container_width=True)
    if d["outlier"].any():
        st.markdown("<b style='color:red;font-size:1.5em;'>🚨 Alerte(s) détectée(s) !</b>", unsafe_allow_html=True)
        st.dataframe(d[d["outlier"]][[semaine_col, selected_pheno, "upper"]])
    else:
        st.info("Aucune alerte détectée selon la règle IC + 8 semaines.")

############## ONGLET 5
with tabs[4]:
    st.markdown("<h2 style='font-size:2em;font-weight:900;'>🔎 Tableau interactif</h2>", unsafe_allow_html=True)
    col_sel = st.multiselect("Colonnes à afficher :", options=list(df_export.columns), default=list(df_export.columns)[:7])
    filtre_val = st.text_input("Filtrer (mot-clé sur toutes les colonnes affichées) :")
    df_to_show = df_export[col_sel]
    if filtre_val.strip():
        mask = df_to_show.astype(str).apply(lambda s: filtre_val.lower() in s.lower()).any(axis=1)
        df_to_show = df_to_show[mask]
    st.dataframe(df_to_show, use_container_width=True)

############## ONGLET 6
with tabs[5]:
    st.markdown("<h2 style='font-size:2em;font-weight:900;'>🚨 Alertes par Service</h2>", unsafe_allow_html=True)
    semaine_col = next((c for c in df_export.columns if "semaine" in c.lower() or "week" in c.lower()), None)
    uf_col = next((c for c in df_export.columns if "uf" in c.lower()), None)
    alerte_col = next((c for c in df_export.columns if "alerte" in c.lower()), None)
    germe_col = next((c for c in df_export.columns if "germe" in c.lower()), None)
    sem_liste = sorted(df_export[semaine_col].dropna().unique())
    s_choisie = st.selectbox("Semaine :", sem_liste, key="alerte_sem")
    if None in [uf_col, alerte_col, germe_col, semaine_col]:
        st.error("Colonnes 'uf', 'alerte', 'germe', ou 'semaine' manquantes.")
    else:
        filt = (df_export[semaine_col] == s_choisie) & (df_export[alerte_col].notnull())
        df_alert = df_export.loc[filt, [semaine_col, uf_col, alerte_col, germe_col]].drop_duplicates()
        if not df_alert.empty:
            st.dataframe(df_alert, use_container_width=True)
        else:
            st.info("Aucune alerte détectée pour cette semaine.")

