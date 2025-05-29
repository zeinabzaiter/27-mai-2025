import streamlit as st
import pandas as pd
import numpy as np

try:
    import matplotlib.pyplot as plt
except ImportError:
    st.error("Le module matplotlib n'est pas installé sur votre environnement. Ajoutez-le dans les dépendances ou requirements.txt avec :\n\nmatplotlib\n\nPuis redémarrez l'app.")
    st.stop()


# Style général (polices très visibles, bold)
st.markdown("""
    <style>
        .css-10trblm, .css-1v3fvcr, .css-1d391kg { font-size:28px !important; font-weight:bold;}
        .stDataFrame th, .stDataFrame td {font-size: 18px !important;}
        h1, h2, h3, h4, h5, h6 { font-weight: bold !important;}
        .element-container { font-size: 20px !important; }
    </style>
    """, unsafe_allow_html=True)

# 1. Chargement des données
@st.cache_data
def load_data():
    data = {}
    data["export_df"] = pd.read_csv("Export_StaphAureus_COMPLET.csv")
    data["all_bact"] = pd.read_excel("TOUS les bacteries a etudier.xlsx")
    data["other_ab"] = pd.read_excel("other Antibiotiques staph aureus.xlsx")
    data["pheno"] = pd.read_excel("staph_aureus_pheno_final.xlsx")
    data["tests_ab"] = pd.read_csv("tests_par_semaine_antibiotiques_2024.csv")
    return data

dfs = load_data()
export_df = dfs["export_df"]
all_bact = dfs["all_bact"]
other_ab = dfs["other_ab"]
pheno = dfs["pheno"]
tests_ab = dfs["tests_ab"]

# Fonction utilitaire : rolling moyenne mobile et IC95%
def rolling_with_ci(series, window=8):
    rolling_mean = series.rolling(window=window, min_periods=1).mean()
    rolling_std = series.rolling(window=window, min_periods=1).std()
    n = series.rolling(window=window, min_periods=1).count()
    ci95 = 1.96 * (rolling_std / np.sqrt(n))
    return rolling_mean, ci95

# TITRE principal
st.markdown("<h1 style='font-size:48px; color:#19334d; font-weight:bold;'>Dashboard - Surveillance Bactériologique 2024</h1>", unsafe_allow_html=True)

# Onglets
onglet = st.tabs([
    "Toutes les bactéries",
    "Résistance - Tests",
    "Résistance - Other AB",
    "Phénotypes",
    "Tableau Interactif",
    "Alertes par Service"
])

# === ONGLET 1 : Toutes les bactéries ===
with onglet[0]:
    st.header("Nombre d'isolats par bactérie (filtrable par semaine)", divider="rainbow")
    semaine_col = next((c for c in export_df.columns if "semaine" in c.lower()), None)
    bacterie_col = next((c for c in export_df.columns if "germe" in c.lower() or "bact" in c.lower()), None)
    if semaine_col and bacterie_col:
        semaines = sorted(export_df[semaine_col].dropna().unique())
        semaine_sel = st.selectbox("Filtrer par semaine :", options=["Toutes"] + [int(s) for s in semaines])
        df_plot = export_df.copy()
        if semaine_sel != "Toutes":
            df_plot = df_plot[df_plot[semaine_col] == int(semaine_sel)]
        counts = df_plot[bacterie_col].value_counts()
        fig, ax = plt.subplots(figsize=(10,6))
        bars = ax.bar(counts.index, counts.values, color='#2166ac')
        ax.set_ylabel("Nombre d'isolats", fontsize=22, fontweight='bold')
        ax.set_xlabel("Bactérie", fontsize=22, fontweight='bold')
        ax.set_title("Répartition des isolats par bactérie", fontsize=26, fontweight='bold')
        plt.xticks(rotation=45, ha='right', fontsize=18)
        plt.yticks(fontsize=18)
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"{int(bar.get_height())}", ha='center', va='bottom', fontsize=18, color='red', fontweight='bold')
        st.pyplot(fig)
    else:
        st.error("Colonnes bactérie ou semaine non trouvées.")

