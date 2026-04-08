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

PROFILS = {
    "score_mc_recuperateur": "MC Récupérateur",
    "score_mc_mdef":         "MC Défensif pur",
    "score_mc_relanceur":    "MC Relanceur",
    "score_mc_boxtbox":      "MC Box to Box",
    "score_mc_interieur":    "MC Intérieur",
    "score_mc_offensif":     "MC Offensif",
}

TOOLTIPS = {
    "Score profil": (
        "Score de 0 à 100 mesurant l'adéquation du joueur avec le profil "
        "sélectionné. Calculé sur les stats ajustées au contexte de son équipe, "
        "normalisées inter-ligues. 100 = meilleur profil toutes ligues confondues."
    ),
    "Impact contexte": (
        "Mesure si les stats du joueur sont gonflées ou dévalorisées par le style "
        "de jeu de son équipe. Positif = joueur sous-coté par son système. "
        "Négatif = joueur favorisé par son système."
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

st.sidebar.title("⚽ MC Scouting")
st.sidebar.markdown("*Scouting contextuel multi-ligues*")
st.sidebar.markdown("---")

mode = st.sidebar.radio(
    "Mode de données",
    ["🎯 Démo (données pré-calculées)", "📁 Custom (mes exports Wyscout)"]
)

df_final        = None
df_players_norm = None

if mode == "🎯 Démo (données pré-calculées)":
    if os.path.exists(DEMO_PATH):
        df_final        = load_demo()
        df_players_norm = load_players_norm()
        st.sidebar.success(f"✅ {len(df_final)} joueurs chargés")
    else:
        st.sidebar.error("❌ Fichier démo introuvable")
        st.stop()
else:
    st.sidebar.markdown("### Fichiers équipes")
    uploaded_equipes = {}
    for ligue in ["L1", "L2", "Liga", "Liga_seg"]:
        files = st.sidebar.file_uploader(
            f"Équipes {ligue}", type=["xlsx"],
            accept_multiple_files=True, key=f"eq_{ligue}"
        )
        if files:
            uploaded_equipes[ligue] = files

    st.sidebar.markdown("### Fichiers joueurs")
    uploaded_joueurs = {}
    for ligue in ["L1", "L2", "Liga", "Liga_seg"]:
        file = st.sidebar.file_uploader(
            f"Joueurs {ligue}", type=["xlsx"], key=f"j_{ligue}"
        )
        if file:
            uploaded_joueurs[ligue] = file

    if uploaded_equipes and uploaded_joueurs:
        with st.spinner("Calcul du pipeline en cours..."):
            try:
                from pipeline import load_teams, load_players
                from modele import normaliser_equipes, build_df_final
                df_teams   = load_teams(uploaded_equipes)
                df_norm    = normaliser_equipes(df_teams)
                df_players = load_players(uploaded_joueurs)
                df_final   = build_df_final(df_players, df_norm)
                st.sidebar.success(f"✅ {len(df_final)} joueurs traités")
            except Exception as e:
                st.sidebar.error(f"❌ Erreur : {e}")
                st.stop()
    else:
        st.info("👈 Upload tes fichiers Wyscout dans la sidebar pour commencer.")
        st.stop()

# ============================================================
# ONGLETS
# ============================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 Scouting",
    "🗺️ Cartographie",
    "📊 Profil joueur",
    "📋 Shortlist",
    "📖 Méthodologie",
])

# ============================================================
# ONGLET 1 — SCOUTING
# ============================================================

