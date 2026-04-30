# app.py
import streamlit as st
import pandas as pd
import numpy as np
import os
import re
from visualisations import radar_joueur, cartographie_mc, pizza_chart

# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="MC Scouting — Scouting contextuel",
    page_icon="⚽",
    layout="wide"
)

DEMO_PATH = "data/df_final_mc.csv"
NORM_PATH = "data/df_players_norm_mc.csv"

# ── Détection langue via URL ──────────────────────────────
try:
    params = st.query_params
    lang = params.get("lang", "fr").lower()
except:
    lang = "fr"
if lang not in ["fr", "es"]:
    lang = "fr"

# ── Dictionnaire de traductions ───────────────────────────
T = {
    "fr": {
        "page_title":        "MC Scouting — Scouting contextuel",
        "sidebar_title":     "⚽ MC Scouting",
        "sidebar_subtitle":  "*Scouting contextuel multi-ligues*",
        "mode_label":        "Mode de données",
        "mode_demo":         "🎯 Démo (données pré-calculées)",
        "mode_custom":       "📁 Custom (mes exports Wyscout)",
        "joueurs_charges":   "joueurs chargés",
        "joueurs_traites":   "joueurs traités",
        "fichiers_equipes":  "Fichiers équipes",
        "equipes_label":     "Équipes",
        "fichiers_joueurs":  "Fichiers joueurs",
        "joueurs_label":     "Joueurs",
        "calcul_pipeline":   "Calcul du pipeline en cours...",
        "upload_info":       "👈 Upload tes fichiers Wyscout dans la sidebar pour commencer.",
        "erreur":            "❌ Erreur",
        "tab1":              "🔍 Scouting",
        "tab2":              "🗺️ Cartographie",
        "tab3":              "📊 Profil joueur",
        "tab4":              "📋 Shortlist",
        "tab5":              "📖 Méthodologie",
        "header_scouting":   "🔍 Scouting contextuel",
        "ligue":             "Ligue",
        "toutes":            "Toutes",
        "profil_mc":         "Profil MC",
        "minutes_min":       "Minutes min.",
        "age_max":           "Âge max.",
        "valeur_max":        "Valeur marchande max (M€)",
        "contrat":           "Contrat expire avant",
        "tous":              "Tous",
        "fiabilite":         "Fiabilité",
        "joueurs_filtres":   "joueurs correspondent aux critères",
        "selectionne":       "Sélectionne un joueur",
        "aucun_joueur":      "Aucun joueur ne correspond aux filtres.",
        "header_carto":      "🗺️ Cartographie des MC",
        "axe_x":             "Axe X",
        "axe_y":             "Axe Y",
        "header_profil":     "📊 Profil joueur",
        "visualisation":     "Visualisation",
        "radar":             "Radar (brut vs ajusté)",
        "pizza":             "Pizza chart (détail métriques)",
        "telecharger":       "⬇️ Télécharger",
        "header_shortlist":  "📋 Shortlist Recrutement",
        "profil":            "Profil",
        "joueurs_categorie": "Joueurs par catégorie",
        "profils_surs":      "Profils sûrs — Titulaires",
        "rotation":          "Rotation fiable",
        "potentiel":         "Potentiel",
        "paris":             "Paris / Upside",
        "header_methodo":    "📖 Méthodologie",
        "joueur":            "Joueur",
        "equipe":            "Équipe",
        "age":               "Âge",
        "valeur":            "Valeur (M€)",
        "minutes":           "Minutes",
        "score_profil":      "Score profil",
        "impact":            "Impact (%)",
        "score":             "Score",
        "footer":            "Data : Hudl Wyscout · Modèle : Tom Hamel · Scouting contextuel MC 2025/2026",
    },
    "es": {
        "page_title":        "MC Scouting — Scouting contextual",
        "sidebar_title":     "⚽ MC Scouting",
        "sidebar_subtitle":  "*Scouting contextual multi-ligas*",
        "mode_label":        "Modo de datos",
        "mode_demo":         "🎯 Demo (datos precalculados)",
        "mode_custom":       "📁 Custom (mis exportaciones Wyscout)",
        "joueurs_charges":   "jugadores cargados",
        "joueurs_traites":   "jugadores procesados",
        "fichiers_equipes":  "Archivos equipos",
        "equipes_label":     "Equipos",
        "fichiers_joueurs":  "Archivos jugadores",
        "joueurs_label":     "Jugadores",
        "calcul_pipeline":   "Calculando el pipeline...",
        "upload_info":       "👈 Sube tus archivos Wyscout en la barra lateral para empezar.",
        "erreur":            "❌ Error",
        "tab1":              "🔍 Scouting",
        "tab2":              "🗺️ Cartografía",
        "tab3":              "📊 Perfil jugador",
        "tab4":              "📋 Shortlist",
        "tab5":              "📖 Metodología",
        "header_scouting":   "🔍 Scouting contextual",
        "ligue":             "Liga",
        "toutes":            "Todas",
        "profil_mc":         "Perfil MC",
        "minutes_min":       "Minutos mín.",
        "age_max":           "Edad máx.",
        "valeur_max":        "Valor de mercado máx (M€)",
        "contrat":           "Contrato expira antes de",
        "tous":              "Todos",
        "fiabilite":         "Fiabilidad",
        "joueurs_filtres":   "jugadores corresponden a los criterios",
        "selectionne":       "Selecciona un jugador",
        "aucun_joueur":      "Ningún jugador corresponde a los filtros.",
        "header_carto":      "🗺️ Cartografía de los MC",
        "axe_x":             "Eje X",
        "axe_y":             "Eje Y",
        "header_profil":     "📊 Perfil jugador",
        "visualisation":     "Visualización",
        "radar":             "Radar (bruto vs ajustado)",
        "pizza":             "Pizza chart (detalle métricas)",
        "telecharger":       "⬇️ Descargar",
        "header_shortlist":  "📋 Shortlist Reclutamiento",
        "profil":            "Perfil",
        "joueurs_categorie": "Jugadores por categoría",
        "profils_surs":      "Perfiles seguros — Titulares",
        "rotation":          "Rotación fiable",
        "potentiel":         "Potencial",
        "paris":             "Apuesta / Upside",
        "header_methodo":    "📖 Metodología",
        "joueur":            "Jugador",
        "equipe":            "Equipo",
        "age":               "Edad",
        "valeur":            "Valor (M€)",
        "minutes":           "Minutos",
        "score_profil":      "Puntuación perfil",
        "impact":            "Impacto (%)",
        "score":             "Puntuación",
        "footer":            "Data : Hudl Wyscout · Modelo : Tom Hamel · Scouting contextual MC 2025/2026",
    }
}

