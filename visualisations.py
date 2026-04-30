# visualisations.py
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec
import plotly.graph_objects as go

# ============================================================
# RADAR — BRUT vs AJUSTÉ
# ============================================================

DIMENSIONS_RADAR = [
    ("Défense",       "actions_def_90",     "actions_def_90_adj_pct"),
    ("Duels déf.",    "duels_def_90",       "duels_def_90_adj_pct"),
    ("Tacles",        "tacles_padj",        "tacles_padj_adj_pct"),
    ("Interceptions", "interceptions_padj", "interceptions_padj_adj_pct"),
    ("Passes prog.",  "passes_prog_90",     "passes_prog_90_adj_pct"),
    ("Passes %",      "passes_pct",         "passes_pct_adj_pct"),
    ("Passes av.",    "passes_avant_90",    "passes_avant_90_adj_pct"),
    ("Courses prog.", "courses_prog_90",    "courses_prog_90_adj_pct"),
    ("xG",            "xg_90",              "xg_90_pct"),
    ("xA",            "xa_90",              "xa_90_pct"),
]

def radar_joueur(nom, df_final, df_players_norm=None, lang="fr"):
    row = df_final[df_final["joueur"] == nom]
    if row.empty:
        return None
    j = row.iloc[0]

    labels    = [d[0] for d in DIMENSIONS_RADAR]
    cols_brut = [d[1] for d in DIMENSIONS_RADAR]
    cols_adj  = [d[2] for d in DIMENSIONS_RADAR]

    vals_brut = []
    for col in cols_brut:
        if df_players_norm is not None and col in df_players_norm.columns:
            r = df_players_norm[df_players_norm["joueur"] == nom]
            v = float(r[col].iloc[0]) if not r.empty and pd.notna(r[col].iloc[0]) else 0
        else:
            v = 0
        vals_brut.append(v)

    vals_adj = [float(j[c]) if c in j and pd.notna(j[c]) else 0 for c in cols_adj]

    N      = len(labels)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]
    brut_plot = vals_brut + vals_brut[:1]
    adj_plot  = vals_adj  + vals_adj[:1]
    score_moy = round(np.mean(vals_adj), 1)

    fig = plt.figure(figsize=(16, 9))
    fig.patch.set_facecolor("#f8f9fa")
    gs  = GridSpec(1, 2, figure=fig, wspace=0.35)

    # ── Colonne gauche ───────────────────────────────────────
    ax_info = fig.add_subplot(gs[0, 0])
    ax_info.set_facecolor("#f8f9fa")
    ax_info.axis("off")

    ax_info.text(0.05, 0.95, nom,
                 fontsize=22, fontweight="bold", color="#2c3e50",
                 transform=ax_info.transAxes, va="top")
    ax_info.text(0.05, 0.88, f"{j['equipe_norm']}  ·  {j['ligue']}",
                 fontsize=13, color="#7f8c8d",
                 transform=ax_info.transAxes, va="top")
    ax_info.text(0.05, 0.83, f"{int(j['minutes'])} min  ·  {j['niveau_fiabilite']}",
                 fontsize=11, color="#95a5a6",
                 transform=ax_info.transAxes, va="top")

    ax_info.plot([0.05, 0.95], [0.79, 0.79], color="#2c3e50",
                 linewidth=1.5, alpha=0.3, transform=ax_info.transAxes)

    # Contexte équipe
    ax_info.text(0.05, 0.75,
                 "CONTEXTE ÉQUIPE" if lang == "fr" else "CONTEXTO EQUIPO",
                 fontsize=10, fontweight="bold", color="#2c3e50",
                 transform=ax_info.transAxes, va="top")

    ctx_descriptions = {
        "label_bloc": {
            "Bloc haut":   "Récupère haut — pressing dans le camp adverse" if lang == "fr" else "Recupera alto — pressing en campo rival",
            "Bloc médian": "Récupère en zone médiane" if lang == "fr" else "Recupera en zona media",
            "Bloc bas":    "Récupère bas — défend dans son camp" if lang == "fr" else "Recupera bajo — defiende en su campo",
        },
        "label_pressing": {
            "Pressing intensif": "Presse intensément après perte de balle" if lang == "fr" else "Presiona intensamente tras pérdida",
            "Pressing modéré":   "Pressing modéré — équipe équilibrée" if lang == "fr" else "Pressing moderado — equipo equilibrado",
            "Bloc passif":       "Peu de pressing — équipe passive défensivement" if lang == "fr" else "Poco pressing — equipo pasivo defensivamente",
        },
        "label_avec_ballon": {
            "Possession": "Jeu de possession — construction élaborée" if lang == "fr" else "Juego de posesión — construcción elaborada",
            "Équilibré":  "Style de jeu équilibré" if lang == "fr" else "Estilo de juego equilibrado",
            "Jeu direct": "Jeu direct — peu de construction depuis l'arrière" if lang == "fr" else "Juego directo — poca construcción desde atrás",
        },
        "label_transition_off": {
            "Contre-attaque": "Équipe qui cherche à contre-attaquer" if lang == "fr" else "Equipo que busca el contraataque",
            "Mixte":          "Transitions offensives modérées" if lang == "fr" else "Transiciones ofensivas moderadas",
            "Jeu placé":      "Peu de transitions — attaque en bloc organisé" if lang == "fr" else "Pocas transiciones — ataque en bloque organizado",
        },
    }

    ctx_labels = [
        ("Bloc",        "label_bloc"),
        ("Pressing",    "label_pressing"),
        ("Avec ballon" if lang == "fr" else "Con balón", "label_avec_ballon"),
        ("Transition",  "label_transition_off"),
    ]

    for i, (label, label_col) in enumerate(ctx_labels):
        y = 0.69 - i * 0.065
        val         = j[label_col] if label_col in j and pd.notna(j[label_col]) else "—"
        description = ctx_descriptions.get(label_col, {}).get(val, val)
        ax_info.text(0.05, y, label,
                     fontsize=8.5, color="#7f8c8d",
                     transform=ax_info.transAxes, va="top")
        ax_info.text(0.05, y - 0.030, description,
                     fontsize=9, fontweight="bold", color="#2c3e50",
                     transform=ax_info.transAxes, va="top")

    ax_info.plot([0.05, 0.95], [0.43, 0.43], color="#2c3e50",
                 linewidth=1.5, alpha=0.3, transform=ax_info.transAxes)

    # Impact contexte
    impact = round(j["impact_contexte"] * 100, 1)
    color  = "#27ae60" if impact >= 0 else "#e74c3c"
    label  = ("sous-coté par son système" if impact >= 0 else "favorisé par son système") if lang == "fr" else ("infravalorado por su sistema" if impact >= 0 else "favorecido por su sistema")

    ax_info.text(0.05, 0.40,
                 "IMPACT CONTEXTE" if lang == "fr" else "IMPACTO CONTEXTO",
                 fontsize=10, fontweight="bold", color="#2c3e50",
                 transform=ax_info.transAxes, va="top")
    ax_info.text(0.05, 0.33, f"{impact:+.1f}%  —  {label}",
                 fontsize=11, fontweight="bold", color=color,
                 transform=ax_info.transAxes, va="top")

    ax_info.plot([0.05, 0.95], [0.26, 0.26], color="#2c3e50",
                 linewidth=1.5, alpha=0.3, transform=ax_info.transAxes)

    # Scores profils
    ax_info.text(0.05, 0.23,
                 "SCORES PROFILS MC" if lang == "fr" else "PUNTUACIONES PERFILES MC",
                 fontsize=10, fontweight="bold", color="#2c3e50",
                 transform=ax_info.transAxes, va="top")

    profil_labels = [
        ("Récupérateur" if lang == "fr" else "Recuperador", "score_mc_recuperateur"),
        ("Relanceur"    if lang == "fr" else "Relanzador",   "score_mc_relanceur"),
        ("Box to Box",                                        "score_mc_boxtbox"),
        ("Intérieur"    if lang == "fr" else "Interior",     "score_mc_interieur"),
        ("Offensif"     if lang == "fr" else "Ofensivo",     "score_mc_offensif"),
    ]
    for i, (label, col) in enumerate(profil_labels):
        y     = 0.19 - i * 0.044
        score = round(j[col], 1) if col in j and pd.notna(j[col]) else 0
        color = "#2ecc71" if score >= 66 else "#f39c12" if score >= 33 else "#e74c3c"
        ax_info.barh(y, score / 100 * 0.6, height=0.030, left=0.30,
                     color=color, alpha=0.7, transform=ax_info.transAxes)
        ax_info.text(0.05, y + 0.010, label,
                     fontsize=8.5, color="#2c3e50",
                     transform=ax_info.transAxes, va="center")
        ax_info.text(0.93, y + 0.010, f"{score}",
                     fontsize=9, fontweight="bold", color="#2c3e50",
                     transform=ax_info.transAxes, va="center", ha="right")

    # ── Colonne droite — Radar ───────────────────────────────
    ax_radar = fig.add_subplot(gs[0, 1], polar=True)

    ax_radar.fill(angles, [100] * (N + 1), color="#2ecc71", alpha=0.08)
    ax_radar.fill(angles, [70]  * (N + 1), color="#f39c12", alpha=0.12)
    ax_radar.fill(angles, [40]  * (N + 1), color="#e74c3c", alpha=0.12)

    ax_radar.set_yticks([20, 40, 60, 80, 100])
    ax_radar.set_yticklabels(["20", "40", "60", "80", "100"],
                              fontsize=7, color="grey")
    ax_radar.set_ylim(0, 100)
    ax_radar.set_xticks(angles[:-1])
    ax_radar.set_xticklabels(labels, fontsize=10, fontweight="bold")
    ax_radar.grid(color="grey", linestyle="--", linewidth=0.5, alpha=0.5)

    ax_radar.plot(angles, brut_plot, color="#95a5a6",
                  linewidth=1.5, linestyle="--", alpha=0.7)
    ax_radar.fill(angles, brut_plot, color="#95a5a6", alpha=0.10)

    ax_radar.plot(angles, adj_plot, color="#2c3e50", linewidth=2.5)
    ax_radar.fill(angles, adj_plot, color="#2c3e50", alpha=0.25)

    for angle, value in zip(angles[:-1], vals_adj):
        ax_radar.plot(angle, value, "o", color="#2c3e50", markersize=6)
        ax_radar.text(angle, value + 7, f"{round(value)}",
                      ha="center", fontsize=9,
                      fontweight="bold", color="#2c3e50")

    ax_radar.set_title(
        f"{'Profil MC contextualisé' if lang == 'fr' else 'Perfil MC contextualizado'}\n"
        f"{'Score moyen ajusté' if lang == 'fr' else 'Puntuación media ajustada'} : {score_moy}/100",
        fontsize=11, fontweight="bold", pad=15)

    patch_brut = mpatches.Patch(color="#95a5a6", alpha=0.7,
                                 label="Brut (intra-ligue)" if lang == "fr" else "Bruto (intra-liga)")
    patch_adj  = mpatches.Patch(color="#2c3e50", alpha=0.7,
                                 label="Ajusté (inter-ligues)" if lang == "fr" else "Ajustado (inter-ligas)")
    ax_radar.legend(handles=[patch_brut, patch_adj],
                    loc="upper right", bbox_to_anchor=(1.3, 1.15),
                    fontsize=9)

    fig.text(0.98, 0.01,
             "Data : Hudl Wyscout | Scouting contextuel MC" if lang == "fr" else "Data : Hudl Wyscout | Scouting contextual MC",
             ha="right", fontsize=8, alpha=0.6)
    plt.suptitle(f"{'Rapport Scouting' if lang == 'fr' else 'Informe Scouting'} — {nom}",
                 fontsize=14, fontweight="bold", y=1.02)

    return fig