with tab1:
    st.header("🔍 Scouting contextuel")

    col1, col2, col3 = st.columns(3)
    with col1:
        ligues_dispo = ["Toutes"] + sorted(
            df_final["ligue"].dropna().unique().tolist()
        )
        ligue_filtre = st.selectbox("Ligue", ligues_dispo, key="scout_ligue")
    with col2:
        profil = st.selectbox(
            "Profil MC", list(PROFILS.keys()),
            format_func=lambda x: PROFILS[x], key="scout_profil"
        )
    with col3:
        min_minutes = st.slider("Minutes min.", 0, 3000, 500, 100,
                                key="scout_min")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        max_age = st.slider("Âge max.", 18, 40, 32, key="scout_age")
    with col_b:
        max_valeur = st.slider("Valeur marchande max (M€)", 0, 50, 50,
                               key="scout_valeur") \
            if "valeur_marchande" in df_final.columns else 50
    with col_c:
        if "contrat" in df_final.columns:
            annees_dispo = sorted(
                df_final["contrat"].dropna().astype(str)
                .str.extract(r"(20\d{2})")[0].dropna().unique().tolist()
            )
            max_contrat = st.selectbox("Contrat expire avant",
                                       ["Tous"] + annees_dispo,
                                       key="scout_contrat")
        else:
            max_contrat = "Tous"

    fiabilite = st.multiselect(
        "Fiabilité",
        ["titulaire", "rotation", "echantillon_moyen", "faible_echantillon"],
        default=["titulaire", "rotation", "echantillon_moyen"],
        key="scout_fiabilite"
    )

    st.markdown("---")

    # Filtrage
    df_filtered = df_final.copy()
    if ligue_filtre != "Toutes":
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
    if max_contrat != "Tous" and "contrat" in df_filtered.columns:
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

    st.markdown(f"**{len(df_filtered)} joueurs** correspondent aux critères")

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
        "joueur":           "Joueur",
        "equipe_norm":      "Équipe",
        "ligue":            "Ligue",
        "age":              "Âge",
        "valeur_marchande": "Valeur (M€)",
        "contrat":          "Contrat",
        "minutes":          "Minutes",
        "niveau_fiabilite": "Fiabilité",
        profil:             "Score profil",
        "impact_contexte":  "Impact (%)",
    })

    st.dataframe(
        df_display, use_container_width=True, hide_index=True,
        column_config={
            "Score profil": st.column_config.ProgressColumn(
                "Score profil", help=TOOLTIPS["Score profil"],
                min_value=0, max_value=100, format="%.1f"
            ),
            "Impact (%)": st.column_config.NumberColumn(
                "Impact (%)", help=TOOLTIPS["Impact contexte"],
                format="%.1f%%"
            ),
            "Valeur (M€)": st.column_config.NumberColumn(
                "Valeur (M€)", format="%.1fM€"
            ),
        }
    )

    st.markdown("---")
    st.subheader("📡 Rapport scouting — Radar")
    joueurs_dispo = df_filtered["joueur"].dropna().unique().tolist()
    if joueurs_dispo:
        joueur_sel = st.selectbox("Sélectionne un joueur", joueurs_dispo,
                                  key="scout_joueur")
        if joueur_sel:
            fig = radar_joueur(joueur_sel, df_final, df_players_norm)
            if fig:
                st.pyplot(fig)
    else:
        st.info("Aucun joueur ne correspond aux filtres.")

# ============================================================
# ONGLET 2 — CARTOGRAPHIE
# ============================================================

with tab2:
    st.header("🗺️ Cartographie des MC")

    PROFILS_LABELS = {
        "score_mc_recuperateur": "Récupérateur",
        "score_mc_mdef":         "Défensif pur",
        "score_mc_relanceur":    "Relanceur",
        "score_mc_boxtbox":      "Box to Box",
        "score_mc_interieur":    "Intérieur",
        "score_mc_offensif":     "Offensif",
    }

    col1, col2, col3 = st.columns(3)
    with col1:
        axe_x = st.selectbox(
            "Axe X", list(PROFILS_LABELS.keys()),
            format_func=lambda x: PROFILS_LABELS[x],
            index=0, key="carto_x"
        )
    with col2:
        axe_y = st.selectbox(
            "Axe Y", list(PROFILS_LABELS.keys()),
            format_func=lambda x: PROFILS_LABELS[x],
            index=2, key="carto_y"
        )
    with col3:
        min_min_carto = st.slider("Minutes min.", 0, 3000, 500, 100,
                                  key="carto_min")

    col4, col5 = st.columns(2)
    with col4:
        ligue_carto = st.selectbox(
            "Ligue",
            ["Toutes"] + sorted(df_final["ligue"].dropna().unique().tolist()),
            key="carto_ligue"
        )
    with col5:
        max_age_carto = st.slider("Âge max.", 18, 40, 40, key="carto_age")

    df_carto = df_final[df_final["minutes"] >= min_min_carto].copy()
    if ligue_carto != "Toutes":
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
    st.header("📊 Profil joueur")

    col1, col2 = st.columns(2)
    with col1:
        ligue_profil = st.selectbox(
            "Ligue",
            ["Toutes"] + sorted(df_final["ligue"].dropna().unique().tolist()),
            key="profil_ligue"
        )
    with col2:
        min_min_profil = st.slider("Minutes min.", 0, 3000, 500, 100,
                                   key="profil_min")

    df_profil = df_final[df_final["minutes"] >= min_min_profil].copy()
    if ligue_profil != "Toutes":
        df_profil = df_profil[df_profil["ligue"] == ligue_profil]

    joueurs_profil = sorted(df_profil["joueur"].dropna().unique().tolist())

    if joueurs_profil:
        joueur_profil = st.selectbox(
            "Sélectionne un joueur", joueurs_profil, key="profil_joueur"
        )

        viz_type = st.radio(
            "Visualisation",
            ["Radar (brut vs ajusté)", "Pizza chart (détail métriques)"],
            horizontal=True,
            key="profil_viz"
        )

        if viz_type == "Radar (brut vs ajusté)":
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
                label="⬇️ Télécharger",
                data=buf,
                file_name=f"profil_{joueur_profil.replace(' ', '_')}.png",
                mime="image/png",
                key="profil_download"
            )
    else:
        st.info("Aucun joueur ne correspond aux filtres.")