t = T[lang]

PROFILS = {
    "score_mc_recuperateur": "MC Récupérateur"    if lang == "fr" else "MC Recuperador",
    "score_mc_mdef":         "MC Défensif pur"    if lang == "fr" else "MC Defensivo puro",
    "score_mc_relanceur":    "MC Relanceur"        if lang == "fr" else "MC Relanzador",
    "score_mc_boxtbox":      "MC Box to Box",
    "score_mc_interieur":    "MC Intérieur"        if lang == "fr" else "MC Interior",
    "score_mc_offensif":     "MC Offensif"         if lang == "fr" else "MC Ofensivo",
}

TOOLTIPS = {
    "Score profil": (
        "Score de 0 à 100 mesurant l'adéquation du joueur avec le profil "
        "sélectionné. Calculé sur les stats ajustées au contexte de son équipe, "
        "normalisées inter-ligues. 100 = meilleur profil toutes ligues confondues."
    ) if lang == "fr" else (
        "Puntuación de 0 a 100 que mide la adecuación del jugador con el perfil "
        "seleccionado. Calculada sobre estadísticas ajustadas al contexto de su equipo, "
        "normalizadas entre ligas. 100 = mejor perfil de todas las ligas."
    ),
    "Impact contexte": (
        "Mesure si les stats du joueur sont gonflées ou dévalorisées par le style "
        "de jeu de son équipe. Positif = joueur sous-coté par son système. "
        "Négatif = joueur favorisé par son système."
    ) if lang == "fr" else (
        "Mide si las estadísticas del jugador están infladas o devaluadas por el estilo "
        "de juego de su equipo. Positivo = jugador infravalorado por su sistema. "
        "Negativo = jugador favorecido por su sistema."
    ),
}

# ============================================================
# CHARGEMENT
# ============================================================

@st.cache_data(ttl=0)
def load_demo():
    return pd.read_csv(DEMO_PATH)

@st.cache_data(ttl=0)
def load_players_norm():
    return pd.read_csv(NORM_PATH)

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(t["sidebar_title"])
st.sidebar.markdown(t["sidebar_subtitle"])
st.sidebar.markdown("---")

