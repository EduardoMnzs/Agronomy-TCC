"""
Prescrição de Fertilizantes e Corretivos
Agro Lagoa da Prata - 2024
----------------------------------------
Shapefiles lidos:
  - agro_ladoa_da_prata_rec_00-21-00.shp  → Adubo fosfatado (00-21-00), coluna: ad21  [kg/ha]
  - agro_ladoa_da_prata_rec_kcl.shp       → Cloreto de potássio (KCl), coluna: KCL   [kg/ha]
"""

import os
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import pandas as pd
import numpy as np
from matplotlib.colorbar import ColorbarBase

# ── Configurações ─────────────────────────────────────────────────────────────
PASTA = os.path.dirname(os.path.abspath(__file__))

ARQUIVOS = {
    "00-21-00 (MAP)": {
        "shp":    os.path.join(PASTA, "agro_ladoa_da_prata_rec_00-21-00.shp"),
        "coluna": "ad21",
        "unidade": "kg/ha",
        "cmap":   "YlOrRd",
        "titulo": "Prescrição – Adubo 00-21-00 (MAP)",
        "cor_legenda": "#e07b00",
    },
    "KCl": {
        "shp":    os.path.join(PASTA, "agro_ladoa_da_prata_rec_kcl.shp"),
        "coluna": "KCL",
        "unidade": "kg/ha",
        "cmap":   "Blues",
        "titulo": "Prescrição – Cloreto de Potássio (KCl)",
        "cor_legenda": "#1f77b4",
    },
}

# ── Leitura ────────────────────────────────────────────────────────────────────
gdfs = {}
for nome, cfg in ARQUIVOS.items():
    gdf = gpd.read_file(cfg["shp"])
    # Garante projeção métrica para cálculo de área (SIRGAS 2000 / UTM zona 23S)
    gdf_utm = gdf.to_crs(epsg=31983)
    gdf_utm["area_ha"] = gdf_utm.geometry.area / 10_000  # m² → ha
    gdf_utm["dose"] = gdf_utm[cfg["coluna"]].astype(float)
    gdf_utm["volume_kg"] = gdf_utm["dose"] * gdf_utm["area_ha"]
    gdfs[nome] = (gdf_utm, cfg)
    print(f"[OK] {nome}: {len(gdf_utm)} zonas carregadas")

# ── Estatísticas por fertilizante ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("RESUMO DE PRESCRIÇÃO")
print("=" * 60)

resumo_rows = []
for nome, (gdf, cfg) in gdfs.items():
    area_total = gdf["area_ha"].sum()
    dose_min   = gdf["dose"].min()
    dose_max   = gdf["dose"].max()
    dose_media = np.average(gdf["dose"], weights=gdf["area_ha"])
    volume_total = gdf["volume_kg"].sum()

    print(f"\n>>> {nome}")
    print(f"    Área total         : {area_total:.2f} ha")
    print(f"    Dose mínima        : {dose_min:.0f} {cfg['unidade']}")
    print(f"    Dose máxima        : {dose_max:.0f} {cfg['unidade']}")
    print(f"    Dose média (pond.) : {dose_media:.1f} {cfg['unidade']}")
    print(f"    Volume total       : {volume_total/1000:.2f} t  ({volume_total:.0f} kg)")

    # Distribuição por dose
    contagem = gdf.groupby("dose")["area_ha"].sum().reset_index()
    contagem.columns = ["Dose (kg/ha)", "Área (ha)"]
    contagem["Volume (kg)"] = contagem["Dose (kg/ha)"] * contagem["Área (ha)"]
    contagem["Volume (t)"]  = contagem["Volume (kg)"] / 1000
    print("\n    Distribuição por dose:")
    print(contagem.to_string(index=False))

    resumo_rows.append({
        "Fertilizante":        nome,
        "Área total (ha)":     round(area_total, 2),
        "Dose mínima (kg/ha)": dose_min,
        "Dose máxima (kg/ha)": dose_max,
        "Dose média (kg/ha)":  round(dose_media, 1),
        "Volume total (kg)":   round(volume_total, 0),
        "Volume total (t)":    round(volume_total / 1000, 2),
    })