# ============================================================
# CARTOGRAPHIE MC — SCATTER INTERACTIF (PLOTLY)
# ============================================================

def cartographie_mc(df, profil_x="score_mc_recuperateur",
                    profil_y="score_mc_relanceur",
                    label_x="Récupérateur", label_y="Relanceur",
                    lang="fr"):

    couleurs = {
        "L1":       "#2c3e50",
        "L2":       "#3498db",
        "Liga":     "#e74c3c",
        "Liga_seg": "#f39c12",
    }

    df = df.copy()
    df["taille"] = (df["minutes"] / df["minutes"].max() * 20 + 6).round(1)

    fig = go.Figure()

    for ligue in sorted(df["ligue"].dropna().unique()):
        sub = df[df["ligue"] == ligue]

        age_label     = "Âge" if lang == "fr" else "Edad"
        minutes_label = "Minutes" if lang == "fr" else "Minutos"
        impact_label  = "Impact contexte" if lang == "fr" else "Impacto contexto"

        hover = (
            "<b>" + sub["joueur"] + "</b><br>" +
            sub["equipe_norm"] + " · " + sub["ligue"] + "<br>" +
            age_label + " : " + sub["age"].astype(str) + "<br>" +
            minutes_label + " : " + sub["minutes"].astype(int).astype(str) + "<br>" +
            impact_label + " : " +
            (sub["impact_contexte"] * 100).round(1).astype(str) + "%<br>" +
            label_x + " : " + sub[profil_x].round(1).astype(str) + "<br>" +
            label_y + " : " + sub[profil_y].round(1).astype(str)
        )

        fig.add_trace(go.Scatter(
            x=sub[profil_x],
            y=sub[profil_y],
            mode="markers",
            name=ligue,
            marker=dict(
                size=sub["taille"],
                color=couleurs.get(ligue, "grey"),
                opacity=0.7,
                line=dict(width=0.5, color="white")
            ),
            hovertemplate=hover + "<extra></extra>",
        ))

    fig.add_hline(y=50, line_dash="dash", line_color="grey", opacity=0.4)
    fig.add_vline(x=50, line_dash="dash", line_color="grey", opacity=0.4)

    fort  = "Fort"   if lang == "fr" else "Alto"
    faible = "Faible" if lang == "fr" else "Bajo"
    profil_limite = "Profil limité" if lang == "fr" else "Perfil limitado"

    fig.add_annotation(x=12, y=95,
        text=f"{fort} {label_y}<br>{faible} {label_x}",
        showarrow=False,
        font=dict(size=10, color="grey"), opacity=0.6)

    fig.add_annotation(x=85, y=95,
        text=f"{fort} {label_x}<br>+ {fort} {label_y}",
        showarrow=False,
        font=dict(size=10, color="#27ae60"), opacity=0.9)

    fig.add_annotation(x=12, y=5,
        text=profil_limite,
        showarrow=False,
        font=dict(size=10, color="grey"), opacity=0.6)

    fig.add_annotation(x=85, y=5,
        text=f"{fort} {label_x}<br>{faible} {label_y}",
        showarrow=False,
        font=dict(size=10, color="grey"), opacity=0.6)

    taille_label = "Taille = minutes jouées" if lang == "fr" else "Tamaño = minutos jugados"
    carto_title  = "Cartographie MC" if lang == "fr" else "Cartografía MC"
    ligue_label  = "Ligue" if lang == "fr" else "Liga"

    fig.update_layout(
        title=dict(
            text=f"{carto_title} — {label_x} vs {label_y}<br>"
                 f"<sup>L1 · L2 · Liga · Liga Segunda 2025/2026 — {taille_label}</sup>",
            font=dict(size=15)
        ),
        xaxis=dict(title=f"← {label_x} →", range=[0, 100],
                   showgrid=True, gridcolor="#eeeeee"),
        yaxis=dict(title=f"← {label_y} →", range=[0, 100],
                   showgrid=True, gridcolor="#eeeeee"),
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="#f8f9fa",
        legend=dict(title=ligue_label),
        height=650,
        hovermode="closest",
        font=dict(family="Arial")
    )

    return fig