mode = st.sidebar.radio(
    t["mode_label"],
    [t["mode_demo"], t["mode_custom"]]
)

df_final        = None
df_players_norm = None

if mode == t["mode_demo"]:
    if os.path.exists(DEMO_PATH):
        df_final        = load_demo()
        df_players_norm = load_players_norm()
        st.sidebar.success(f"✅ {len(df_final)} {t['joueurs_charges']}")
    else:
        st.sidebar.error("❌ Fichier démo introuvable")
        st.stop()
else:
    st.sidebar.markdown(f"### {t['fichiers_equipes']}")
    uploaded_equipes = {}
    for ligue in ["L1", "L2", "Liga", "Liga_seg"]:
        files = st.sidebar.file_uploader(
            f"{t['equipes_label']} {ligue}", type=["xlsx"],
            accept_multiple_files=True, key=f"eq_{ligue}"
        )
        if files:
            uploaded_equipes[ligue] = files

    st.sidebar.markdown(f"### {t['fichiers_joueurs']}")
    uploaded_joueurs = {}
    for ligue in ["L1", "L2", "Liga", "Liga_seg"]:
        file = st.sidebar.file_uploader(
            f"{t['joueurs_label']} {ligue}", type=["xlsx"], key=f"j_{ligue}"
        )
        if file:
            uploaded_joueurs[ligue] = file

    if uploaded_equipes and uploaded_joueurs:
        with st.spinner(t["calcul_pipeline"]):
            try:
                from pipeline import load_teams, load_players
                from modele import normaliser_equipes, build_df_final
                df_teams   = load_teams(uploaded_equipes)
                df_norm    = normaliser_equipes(df_teams)
                df_players = load_players(uploaded_joueurs)
                df_final   = build_df_final(df_players, df_norm)
                st.sidebar.success(f"✅ {len(df_final)} {t['joueurs_traites']}")
            except Exception as e:
                st.sidebar.error(f"{t['erreur']} : {e}")
                st.stop()
    else:
        st.info(t["upload_info"])
        st.stop()

# ============================================================
# ONGLETS
# ============================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    t["tab1"], t["tab2"], t["tab3"], t["tab4"], t["tab5"]
])

# ============================================================
# ONGLET 1 — SCOUTING
# ============================================================