# === ONGLET 2 : Résistance - Tests ===
with onglet[1]:
    st.header("Évolution % Résistance par antibiotique (tests principaux)", divider="rainbow")
    ab_cols = [col for col in export_df.columns if col.startswith('q') or col in ['peni','oxa','fox','ctx','cro','cef','cli','ery','cip','sxt','tet','van']]
    semaine_col = next((c for c in export_df.columns if "semaine" in c.lower()), None)
    if not ab_cols or not semaine_col:
        st.error("Colonnes antibiotiques ou semaine manquantes.")
    else:
        ab_sel = st.selectbox("Choisir l'antibiotique :", ab_cols)
        seuil_alerte = st.slider("Seuil d'alerte (%)", 0, 100, 50)
        df_plot = export_df[[semaine_col, ab_sel]].dropna()
        # On considère R comme résistance
        res_count = df_plot.groupby(semaine_col)[ab_sel].apply(lambda x: (x == 'R').sum())
        tot_count = df_plot.groupby(semaine_col)[ab_sel].count()
        pct = (res_count / tot_count * 100).fillna(0)
        roll, ci = rolling_with_ci(pct)
        fig, ax = plt.subplots(figsize=(11,6))
        ax.plot(pct.index, pct.values, '-o', label='% Résistance', color='#D7263D', linewidth=3, markersize=10)
        ax.plot(roll.index, roll.values, '-s', label='Moy. mobile (8 sem)', color='#133C55', linewidth=4)
        ax.fill_between(roll.index, roll-ci, roll+ci, color='#133C55', alpha=0.18, label='IC95%')
        ax.axhline(seuil_alerte, color='red', linestyle='--', linewidth=3, label='Seuil Alerte')
        ax.set_xlabel("Semaine", fontsize=20, fontweight='bold')
        ax.set_ylabel("% Résistance", fontsize=20, fontweight='bold')
        ax.set_title(f"Évolution de la résistance à {ab_sel}", fontsize=26, fontweight='bold')
        ax.legend(fontsize=17, loc='upper left')
        plt.xticks(fontsize=17)
        plt.yticks(fontsize=17)
        st.pyplot(fig)

# === ONGLET 3 : Résistance - Other AB ===
with onglet[2]:
    st.header("Évolution % Résistance autres antibiotiques", divider="rainbow")
    semaine_col = next((c for c in other_ab.columns if "semaine" in c.lower()), None)
    ab_cols = [col for col in other_ab.columns if col not in [semaine_col, 'id', 'uf', 'num_specimen', 'nature', 'code_germe', 'lib_germe']]
    if not ab_cols or not semaine_col:
        st.error("Colonnes manquantes dans autres antibiotiques.")
    else:
        ab_sel = st.selectbox("Choisir l'antibiotique :", ab_cols)
        seuil_alerte = st.slider("Seuil d'alerte (%)", 0, 100, 30)
        df_plot = other_ab[[semaine_col, ab_sel]].dropna()
        res_count = df_plot.groupby(semaine_col)[ab_sel].apply(lambda x: (x == 'R').sum())
        tot_count = df_plot.groupby(semaine_col)[ab_sel].count()
        pct = (res_count / tot_count * 100).fillna(0)
        roll, ci = rolling_with_ci(pct)
        fig, ax = plt.subplots(figsize=(11,6))
        ax.plot(pct.index, pct.values, '-o', label='% Résistance', color='#DA7635', linewidth=3, markersize=10)
        ax.plot(roll.index, roll.values, '-s', label='Moy. mobile (8 sem)', color='#003049', linewidth=4)
        ax.fill_between(roll.index, roll-ci, roll+ci, color='#003049', alpha=0.16, label='IC95%')
        ax.axhline(seuil_alerte, color='red', linestyle='--', linewidth=3, label='Seuil Alerte')
        ax.set_xlabel("Semaine", fontsize=20, fontweight='bold')
        ax.set_ylabel("% Résistance", fontsize=20, fontweight='bold')
        ax.set_title(f"Évolution autre AB : {ab_sel}", fontsize=26, fontweight='bold')
        ax.legend(fontsize=17, loc='upper left')
        plt.xticks(fontsize=17)
        plt.yticks(fontsize=17)
        st.pyplot(fig)