# ============================================================
# ONGLET 4 — SHORTLIST
# ============================================================

with tab4:
    st.header("📋 Shortlist Recrutement")

    col1, col2, col3 = st.columns(3)
    with col1:
        profil_short = st.selectbox(
            "Profil", list(PROFILS.keys()),
            format_func=lambda x: PROFILS[x],
            key="short_profil"
        )
    with col2:
        top_n = st.slider("Joueurs par catégorie", 3, 15, 5, key="short_topn")
    with col3:
        ligue_short = st.selectbox(
            "Ligue", ["Toutes"] + sorted(
                df_final["ligue"].dropna().unique().tolist()
            ), key="short_ligue"
        )

    col4, col5, col6, col7 = st.columns(4)
    with col4:
        max_age_short = st.slider("Âge max.", 18, 40, 32, key="short_age")
    with col5:
        min_min_short = st.slider("Minutes min.", 0, 3000, 500, 100,
                                  key="short_min")
    with col6:
        max_valeur_short = st.slider("Valeur max (M€)", 0, 50, 50,
                                     key="short_valeur") \
            if "valeur_marchande" in df_final.columns else 50
    with col7:
        if "contrat" in df_final.columns:
            annees_short = sorted(
                df_final["contrat"].dropna().astype(str)
                .str.extract(r"(20\d{2})")[0].dropna().unique().tolist()
            )
            max_contrat_short = st.selectbox(
                "Contrat expire avant",
                ["Tous"] + annees_short,
                key="short_contrat"
            )
        else:
            max_contrat_short = "Tous"

    st.markdown("---")

    df_short = df_final.copy()
    if ligue_short != "Toutes":
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
    if max_contrat_short != "Tous" and "contrat" in df_short.columns:
        def get_year_short(val):
            if pd.isna(val): return 9999
            m = re.search(r"(20\d{2})", str(val))
            return int(m.group(1)) if m else 9999
        df_short = df_short[
            df_short["contrat"].apply(get_year_short) <= int(max_contrat_short)
        ]

    for fiab, titre, emoji in [
        ("titulaire",          "Profils sûrs — Titulaires", "🟢"),
        ("rotation",           "Rotation fiable",           "🟡"),
        ("echantillon_moyen",  "Potentiel",                 "🟠"),
        ("faible_echantillon", "Paris / Upside",            "🔴"),
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
            "joueur":           "Joueur",
            "equipe_norm":      "Équipe",
            "ligue":            "Ligue",
            "age":              "Âge",
            "valeur_marchande": "Valeur (M€)",
            "contrat":          "Contrat",
            "minutes":          "Minutes",
            profil_short:       "Score",
            "impact_contexte":  "Impact (%)",
        })

        st.dataframe(
            sub_disp, use_container_width=True, hide_index=True,
            column_config={
                "Score": st.column_config.ProgressColumn(
                    "Score", min_value=0, max_value=100, format="%.1f"
                ),
                "Valeur (M€)": st.column_config.NumberColumn(
                    "Valeur (M€)", format="%.1fM€"
                ),
                "Impact (%)": st.column_config.NumberColumn(
                    "Impact (%)", format="%.1f%%"
                ),
            }
        )