with tab1:
    st.header(t["header_scouting"])

    col1, col2, col3 = st.columns(3)
    with col1:
        ligues_dispo = [t["toutes"]] + sorted(
            df_final["ligue"].dropna().unique().tolist()
        )
        ligue_filtre = st.selectbox(t["ligue"], ligues_dispo, key="scout_ligue")
    with col2:
        profil = st.selectbox(
            t["profil_mc"], list(PROFILS.keys()),
            format_func=lambda x: PROFILS[x], key="scout_profil"
        )
    with col3:
        min_minutes = st.slider(t["minutes_min"], 0, 3000, 500, 100,
                                key="scout_min")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        max_age = st.slider(t["age_max"], 18, 40, 32, key="scout_age")
    with col_b:
        max_valeur = st.slider(t["valeur_max"], 0, 50, 50,
                               key="scout_valeur") \
            if "valeur_marchande" in df_final.columns else 50
    with col_c:
        if "contrat" in df_final.columns:
            annees_dispo = sorted(
                df_final["contrat"].dropna().astype(str)
                .str.extract(r"(20\d{2})")[0].dropna().unique().tolist()
            )
            max_contrat = st.selectbox(t["contrat"],
                                       [t["tous"]] + annees_dispo,
                                       key="scout_contrat")
        else:
            max_contrat = t["tous"]

    fiabilite = st.multiselect(
        t["fiabilite"],
        ["titulaire", "rotation", "echantillon_moyen", "faible_echantillon"],
        default=["titulaire", "rotation", "echantillon_moyen"],
        key="scout_fiabilite"
    )

    st.markdown("---")

    df_filtered = df_final.copy()
    if ligue_filtre != t["toutes"]:
        df_filtered = df_filtered[df_filtered["ligue"] == ligue_filtre]
    df_filtered = df_filtered[df_filtered["minutes"] >= min_minutes]
    if "age" in df_filtered.columns:
        df_filtered = df_filtered[
            pd.to_numeric(df_filtered["age"], errors="coerce") <= max_age
        ]
    if "valeur_marchande" in df_filtered.columns and max_valeur < 50:
        df_filtered = df_filtered[
            pd.to_numeric(df_filtered["valeur_marchande"],
                          errors="coerce").fillna(0) <= max_valeur * 1_000_000
        ]
    if max_contrat != t["tous"] and "contrat" in df_filtered.columns:
        def get_year(val):
            if pd.isna(val): return 9999
            m = re.search(r"(20\d{2})", str(val))
            return int(m.group(1)) if m else 9999
        df_filtered = df_filtered[
            df_filtered["contrat"].apply(get_year) <= int(max_contrat)
        ]
    if fiabilite:
        df_filtered = df_filtered[
            df_filtered["niveau_fiabilite"].isin(fiabilite)
        ]
    df_filtered = df_filtered.sort_values(profil, ascending=False)

    st.markdown(f"**{len(df_filtered)} {t['joueurs_filtres']}**")

    cols_affichage = [
        "joueur", "equipe_norm", "ligue", "age",
        "valeur_marchande", "contrat", "minutes",
        "niveau_fiabilite", profil, "impact_contexte"
    ]
    cols_affichage = [c for c in cols_affichage if c in df_filtered.columns]
    df_display     = df_filtered[cols_affichage].copy()
    df_display[profil]            = df_display[profil].round(1)
    df_display["impact_contexte"] = (df_display["impact_contexte"] * 100).round(1)
    if "valeur_marchande" in df_display.columns:
        df_display["valeur_marchande"] = (
            pd.to_numeric(df_display["valeur_marchande"], errors="coerce")
            / 1_000_000
        ).round(1)

    df_display = df_display.rename(columns={
        "joueur":           t["joueur"],
        "equipe_norm":      t["equipe"],
        "ligue":            "Liga" if lang == "es" else "Ligue",
        "age":              t["age"],
        "valeur_marchande": t["valeur"],
        "contrat":          "Contrato" if lang == "es" else "Contrat",
        "minutes":          t["minutes"],
        "niveau_fiabilite": "Fiabilidad" if lang == "es" else "Fiabilité",
        profil:             t["score_profil"],
        "impact_contexte":  t["impact"],
    })

    st.dataframe(
        df_display, use_container_width=True, hide_index=True,
        column_config={
            t["score_profil"]: st.column_config.ProgressColumn(
                t["score_profil"], help=TOOLTIPS["Score profil"],
                min_value=0, max_value=100, format="%.1f"
            ),
            t["impact"]: st.column_config.NumberColumn(
                t["impact"], help=TOOLTIPS["Impact contexte"],
                format="%.1f%%"
            ),
            t["valeur"]: st.column_config.NumberColumn(
                t["valeur"], format="%.1fM€"
            ),
        }
    )

    st.markdown("---")
    st.subheader("📡 Rapport scouting — Radar" if lang == "fr" else "📡 Informe scouting — Radar")
    joueurs_dispo = df_filtered["joueur"].dropna().unique().tolist()
    if joueurs_dispo:
        joueur_sel = st.selectbox(t["selectionne"], joueurs_dispo,
                                  key="scout_joueur")
        if joueur_sel:
            fig = radar_joueur(joueur_sel, df_final, df_players_norm)
            if fig:
                st.pyplot(fig)
    else:
        st.info(t["aucun_joueur"])

# ============================================================
# ONGLET 2 — CARTOGRAPHIE
# ============================================================

with tab2:
    st.header(t["header_carto"])

    PROFILS_LABELS = {
        "score_mc_recuperateur": "Récupérateur"  if lang == "fr" else "Recuperador",
        "score_mc_mdef":         "Défensif pur"  if lang == "fr" else "Defensivo puro",
        "score_mc_relanceur":    "Relanceur"      if lang == "fr" else "Relanzador",
        "score_mc_boxtbox":      "Box to Box",
        "score_mc_interieur":    "Intérieur"      if lang == "fr" else "Interior",
        "score_mc_offensif":     "Offensif"       if lang == "fr" else "Ofensivo",
    }

    col1, col2, col3 = st.columns(3)
    with col1:
        axe_x = st.selectbox(
            t["axe_x"], list(PROFILS_LABELS.keys()),
            format_func=lambda x: PROFILS_LABELS[x],
            index=0, key="carto_x"
        )
    with col2:
        axe_y = st.selectbox(
            t["axe_y"], list(PROFILS_LABELS.keys()),
            format_func=lambda x: PROFILS_LABELS[x],
            index=2, key="carto_y"
        )
    with col3:
        min_min_carto = st.slider(t["minutes_min"], 0, 3000, 500, 100,
                                  key="carto_min")

    col4, col5 = st.columns(2)
    with col4:
        ligue_carto = st.selectbox(
            t["ligue"],
            [t["toutes"]] + sorted(df_final["ligue"].dropna().unique().tolist()),
            key="carto_ligue"
        )
    with col5:
        max_age_carto = st.slider(t["age_max"], 18, 40, 40, key="carto_age")

    df_carto = df_final[df_final["minutes"] >= min_min_carto].copy()
    if ligue_carto != t["toutes"]:
        df_carto = df_carto[df_carto["ligue"] == ligue_carto]
    if "age" in df_carto.columns:
        df_carto = df_carto[
            pd.to_numeric(df_carto["age"], errors="coerce") <= max_age_carto
        ]

    fig_carto = cartographie_mc(
        df_carto,
        profil_x=axe_x,
        profil_y=axe_y,
        label_x=PROFILS_LABELS[axe_x],
        label_y=PROFILS_LABELS[axe_y]
    )
    st.plotly_chart(fig_carto, use_container_width=True)