# ============================================================
# PIZZA CHART — PROFIL MC COMPLET
# ============================================================

def pizza_chart(nom, df_final, lang="fr"):
    row = df_final[df_final["joueur"] == nom]
    if row.empty:
        return None
    j = row.iloc[0]

    dimensions = [
        ("Actions déf.",     "actions_def_90_adj_pct",       "#e74c3c"),
        ("Duels déf.",       "duels_def_90_adj_pct",         "#e74c3c"),
        ("Tacles",           "tacles_padj_adj_pct",          "#e74c3c"),
        ("Interceptions",    "interceptions_padj_adj_pct",   "#e74c3c"),
        ("Tirs contrés",     "tirs_contres_90_adj_pct",      "#e74c3c"),
        ("Passes",           "passes_90_adj_pct",            "#3498db"),
        ("Passes %",         "passes_pct_adj_pct",           "#3498db"),
        ("Passes prog.",     "passes_prog_90_adj_pct",       "#3498db"),
        ("Passes av.",       "passes_avant_90_adj_pct",      "#3498db"),
        ("Passes tiers adv.","passes_tiers_adv_90_adj_pct",  "#3498db"),
        ("Courses prog.",    "courses_prog_90_adj_pct",      "#2ecc71"),
        ("Accélérations",    "accelerations_90_adj_pct",     "#2ecc71"),
        ("Dribbles",         "dribbles_90_adj_pct",          "#2ecc71"),
        ("xG",               "xg_90_pct",                    "#f39c12"),
        ("xA",               "xa_90_pct",                    "#f39c12"),
        ("2e passes déc.",   "secondes_pd_90_pct",           "#f39c12"),
        ("Passes surface",   "passes_surface_90_pct",        "#f39c12"),
    ]

    labels = [d[0] for d in dimensions]
    cols   = [d[1] for d in dimensions]
    colors = [d[2] for d in dimensions]
    values = [float(j[c]) if c in j and pd.notna(j[c]) else 0 for c in cols]

    N      = len(labels)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()

    fig = plt.figure(figsize=(14, 10))
    fig.patch.set_facecolor("#f8f9fa")

    ax = fig.add_axes([0.05, 0.05, 0.60, 0.90], polar=True)
    ax.set_facecolor("#f8f9fa")

    for r, alpha in [(100, 0.04), (75, 0.04), (50, 0.04), (25, 0.04)]:
        ax.fill(angles + [angles[0]], [r] * (N + 1), color="#2c3e50", alpha=alpha)
    for r in [25, 50, 75, 100]:
        ax.plot(angles + [angles[0]], [r] * (N + 1),
                color="grey", linewidth=0.5, alpha=0.3)
    for angle in angles:
        ax.plot([angle, angle], [0, 100], color="grey", linewidth=0.5, alpha=0.3)

    bar_width = 2 * np.pi / N
    for angle, value, color in zip(angles, values, colors):
        ax.bar(angle, value, width=bar_width * 0.85,
               bottom=0, color=color, alpha=0.75,
               edgecolor="white", linewidth=0.8)

    ax.set_xticks(angles)
    ax.set_xticklabels([])
    ax.set_yticks([])
    ax.set_ylim(0, 115)
    ax.spines["polar"].set_visible(False)

    for angle, label, value in zip(angles, labels, values):
        ax.text(angle, 108, f"{label}\n{round(value)}",
                ha="center", va="center",
                fontsize=7.5, color="#2c3e50", fontweight="bold")

    # Colonne droite
    ax_info = fig.add_axes([0.65, 0.05, 0.33, 0.90])
    ax_info.set_facecolor("#f8f9fa")
    ax_info.axis("off")

    ax_info.text(0.0, 0.97, nom,
                 fontsize=18, fontweight="bold", color="#2c3e50",
                 transform=ax_info.transAxes, va="top")
    ax_info.text(0.0, 0.91, f"{j['equipe_norm']}  ·  {j['ligue']}",
                 fontsize=11, color="#7f8c8d",
                 transform=ax_info.transAxes, va="top")
    ax_info.text(0.0, 0.86, f"{int(j['minutes'])} min  ·  {j['niveau_fiabilite']}",
                 fontsize=10, color="#95a5a6",
                 transform=ax_info.transAxes, va="top")

    ax_info.plot([0, 1], [0.83, 0.83], color="#2c3e50",
                 linewidth=1, alpha=0.3, transform=ax_info.transAxes)

    ax_info.text(0.0, 0.80,
                 "DIMENSIONS" if lang == "fr" else "DIMENSIONES",
                 fontsize=9, fontweight="bold", color="#2c3e50",
                 transform=ax_info.transAxes, va="top")

    dim_labels = [
        ("#e74c3c", "Défense"    if lang == "fr" else "Defensa"),
        ("#3498db", "Passes"     if lang == "fr" else "Pases"),
        ("#2ecc71", "Transition" if lang == "fr" else "Transición"),
        ("#f39c12", "Offensif"   if lang == "fr" else "Ofensivo"),
    ]
    for i, (color, label) in enumerate(dim_labels):
        y = 0.74 - i * 0.07
        ax_info.add_patch(plt.Rectangle(
            (0.0, y - 0.015), 0.08, 0.04,
            color=color, alpha=0.75, transform=ax_info.transAxes
        ))
        ax_info.text(0.12, y, label, fontsize=10, color="#2c3e50",
                     transform=ax_info.transAxes, va="center")

    ax_info.plot([0, 1], [0.43, 0.43], color="#2c3e50",
                 linewidth=1, alpha=0.3, transform=ax_info.transAxes)

    ax_info.text(0.0, 0.40,
                 "SCORES PROFILS" if lang == "fr" else "PUNTUACIONES PERFILES",
                 fontsize=9, fontweight="bold", color="#2c3e50",
                 transform=ax_info.transAxes, va="top")

    pizza_profils = [
        ("Récupérateur" if lang == "fr" else "Recuperador", "score_mc_recuperateur", "#e74c3c"),
        ("Relanceur"    if lang == "fr" else "Relanzador",   "score_mc_relanceur",    "#3498db"),
        ("Box to Box",                                        "score_mc_boxtbox",      "#2ecc71"),
        ("Intérieur"    if lang == "fr" else "Interior",     "score_mc_interieur",    "#9b59b6"),
        ("Offensif"     if lang == "fr" else "Ofensivo",     "score_mc_offensif",     "#f39c12"),
    ]
    for i, (label, col, color) in enumerate(pizza_profils):
        y     = 0.33 - i * 0.060
        score = round(j[col], 1) if col in j and pd.notna(j[col]) else 0
        ax_info.barh(y, score / 100 * 0.85, height=0.038,
                     color=color, alpha=0.7, transform=ax_info.transAxes)
        ax_info.text(0.0, y + 0.022, label, fontsize=8.5, color="#2c3e50",
                     transform=ax_info.transAxes, va="center")
        ax_info.text(0.88, y + 0.022, f"{score}", fontsize=8.5,
                     fontweight="bold", color="#2c3e50",
                     transform=ax_info.transAxes, va="center", ha="right")

    ax_info.plot([0, 1], [0.04, 0.04], color="#2c3e50",
                 linewidth=1, alpha=0.3, transform=ax_info.transAxes)

    impact       = round(j["impact_contexte"] * 100, 1)
    impact_color = "#27ae60" if impact >= 0 else "#e74c3c"
    impact_label = ("sous-coté" if impact >= 0 else "favorisé") if lang == "fr" else ("infravalorado" if impact >= 0 else "favorecido")
    impact_title = "Impact contexte" if lang == "fr" else "Impacto contexto"

    ax_info.text(0.0, 0.03,
                 f"{impact_title} : {impact:+.1f}% — {impact_label}",
                 fontsize=8.5, color=impact_color, fontweight="bold",
                 transform=ax_info.transAxes, va="top")

    footer = "Data : Hudl Wyscout | Percentiles inter-ligues ajustés" if lang == "fr" else "Data : Hudl Wyscout | Percentiles inter-ligas ajustados"
    fig.text(0.98, 0.01, footer, ha="right", fontsize=8, alpha=0.6)

    return fig