# ============================================================
# ONGLET 5 — MÉTHODOLOGIE
# ============================================================

with tab5:
    st.header("📖 Méthodologie")

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
    Mesure l'intensité du pressing défensif.

    | Métrique | Poids | Source |
    |---|---|---|
    | PPDA — passes autorisées par action défensive (inversé) | 40% | Wyscout |
    | Tacles | 25% | Wyscout |
    | Interceptions | 25% | Wyscout |
    | Duels défensifs | 10% | Wyscout |

    **Logique :** un PPDA bas = pressing intense. Il est inversé pour que score élevé = pressing fort.

    **Labels :** Pressing intensif (≥66) · Pressing modéré (33–66) · Bloc passif (<33)
    """)

    st.markdown("#### ⚽ Avec ballon")
    st.markdown("""
    Mesure le style de jeu offensif — possession vs jeu direct.

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
    Mesure la fréquence des transitions offensives — pas leur efficacité.

    | Métrique | Poids | Source |
    |---|---|---|
    | Contre-attaques | 60% | Wyscout |
    | Passes en profondeur terminées | 40% | Wyscout |

    **Labels :** Contre-attaquant (≥66) · Mixte (33–66) · Jeu placé (<33)
    """)

    st.markdown("---")
    st.subheader("🎯 Niveau 3 — Ajustement contextuel")
    st.markdown("""
    Chaque stat individuelle est corrigée selon le style de l'équipe du joueur.

    | Stats joueur | Corrigées par | Logique |
    |---|---|---|
    | Défensives (duels, tacles, interceptions) | Score pressing | Un pressing fort gonfle les stats défensives |
    | Passes (volume, précision, progressives) | Score avec ballon | Un jeu de possession gonfle les stats de passes |
    | Transition (courses, accélérations, dribbles) | Score transition | Une équipe qui contre gonfle les stats de transition |

    **Amplitude de correction progressive ±30%** — réduite aux extrêmes pour éviter les sur-corrections.
    Exemple : PSG score avec ballon 100/100 → correction réduite à -15% au lieu de -30%.
    """)

    st.markdown("---")
    st.subheader("📊 Impact contexte")
    st.markdown("""
    Moyenne des deltas brut→ajusté sur 4 métriques : interceptions, tacles, passes progressives, précision passes.

    - **Positif (+%)** → joueur **sous-coté** par son système
    - **Négatif (-%)** → joueur **favorisé** par son système

    *Exemple : I. Fofana (Amiens SC, L2) — +18% — bloc bas avec peu de possession,
    ses stats défensives sont mécaniquement tirées vers le bas.*
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
    | **MC Intérieur** | Passes entre les lignes, dribbles, xA | Passes pénétrantes/judicieuses/xA 50% + Passes 30% + Transition 20% |
    | **MC Offensif** | Création de danger, xG, xA | Offensif 55% + Passes 25% + Transition 20% |
    """)

    st.markdown("---")
    st.subheader("📈 Visualisations")
    st.markdown("""
    - **Radar brut vs ajusté** — percentiles intra-ligue (gris) vs inter-ligues ajustés (bleu)
    - **Pizza chart** — 17 métriques en percentiles inter-ligues ajustés, par dimension
    - **Cartographie MC** — scatter plot interactif, axes dynamiques parmi les 6 profils
    """)

    st.markdown("---")
    st.subheader("⚠️ Limites du modèle")
    st.markdown("""
    - Correction linéaire — relation proportionnelle assumée entre style équipe et stats individuelles
    - Pondérations définies manuellement, pas optimisées mathématiquement
    - Même facteur appliqué à tous les joueurs d'une équipe quel que soit leur rôle précis
    - Données statiques — ne reflètent pas les changements de système en cours de saison
    """)

    st.markdown("---")
    st.caption(
        "Données : Hudl Wyscout · Modèle : Tom Hamel · "
        "Scouting contextuel MC 2025/2026"
    )

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:grey; font-size:12px'>"
    "Data : Hudl Wyscout · Modèle : Tom Hamel · "
    "Scouting contextuel MC 2025/2026"
    "</div>",
    unsafe_allow_html=True
)