# ============================================================
# ONGLET 3 — PROFIL JOUEUR
# ============================================================

with tab3:
    st.header(t["header_profil"])

    col1, col2 = st.columns(2)
    with col1:
        ligue_profil = st.selectbox(
            t["ligue"],
            [t["toutes"]] + sorted(df_final["ligue"].dropna().unique().tolist()),
            key="profil_ligue"
        )
    with col2:
        min_min_profil = st.slider(t["minutes_min"], 0, 3000, 500, 100,
                                   key="profil_min")

    df_profil = df_final[df_final["minutes"] >= min_min_profil].copy()
    if ligue_profil != t["toutes"]:
        df_profil = df_profil[df_profil["ligue"] == ligue_profil]

    joueurs_profil = sorted(df_profil["joueur"].dropna().unique().tolist())

    if joueurs_profil:
        joueur_profil = st.selectbox(
            t["selectionne"], joueurs_profil, key="profil_joueur"
        )

        viz_type = st.radio(
            t["visualisation"],
            [t["radar"], t["pizza"]],
            horizontal=True,
            key="profil_viz"
        )

        if viz_type == t["radar"]:
            fig = radar_joueur(joueur_profil, df_final, df_players_norm)
        else:
            fig = pizza_chart(joueur_profil, df_final)

        if fig:
            st.pyplot(fig)
            import io
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=300,
                        bbox_inches="tight",
                        facecolor=fig.get_facecolor())
            buf.seek(0)
            st.download_button(
                label=t["telecharger"],
                data=buf,
                file_name=f"profil_{joueur_profil.replace(' ', '_')}.png",
                mime="image/png",
                key="profil_download"
            )
    else:
        st.info(t["aucun_joueur"])

# ============================================================
# ONGLET 4 — SHORTLIST
# ============================================================

