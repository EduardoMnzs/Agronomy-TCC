"""
Mapas de Fertilidade do Solo — Agricultura de Precisão
Propriedade : AGROP LAGOA DE PRATA  |  Talhão T_29
Data        : 2026-04-09
"""

import os
import warnings
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import numpy as np
warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
ANAL_SHP  = os.path.join(BASE_DIR, "ANALISE", "agro_lagoa_prata_analise.shp")
CONT_SHP  = os.path.join(BASE_DIR, "CONTORNO", "agro_lagoa_prata_contorno.shp")
OUT_DIR   = os.path.join(BASE_DIR, "MAPAS_FERTILIDADE")
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Projeção UTM (zona 22 S, WGS 84)
# ---------------------------------------------------------------------------
UTM_EPSG = 32722

contorno_utm = gpd.read_file(CONT_SHP).to_crs(epsg=UTM_EPSG)
analise_utm  = gpd.read_file(ANAL_SHP).to_crs(epsg=UTM_EPSG)

# ---------------------------------------------------------------------------
# Definição dos atributos e metadados
# Cada entrada: (coluna, titulo, unidade, colormap, faixas_interpretação)
# faixas: lista de (limite_sup, cor_hex, rótulo)  → usada na legenda de referência
# ---------------------------------------------------------------------------
ATTRS = [
    # — Saturação por Bases (V%) —
    dict(col="V2",     titulo="Saturação por Bases — V% (0–10 cm)",  unidade="%",
         cmap="RdYlGn", faixas=[
             (45,  "#d73027", "Muito Baixo (<45%)"),
             (60,  "#fdae61", "Baixo (45–60%)"),
             (70,  "#a6d96a", "Médio (60–70%)"),
             (100, "#1a9641", "Alto (>70%)"),
         ]),
    dict(col="V3",     titulo="Saturação por Bases — V% (10–20 cm)", unidade="%",
         cmap="RdYlGn", faixas=[
             (45,  "#d73027", "Muito Baixo (<45%)"),
             (60,  "#fdae61", "Baixo (45–60%)"),
             (70,  "#a6d96a", "Médio (60–70%)"),
             (100, "#1a9641", "Alto (>70%)"),
         ]),
    dict(col="V4",     titulo="Saturação por Bases — V% (20–40 cm)", unidade="%",
         cmap="RdYlGn", faixas=[
             (45,  "#d73027", "Muito Baixo (<45%)"),
             (60,  "#fdae61", "Baixo (45–60%)"),
             (70,  "#a6d96a", "Médio (60–70%)"),
             (100, "#1a9641", "Alto (>70%)"),
         ]),
    # — Fósforo (P-Resina) —
    dict(col="P_RES2", titulo="Fósforo P-Resina (0–10 cm)",          unidade="mg/dm³",
         cmap="YlOrRd", faixas=[
             (12,  "#d73027", "Muito Baixo (<12)"),
             (25,  "#fdae61", "Baixo (12–25)"),
             (40,  "#ffffbf", "Médio (25–40)"),
             (70,  "#1a9641", "Alto (>40)"),
         ]),
    dict(col="P_RES3", titulo="Fósforo P-Resina (10–20 cm)",         unidade="mg/dm³",
         cmap="YlOrRd", faixas=[
             (12,  "#d73027", "Muito Baixo (<12)"),
             (25,  "#fdae61", "Baixo (12–25)"),
             (40,  "#ffffbf", "Médio (25–40)"),
             (70,  "#1a9641", "Alto (>40)"),
         ]),
    # — Potássio (K⁺) —
    dict(col="K2",     titulo="Potássio K⁺ (0–10 cm)",               unidade="cmolc/dm³",
         cmap="YlGn", faixas=[
             (0.15, "#d73027", "Muito Baixo (<0,15)"),
             (0.30, "#fdae61", "Baixo (0,15–0,30)"),
             (0.60, "#a6d96a", "Médio (0,30–0,60)"),
             (1.20, "#1a9641", "Alto (>0,60)"),
         ]),
    dict(col="K3",     titulo="Potássio K⁺ (10–20 cm)",              unidade="cmolc/dm³",
         cmap="YlGn", faixas=[
             (0.15, "#d73027", "Muito Baixo (<0,15)"),
             (0.30, "#fdae61", "Baixo (0,15–0,30)"),
             (0.60, "#a6d96a", "Médio (0,30–0,60)"),
             (1.20, "#1a9641", "Alto (>0,60)"),
         ]),
    # — Cálcio (Ca²⁺) —
    dict(col="CA2",    titulo="Cálcio Ca²⁺ (0–10 cm)",               unidade="cmolc/dm³",
         cmap="Blues", faixas=[
             (1.5,  "#d73027", "Muito Baixo (<1,5)"),
             (3.0,  "#fdae61", "Baixo (1,5–3,0)"),
             (7.0,  "#a6d96a", "Médio (3,0–7,0)"),
             (15.0, "#1a9641", "Alto (>7,0)"),
         ]),
    dict(col="CA3",    titulo="Cálcio Ca²⁺ (10–20 cm)",              unidade="cmolc/dm³",
         cmap="Blues", faixas=[
             (1.5,  "#d73027", "Muito Baixo (<1,5)"),
             (3.0,  "#fdae61", "Baixo (1,5–3,0)"),
             (7.0,  "#a6d96a", "Médio (3,0–7,0)"),
             (15.0, "#1a9641", "Alto (>7,0)"),
         ]),
    # — Magnésio (Mg²⁺) —
    dict(col="MG2",    titulo="Magnésio Mg²⁺ (0–10 cm)",             unidade="cmolc/dm³",
         cmap="Purples", faixas=[
             (0.4,  "#d73027", "Muito Baixo (<0,4)"),
             (0.8,  "#fdae61", "Baixo (0,4–0,8)"),
             (2.0,  "#a6d96a", "Médio (0,8–2,0)"),
             (5.0,  "#1a9641", "Alto (>2,0)"),
         ]),
    dict(col="MG3",    titulo="Magnésio Mg²⁺ (10–20 cm)",            unidade="cmolc/dm³",
         cmap="Purples", faixas=[
             (0.4,  "#d73027", "Muito Baixo (<0,4)"),
             (0.8,  "#fdae61", "Baixo (0,4–0,8)"),
             (2.0,  "#a6d96a", "Médio (0,8–2,0)"),
             (5.0,  "#1a9641", "Alto (>2,0)"),
         ]),
    # — CTC —
    dict(col="CTC2",   titulo="CTC (0–10 cm)",                       unidade="cmolc/dm³",
         cmap="OrRd", faixas=[
             (4.0,  "#d73027", "Muito Baixo (<4)"),
             (8.0,  "#fdae61", "Baixo (4–8)"),
             (15.0, "#a6d96a", "Médio (8–15)"),
             (25.0, "#1a9641", "Alto (>15)"),
         ]),
    # — Enxofre —
    dict(col="S4",     titulo="Enxofre S (20–40 cm)",                unidade="mg/dm³",
         cmap="copper_r", faixas=[
             (10,  "#d73027", "Baixo (<10)"),
             (20,  "#fdae61", "Médio (10–20)"),
             (50,  "#1a9641", "Alto (>20)"),
         ]),
    # — Saturação de Ca e Mg —
    dict(col="SAT_CA2", titulo="Sat. Cálcio — Ca/CTC (0–10 cm)",    unidade="%",
         cmap="Blues", faixas=[
             (25,  "#d73027", "Baixo (<25%)"),
             (60,  "#1a9641", "Adequado (25–60%)"),
             (100, "#fdae61", "Alto (>60%)"),
         ]),
    dict(col="SAT_MG2", titulo="Sat. Magnésio — Mg/CTC (0–10 cm)", unidade="%",
         cmap="Purples", faixas=[
             (5,   "#d73027", "Baixo (<5%)"),
             (20,  "#1a9641", "Adequado (5–20%)"),
             (100, "#fdae61", "Alto (>20%)"),
         ]),
]