# Salva resumo em CSV
df_resumo = pd.DataFrame(resumo_rows)
csv_saida = os.path.join(PASTA, "resumo_prescricao.csv")
df_resumo.to_csv(csv_saida, index=False, sep=";", decimal=",")
print(f"\n[OK] Resumo salvo em: {csv_saida}")

# ── Visualização ───────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(18, 8))
fig.suptitle(
    "Mapas de Prescrição – Agro Lagoa da Prata (2024)",
    fontsize=16, fontweight="bold", y=1.01,
)

for ax, (nome, (gdf, cfg)) in zip(axes, gdfs.items()):
    col = "dose"
    vmin, vmax = gdf[col].min(), gdf[col].max()

    gdf.plot(
        column=col,
        cmap=cfg["cmap"],
        vmin=vmin,
        vmax=vmax,
        linewidth=0.1,
        edgecolor="gray",
        legend=True,
        legend_kwds={
            "label":       f"Dose ({cfg['unidade']})",
            "orientation": "horizontal",
            "shrink":      0.7,
            "pad":         0.02,
        },
        ax=ax,
    )

    # Rótulo de doses únicas por zona (opcional – descomente se quiser)
    # for _, row in gdf.iterrows():
    #     cx, cy = row.geometry.centroid.x, row.geometry.centroid.y
    #     ax.annotate(str(int(row[col])), (cx, cy), fontsize=3, ha="center")

    ax.set_title(cfg["titulo"], fontsize=13, fontweight="bold")
    ax.set_xlabel("Longitude / X (m)")
    ax.set_ylabel("Latitude / Y (m)")
    ax.tick_params(labelsize=8)
    ax.set_aspect("equal")

    # Anotação de volume total
    vol_t = gdf["volume_kg"].sum() / 1000
    ax.annotate(
        f"Volume total: {vol_t:.1f} t",
        xy=(0.02, 0.97), xycoords="axes fraction",
        fontsize=10, color="black",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8),
        va="top",
    )

plt.tight_layout()
img_saida = os.path.join(PASTA, "mapa_prescricao.png")
plt.savefig(img_saida, dpi=200, bbox_inches="tight")
print(f"[OK] Mapa salvo em: {img_saida}")
plt.show()

# ── Mapa comparativo lado a lado (doses em classes) ───────────────────────────
fig2, axes2 = plt.subplots(1, 2, figsize=(18, 8))
fig2.suptitle(
    "Distribuição de Doses por Zona – Agro Lagoa da Prata (2024)",
    fontsize=15, fontweight="bold",
)

for ax, (nome, (gdf, cfg)) in zip(axes2, gdfs.items()):
    doses_unicas = sorted(gdf["dose"].unique())
    n = len(doses_unicas)
    cmap_obj = plt.get_cmap(cfg["cmap"], n)
    dose_to_idx = {d: i for i, d in enumerate(doses_unicas)}
    gdf = gdf.copy()
    gdf["dose_idx"] = gdf["dose"].map(dose_to_idx)

    gdf.plot(
        column="dose_idx",
        cmap=cmap_obj,
        vmin=-0.5,
        vmax=n - 0.5,
        linewidth=0.1,
        edgecolor="gray",
        legend=False,
        ax=ax,
    )

    # Legenda manual com dose e área
    patches = []
    for i, dose in enumerate(doses_unicas):
        area = gdf.loc[gdf["dose"] == dose, "area_ha"].sum()
        cor  = cmap_obj(i / max(n - 1, 1))
        patches.append(
            mpatches.Patch(
                color=cor,
                label=f"{int(dose)} kg/ha  ({area:.1f} ha)",
            )
        )
    ax.legend(
        handles=patches,
        title=f"Dose {cfg['unidade']}",
        loc="lower left",
        fontsize=7,
        title_fontsize=8,
        framealpha=0.85,
    )

    ax.set_title(cfg["titulo"], fontsize=12, fontweight="bold")
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_aspect("equal")

plt.tight_layout()
img2_saida = os.path.join(PASTA, "mapa_prescricao_classes.png")
plt.savefig(img2_saida, dpi=200, bbox_inches="tight")
print(f"[OK] Mapa de classes salvo em: {img2_saida}")
plt.show()

print("\nProcessamento concluído.")