with tab4:
    st.header(t["header_shortlist"])

    col1, col2, col3 = st.columns(3)
    with col1:
        profil_short = st.selectbox(
            t["profil"], list(PROFILS.keys()),
            format_func=lambda x: PROFILS[x],
            key="short_profil"
        )
    with col2:
        top_n = st.slider(t["joueurs_categorie"], 3, 15, 5, key="short_topn")
    with col3:
        ligue_short = st.selectbox(
            t["ligue"], [t["toutes"]] + sorted(
                df_final["ligue"].dropna().unique().tolist()
            ), key="short_ligue"
        )

    col4, col5, col6, col7 = st.columns(4)
    with col4:
        max_age_short = st.slider(t["age_max"], 18, 40, 32, key="short_age")
    with col5:
        min_min_short = st.slider(t["minutes_min"], 0, 3000, 500, 100,
                                  key="short_min")
    with col6:
        max_valeur_short = st.slider(t["valeur_max"], 0, 50, 50,
                                     key="short_valeur") \
            if "valeur_marchande" in df_final.columns else 50
    with col7:
        if "contrat" in df_final.columns:
            annees_short = sorted(
                df_final["contrat"].dropna().astype(str)
                .str.extract(r"(20\d{2})")[0].dropna().unique().tolist()
            )
            max_contrat_short = st.selectbox(
                t["contrat"],
                [t["tous"]] + annees_short,
                key="short_contrat"
            )
        else:
            max_contrat_short = t["tous"]

    st.markdown("---")

    df_short = df_final.copy()
    if ligue_short != t["toutes"]:
        df_short = df_short[df_short["ligue"] == ligue_short]
    df_short = df_short[df_short["minutes"] >= min_min_short]
    if "age" in df_short.columns:
        df_short = df_short[
            pd.to_numeric(df_short["age"], errors="coerce") <= max_age_short
        ]
    if "valeur_marchande" in df_short.columns and max_valeur_short < 50:
        df_short = df_short[
            pd.to_numeric(df_short["valeur_marchande"],
                          errors="coerce").fillna(0) <= max_valeur_short * 1_000_000
        ]
    if max_contrat_short != t["tous"] and "contrat" in df_short.columns:
        def get_year_short(val):
            if pd.isna(val): return 9999
            m = re.search(r"(20\d{2})", str(val))
            return int(m.group(1)) if m else 9999
        df_short = df_short[
            df_short["contrat"].apply(get_year_short) <= int(max_contrat_short)
        ]

    for fiab, titre, emoji in [
        ("titulaire",          t["profils_surs"], "🟢"),
        ("rotation",           t["rotation"],     "🟡"),
        ("echantillon_moyen",  t["potentiel"],    "🟠"),
        ("faible_echantillon", t["paris"],        "🔴"),
    ]:
        sub = (df_short[df_short["niveau_fiabilite"] == fiab]
               .sort_values(profil_short, ascending=False)
               .head(top_n))
        if sub.empty:
            continue

        st.subheader(f"{emoji} {titre}")

        cols_s = ["joueur", "equipe_norm", "ligue", "age",
                  "valeur_marchande", "contrat", "minutes",
                  profil_short, "impact_contexte"]
        cols_s   = [c for c in cols_s if c in sub.columns]
        sub_disp = sub[cols_s].copy()
        sub_disp[profil_short]      = sub_disp[profil_short].round(1)
        sub_disp["impact_contexte"] = (sub_disp["impact_contexte"] * 100).round(1)
        if "valeur_marchande" in sub_disp.columns:
            sub_disp["valeur_marchande"] = (
                pd.to_numeric(sub_disp["valeur_marchande"], errors="coerce")
                / 1_000_000
            ).round(1)

        sub_disp = sub_disp.rename(columns={
            "joueur":           t["joueur"],
            "equipe_norm":      t["equipe"],
            "ligue":            "Liga" if lang == "es" else "Ligue",
            "age":              t["age"],
            "valeur_marchande": t["valeur"],
            "contrat":          "Contrato" if lang == "es" else "Contrat",
            "minutes":          t["minutes"],
            profil_short:       t["score"],
            "impact_contexte":  t["impact"],
        })

        st.dataframe(
            sub_disp, use_container_width=True, hide_index=True,
            column_config={
                t["score"]: st.column_config.ProgressColumn(
                    t["score"], min_value=0, max_value=100, format="%.1f"
                ),
                t["valeur"]: st.column_config.NumberColumn(
                    t["valeur"], format="%.1fM€"
                ),
                t["impact"]: st.column_config.NumberColumn(
                    t["impact"], format="%.1f%%"
                ),
            }
        )

# ============================================================
# ONGLET 5 — MÉTHODOLOGIE
# ============================================================