# ---------------------------------------------------------------------------
# Função auxiliar — criar legenda de interpretação agronômica
# ---------------------------------------------------------------------------
def legenda_faixas(ax, faixas, vmin, vmax):
    patches = []
    for i, (lim, cor, lbl) in enumerate(faixas):
        patches.append(mpatches.Patch(color=cor, label=lbl))
    ax.legend(handles=patches, loc="lower right", fontsize=8,
              title="Interpretação (5ª Aprox.)", title_fontsize=8,
              framealpha=0.9)

# ---------------------------------------------------------------------------
# Geração dos mapas
# ---------------------------------------------------------------------------
for attr in ATTRS:
    col    = attr["col"]
    titulo = attr["titulo"]
    unid   = attr["unidade"]
    cmap_  = attr["cmap"]
    faixas = attr["faixas"]

    vmin = analise_utm[col].min()
    vmax = analise_utm[col].max()
    mean = analise_utm[col].mean()

    anotacao = (
        f"Mín: {vmin:.2f} {unid}\n"
        f"Méd: {mean:.2f} {unid}\n"
        f"Máx: {vmax:.2f} {unid}"
    )

    fig, ax = plt.subplots(figsize=(12, 10))

    # Plotar análise com gradiente contínuo
    analise_utm.plot(
        ax=ax, column=col, cmap=cmap_, edgecolor="none",
        legend=True,
        legend_kwds={"label": f"{col} ({unid})",
                     "orientation": "horizontal",
                     "shrink": 0.65, "pad": 0.04},
        vmin=vmin, vmax=vmax, zorder=2,
    )

    # Contorno do talhão por cima
    contorno_utm.boundary.plot(ax=ax, color="black", linewidth=1.8, zorder=3)

    # Anotação de estatísticas
    ax.text(0.01, 0.99, anotacao, transform=ax.transAxes,
            fontsize=9, verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.85))

    # Legenda de interpretação agronômica
    legenda_faixas(ax, faixas, vmin, vmax)

    ax.set_title(
        f"Mapa de Fertilidade — {titulo}\nTalhão T_29 | AGROP Lagoa de Prata",
        fontsize=13
    )
    ax.set_xlabel("Longitude (m UTM)")
    ax.set_ylabel("Latitude (m UTM)")
    ax.ticklabel_format(style="plain", axis="both")
    plt.tight_layout()

    fname = os.path.join(OUT_DIR, f"fertilidade_{col.lower()}.png")
    fig.savefig(fname, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Salvo: {fname}")

print(f"\nTotal de mapas gerados: {len(ATTRS)}")
print(f"Pasta de saída: {OUT_DIR}")