# === ONGLET 4 : Phénotypes ===
with onglet[3]:
    st.header("Phénotypes (évolution, filtres, seuils…)", divider="rainbow")
    semaine_col = next((c for c in pheno.columns if "semaine" in c.lower()), None)
    pheno_cols = [col for col in pheno.columns if col not in [semaine_col, 'id', 'uf', 'nature', 'code_germe', 'lib_germe']]
    if not pheno_cols or not semaine_col:
        st.error("Colonnes manquantes dans phénotypes.")
    else:
        pheno_sel = st.selectbox("Choisir le phénotype :", pheno_cols)
        seuil_alerte = st.slider("Seuil d'alerte (%)", 0, 100, 10)
        df_plot = pheno[[semaine_col, pheno_sel]].dropna()
        res_count = df_plot.groupby(semaine_col)[pheno_sel].apply(lambda x: (x == 'R').sum())
        tot_count = df_plot.groupby(semaine_col)[pheno_sel].count()
        pct = (res_count / tot_count * 100).fillna(0)
        roll, ci = rolling_with_ci(pct)
        fig, ax = plt.subplots(figsize=(11,6))
        ax.plot(pct.index, pct.values, '-o', label='% Phénotype', color='#008148', linewidth=3, markersize=10)
        ax.plot(roll.index, roll.values, '-s', label='Moy. mobile (8 sem)', color='#165b33', linewidth=4)
        ax.fill_between(roll.index, roll-ci, roll+ci, color='#165b33', alpha=0.16, label='IC95%')
        ax.axhline(seuil_alerte, color='red', linestyle='--', linewidth=3, label='Seuil Alerte')
        ax.set_xlabel("Semaine", fontsize=20, fontweight='bold')
        ax.set_ylabel("%", fontsize=20, fontweight='bold')
        ax.set_title(f"Évolution du phénotype : {pheno_sel}", fontsize=26, fontweight='bold')
        ax.legend(fontsize=17, loc='upper left')
        plt.xticks(fontsize=17)
        plt.yticks(fontsize=17)
        st.pyplot(fig)

# === ONGLET 5 : Tableau Interactif ===
with onglet[4]:
    st.header("Exploration interactive du jeu de données", divider="rainbow")
    # On affiche un filtre par colonne :
    filter_col = st.selectbox("Filtrer sur la colonne :", export_df.columns)
    search = st.text_input(f"Filtrer {filter_col} (laisser vide pour tout afficher) :")
    df_plot = export_df.copy()
    if search:
        df_plot = df_plot[df_plot[filter_col].astype(str).str.contains(search, case=False, na=False)]
    st.dataframe(df_plot, use_container_width=True, hide_index=True)

# === ONGLET 6 : Alertes par Service ===
with onglet[5]:
    st.header("Alertes par service", divider="rainbow")
    semaine_col = next((c for c in export_df.columns if "semaine" in c.lower()), None)
    uf_col = next((c for c in export_df.columns if "uf" in c.lower()), None)
    alerte_col = next((c for c in export_df.columns if "alerte" in c.lower()), None)
    if None in [semaine_col, uf_col, alerte_col]:
        st.error("Colonnes semaine, uf, ou alerte manquantes.")
    else:
        sem_dispo = sorted(export_df[semaine_col].dropna().unique())
        sem_choisie = st.selectbox("Choisir la semaine :", options=sem_dispo)
        subset = export_df[export_df[semaine_col]==sem_choisie]
        alerts = subset[[uf_col, alerte_col]].drop_duplicates()
        # Si alertes présentes :
        if not alerts.empty:
            st.dataframe(alerts, hide_index=True)
            st.markdown("<span style='color: red; font-size:36px; font-weight:bold;'>🔴 ALERTE!</span>", unsafe_allow_html=True)
        else:
            st.info("Aucune alerte cette semaine.")