with tab5:
    st.header(t["header_methodo"])

    if lang == "fr":
        st.markdown("""
        Outil de scouting contextuel pour les milieux centraux sur 4 ligues
        (L1, L2, Liga, Liga Segunda — saison 2025/2026).
        Source des données : **Hudl Wyscout**. Développé en Python par Tom Hamel.
        """)

        st.markdown("---")
        st.subheader("🏗️ Architecture du modèle — 4 niveaux")
        st.markdown("""
        **Niveau 1** — Chaque équipe est profilée sur 4 dimensions tactiques (scores 0-100, normalisés intra-ligue)

        **Niveau 2** — Les stats individuelles des joueurs sont normalisées en percentiles intra-ligue

        **Niveau 3** — Les stats sont ajustées selon le style de jeu de l'équipe du joueur (ajustement contextuel progressif ±30%)

        **Niveau 4** — Les stats ajustées sont re-normalisées en percentiles inter-ligues pour obtenir les scores finaux comparables sur l'ensemble du pool
        """)

        st.markdown("---")
        st.subheader("🧩 Niveau 1 — Style de jeu équipe")
        st.markdown("#### 🛡️ Bloc défensif")
        st.markdown("""
        Mesure la hauteur du bloc — où l'équipe récupère le ballon.

        | Métrique | Poids | Source |
        |---|---|---|
        | Récupérations zone haute | 50% | Wyscout |
        | Récupérations zone médiane | 30% | Wyscout |
        | Récupérations zone basse (inversé) | 20% | Wyscout |

        **Labels :** Bloc haut (≥66) · Bloc médian (33–66) · Bloc bas (<33)
        """)

        st.markdown("#### ⚡ Pressing")
        st.markdown("""
        | Métrique | Poids | Source |
        |---|---|---|
        | PPDA (inversé) | 40% | Wyscout |
        | Tacles | 25% | Wyscout |
        | Interceptions | 25% | Wyscout |
        | Duels défensifs | 10% | Wyscout |

        **Labels :** Pressing intensif (≥66) · Pressing modéré (33–66) · Bloc passif (<33)
        """)

        st.markdown("#### ⚽ Avec ballon")
        st.markdown("""
        | Métrique | Poids | Source |
        |---|---|---|
        | Possession % | 30% | Wyscout |
        | Passes progressives | 30% | Wyscout |
        | % passes longues (inversé) | 25% | Wyscout |
        | Passes dans le tiers adverse | 15% | Wyscout |

        **Labels :** Possession (≥66) · Équilibré (33–66) · Jeu direct (<33)
        """)

        st.markdown("#### 🔄 Transition offensive")
        st.markdown("""
        | Métrique | Poids | Source |
        |---|---|---|
        | Contre-attaques | 60% | Wyscout |
        | Passes en profondeur terminées | 40% | Wyscout |

        **Labels :** Contre-attaquant (≥66) · Mixte (33–66) · Jeu placé (<33)
        """)

        st.markdown("---")
        st.subheader("🎯 Niveau 3 — Ajustement contextuel")
        st.markdown("""
        | Stats joueur | Corrigées par | Logique |
        |---|---|---|
        | Défensives | Score pressing | Un pressing fort gonfle les stats défensives |
        | Passes | Score avec ballon | Un jeu de possession gonfle les stats de passes |
        | Transition | Score transition | Une équipe qui contre gonfle les stats de transition |

        **Amplitude de correction progressive ±30%**
        """)

        st.markdown("---")
        st.subheader("📊 Impact contexte")
        st.markdown("""
        - **Positif (+%)** → joueur **sous-coté** par son système
        - **Négatif (-%)** → joueur **favorisé** par son système
        """)

        st.markdown("---")
        st.subheader("👤 Profils MC — 6 profils")
        st.markdown("""
        | Profil | Description | Pondération principale |
        |---|---|---|
        | **MC Récupérateur** | Défend, récupère, relance simple | Défensif 55% + Pressing 25% + Passes 20% |
        | **MC Défensif pur** | Défend, donne simple, peu de risques | Défensif 65% + Pressing 25% + Passes % 10% |
        | **MC Relanceur** | Relance et fait progresser le jeu | Passes 55% + Défensif 20% + Offensif 25% |
        | **MC Box to Box** | Équilibré sur toutes les dimensions | Défensif 30% + Passes 30% + Transition 20% + Offensif 20% |
        | **MC Intérieur** | Passes entre les lignes, dribbles, xA | Passes pénétrantes 50% + Passes 30% + Transition 20% |
        | **MC Offensif** | Création de danger, xG, xA | Offensif 55% + Passes 25% + Transition 20% |
        """)

        st.markdown("---")
        st.subheader("⚠️ Limites du modèle")
        st.markdown("""
        - Correction linéaire — relation proportionnelle assumée
        - Pondérations définies manuellement
        - Même facteur appliqué à tous les joueurs d'une équipe
        - Données statiques
        """)

    else:
        st.markdown("""
        Herramienta de scouting contextual para mediocampistas centrales en 4 ligas
        (L1, L2, Liga, Liga Segunda — temporada 2025/2026).
        Fuente de datos : **Hudl Wyscout**. Desarrollado en Python por Tom Hamel.
        """)

        st.markdown("---")
        st.subheader("🏗️ Arquitectura del modelo — 4 niveles")
        st.markdown("""
        **Nivel 1** — Cada equipo es perfilado en 4 dimensiones tácticas (puntuaciones 0-100, normalizadas intra-liga)

        **Nivel 2** — Las estadísticas individuales de los jugadores se normalizan en percentiles intra-liga

        **Nivel 3** — Las estadísticas se ajustan según el estilo de juego del equipo del jugador (ajuste contextual progresivo ±30%)

        **Nivel 4** — Las estadísticas ajustadas se re-normalizan en percentiles inter-ligas para obtener las puntuaciones finales comparables en todo el pool
        """)

        st.markdown("---")
        st.subheader("🧩 Nivel 1 — Estilo de juego del equipo")
        st.markdown("#### 🛡️ Bloque defensivo")
        st.markdown("""
        Mide la altura del bloque — dónde el equipo recupera el balón.

        | Métrica | Peso | Fuente |
        |---|---|---|
        | Recuperaciones zona alta | 50% | Wyscout |
        | Recuperaciones zona media | 30% | Wyscout |
        | Recuperaciones zona baja (invertido) | 20% | Wyscout |

        **Etiquetas :** Bloque alto (≥66) · Bloque medio (33–66) · Bloque bajo (<33)
        """)

        st.markdown("#### ⚡ Pressing")
        st.markdown("""
        | Métrica | Peso | Fuente |
        |---|---|---|
        | PPDA (invertido) | 40% | Wyscout |
        | Tacles | 25% | Wyscout |
        | Interceptaciones | 25% | Wyscout |
        | Duelos defensivos | 10% | Wyscout |

        **Etiquetas :** Pressing intensivo (≥66) · Pressing moderado (33–66) · Bloque pasivo (<33)
        """)

        st.markdown("#### ⚽ Con balón")
        st.markdown("""
        | Métrica | Peso | Fuente |
        |---|---|---|
        | Posesión % | 30% | Wyscout |
        | Pases progresivos | 30% | Wyscout |
        | % pases largos (invertido) | 25% | Wyscout |
        | Pases al tercio rival | 15% | Wyscout |

        **Etiquetas :** Posesión (≥66) · Equilibrado (33–66) · Juego directo (<33)
        """)

        st.markdown("#### 🔄 Transición ofensiva")
        st.markdown("""
        | Métrica | Peso | Fuente |
        |---|---|---|
        | Contraataques | 60% | Wyscout |
        | Pases en profundidad completados | 40% | Wyscout |

        **Etiquetas :** Contraatacante (≥66) · Mixto (33–66) · Juego posicional (<33)
        """)

        st.markdown("---")
        st.subheader("🎯 Nivel 3 — Ajuste contextual")
        st.markdown("""
        | Estadísticas jugador | Corregidas por | Lógica |
        |---|---|---|
        | Defensivas | Puntuación pressing | Un pressing fuerte infla las estadísticas defensivas |
        | Pases | Puntuación con balón | Un juego de posesión infla las estadísticas de pases |
        | Transición | Puntuación transición | Un equipo que contraataca infla las estadísticas de transición |

        **Amplitud de corrección progresiva ±30%**
        """)

        st.markdown("---")
        st.subheader("📊 Impacto contexto")
        st.markdown("""
        - **Positivo (+%)** → jugador **infravalorado** por su sistema
        - **Negativo (-%)** → jugador **favorecido** por su sistema
        """)

        st.markdown("---")
        st.subheader("👤 Perfiles MC — 6 perfiles")
        st.markdown("""
        | Perfil | Descripción | Ponderación principal |
        |---|---|---|
        | **MC Recuperador** | Defiende, recupera, relanza simple | Defensivo 55% + Pressing 25% + Pases 20% |
        | **MC Defensivo puro** | Defiende, da simple, pocos riesgos | Defensivo 65% + Pressing 25% + Pases % 10% |
        | **MC Relanzador** | Relanza y hace progresar el juego | Pases 55% + Defensivo 20% + Ofensivo 25% |
        | **MC Box to Box** | Equilibrado en todas las dimensiones | Defensivo 30% + Pases 30% + Transición 20% + Ofensivo 20% |
        | **MC Interior** | Pases entre líneas, regates, xA | Pases penetrantes 50% + Pases 30% + Transición 20% |
        | **MC Ofensivo** | Creación de peligro, xG, xA | Ofensivo 55% + Pases 25% + Transición 20% |
        """)

        st.markdown("---")
        st.subheader("⚠️ Limitaciones del modelo")
        st.markdown("""
        - Corrección lineal — relación proporcional asumida
        - Ponderaciones definidas manualmente
        - Mismo factor aplicado a todos los jugadores de un equipo
        - Datos estáticos
        """)

    st.markdown("---")
    st.caption(t["footer"])

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")
st.markdown(
    f"<div style='text-align:center; color:grey; font-size:12px'>{t['footer']}</div>",
    unsafe_allow_html=True
)
