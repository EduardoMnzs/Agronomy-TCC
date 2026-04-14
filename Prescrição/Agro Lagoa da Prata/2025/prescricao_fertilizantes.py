"""
Prescricao de Fertilizantes e Corretivos — Agricultura de Precisão
Propriedade : AGROP LAGOA DE PRATA
Produtor     : GUILHERME LOPES
Talhão       : T_29
Autor        : Script gerado automaticamente via GitHub Copilot
Data         : 2026-04-09
"""

import os
import glob
import warnings
import geopandas as gpd
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import numpy as np
warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Configuração de caminhos
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FERC_DIR = os.path.join(BASE_DIR, "FERTILIZANTES E CORRETIVOS")
CONT_SHP = os.path.join(BASE_DIR, "CONTORNO", "agro_lagoa_prata_contorno.shp")
OUT_CSV  = os.path.join(BASE_DIR, "resumo_prescricao.csv")

# ---------------------------------------------------------------------------
# 1. Detecção da zona UTM pelo centróide do contorno
# ---------------------------------------------------------------------------
contorno_geo = gpd.read_file(CONT_SHP)
cx = contorno_geo.geometry.to_crs(epsg=4326).centroid.x.values[0]
# UTM zone SIRGAS 2000: zone = int((lon + 180) / 6) + 1, hemisfério Sul → +32700
utm_zone    = int((cx + 180) / 6) + 1   # 22 para lon ≈ -50°
utm_epsg    = 32700 + utm_zone           # WGS84 UTM Sul (usado para área)
sirgas_epsg = 31900 + utm_zone           # SIRGAS 2000 UTM Sul
print(f"Zona UTM detectada: {utm_zone}S  |  EPSG WGS84={utm_epsg}  EPSG SIRGAS={sirgas_epsg}")

# Reprojetar contorno para UTM para uso nos mapas
contorno_utm = contorno_geo.to_crs(epsg=utm_epsg)
area_total_ha = contorno_utm.geometry.area.sum() / 10_000
print(f"Área total (contorno UTM): {area_total_ha:.2f} ha\n")

# ---------------------------------------------------------------------------
# 2. Metadados dos fertilizantes / corretivos
# ---------------------------------------------------------------------------
META = {
    "agro_lagoa_prata_rec_00-21-00.shp": {
        "nome"      : "Superfosfato Simples 00-21-00",
        "sigla"     : "SFS 00-21-00",
        "nutriente" : "P₂O₅ (21%)",
        "unidade"   : "kg/ha",
    },
    "agro_lagoa_prata_rec_calcario.shp": {
        "nome"      : "Calcário Dolomítico",
        "sigla"     : "Calcário",
        "nutriente" : "CaO + MgO",
        "unidade"   : "kg/ha",
    },
    "agro_lagoa_prata_rec_kcl.shp": {
        "nome"      : "Cloreto de Potássio (KCl 60%)",
        "sigla"     : "KCl 60%",
        "nutriente" : "K₂O (60%)",
        "unidade"   : "kg/ha",
    },
}

# ---------------------------------------------------------------------------
# 3. Detectar coluna de dose automaticamente
# ---------------------------------------------------------------------------
def detectar_coluna_dose(gdf: gpd.GeoDataFrame) -> str:
    excluir = {"fid", "id", "geometry"}
    numericas = [c for c in gdf.columns
                 if c.lower() not in excluir and pd.api.types.is_numeric_dtype(gdf[c])]
    if len(numericas) == 1:
        return numericas[0]
    # Se houver mais de uma, escolhe a de maior variância
    return max(numericas, key=lambda c: gdf[c].var())

# ---------------------------------------------------------------------------
# 4. Loop de processamento
# ---------------------------------------------------------------------------
resultados  = []
distribuicoes = {}

shapefiles = sorted(glob.glob(os.path.join(FERC_DIR, "*.shp")))
print(f"Shapefiles encontrados: {len(shapefiles)}")
for shp in shapefiles:
    fname = os.path.basename(shp)
    meta  = META.get(fname, {"nome": fname, "sigla": fname, "nutriente": "?", "unidade": "kg/ha"})

    gdf = gpd.read_file(shp).to_crs(epsg=utm_epsg)
    col = detectar_coluna_dose(gdf)
    gdf["area_ha"] = gdf.geometry.area / 10_000

    # Subtotais por dose
    sub = (
        gdf.groupby(col)["area_ha"]
        .sum()
        .reset_index()
        .rename(columns={col: "dose_kg_ha", "area_ha": "area_ha"})
    )
    sub["volume_kg"] = sub["dose_kg_ha"] * sub["area_ha"]
    sub["insumo"]    = meta["sigla"]
    distribuicoes[fname] = {"gdf": gdf, "col": col, "sub": sub, "meta": meta}

    area_tot     = gdf["area_ha"].sum()
    vol_total_kg = (gdf[col] * gdf["area_ha"]).sum()
    dose_media   = vol_total_kg / area_tot

    resultados.append({
        "Insumo"           : meta["nome"],
        "Coluna_dose"      : col,
        "Nutriente"        : meta["nutriente"],
        "Área_total_ha"    : round(area_tot, 2),
        "Dose_min_kg_ha"   : gdf[col].min(),
        "Dose_max_kg_ha"   : gdf[col].max(),
        "Dose_media_kg_ha" : round(dose_media, 2),
        "Volume_total_kg"  : round(vol_total_kg, 0),
        "Volume_total_t"   : round(vol_total_kg / 1_000, 3),
    })

    print(f"\n{'='*60}")
    print(f"  {meta['nome']}  |  coluna: {col}")
    print(f"{'='*60}")
    print(sub[["dose_kg_ha","area_ha","volume_kg"]].to_string(index=False))
    print(f"\n  Área total : {area_tot:.2f} ha")
    print(f"  Dose média : {dose_media:.2f} kg/ha")
    print(f"  Volume     : {vol_total_kg/1000:.3f} t")

# ---------------------------------------------------------------------------
# 5. Resumo geral
# ---------------------------------------------------------------------------
df_resumo = pd.DataFrame(resultados)
print("\n\n" + "="*70)
print("RESUMO FINAL — PRESCRIÇÃO DE FERTILIZANTES E CORRETIVOS")
print("="*70)
print(df_resumo[["Insumo","Área_total_ha","Dose_min_kg_ha","Dose_max_kg_ha",
                  "Dose_media_kg_ha","Volume_total_kg","Volume_total_t"]]
      .to_string(index=False))

# ---------------------------------------------------------------------------
# 6. Exportar CSV
# ---------------------------------------------------------------------------
df_resumo.to_csv(
    OUT_CSV,
    index=False,
    sep=";",
    decimal=",",
    encoding="utf-8-sig",
)
print(f"\nCSV salvo: {OUT_CSV}")

# ---------------------------------------------------------------------------
# 7. Mapas
# ---------------------------------------------------------------------------
CMAPS = {
    "agro_lagoa_prata_rec_00-21-00.shp" : "YlOrRd",
    "agro_lagoa_prata_rec_calcario.shp" : "RdYlGn_r",
    "agro_lagoa_prata_rec_kcl.shp"      : "Blues",
}

for fname, dados in distribuicoes.items():
    gdf  = dados["gdf"]
    col  = dados["col"]
    sub  = dados["sub"]
    meta = dados["meta"]
    cmap = CMAPS.get(fname, "viridis")

    vol_t         = (gdf[col] * gdf["area_ha"]).sum() / 1_000
    dose_media    = (gdf[col] * gdf["area_ha"]).sum() / gdf["area_ha"].sum()
    area_total    = gdf["area_ha"].sum()
    anotacao_vol  = (
        f"Vol. total: {vol_t:.1f} t\n"
        f"Dose média: {dose_media:.0f} kg/ha\n"
        f"Área: {area_total:.1f} ha"
    )
    base = fname.replace(".shp", "")

    # --- Mapa 1: gradiente contínuo ---
    fig, ax = plt.subplots(figsize=(12, 10))
    contorno_utm.boundary.plot(ax=ax, color="black", linewidth=1.5, zorder=3)
    gdf.plot(
        ax=ax, column=col, cmap=cmap, legend=True,
        legend_kwds={"label": f"Dose ({meta['unidade']})",
                     "orientation": "horizontal",
                     "shrink": 0.7, "pad": 0.04},
        zorder=2,
    )
    ax.set_title(f"Prescrição — {meta['nome']}\nTalhão T_29 | AGROP Lagoa de Prata", fontsize=13)
    ax.set_xlabel("Longitude (m UTM)")
    ax.set_ylabel("Latitude (m UTM)")
    ax.text(0.01, 0.99, anotacao_vol, transform=ax.transAxes,
            fontsize=9, verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.8))
    ax.ticklabel_format(style="plain", axis="both")
    plt.tight_layout()
    out1 = os.path.join(BASE_DIR, f"mapa_prescricao_{base}.png")
    fig.savefig(out1, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Mapa contínuo salvo: {out1}")

    # --- Mapa 2: por classes de dose (CORRIGIDO) ---
    # Estratégia: mapear cada célula a um índice inteiro de classe (0…n-1)
    # e usar ListedColormap discreto para garantir cor única por classe.
    doses_unicas = sorted(sub["dose_kg_ha"].unique())
    n_classes    = min(8, len(doses_unicas))
    base_cmap    = matplotlib.colormaps.get_cmap(cmap)

    if len(doses_unicas) > n_classes:
        bins = np.linspace(min(doses_unicas), max(doses_unicas) + 1, n_classes + 1)
        gdf["class_idx"] = pd.cut(
            gdf[col], bins=bins, labels=list(range(n_classes)), right=False
        ).astype(float)
        cls_data = []
        for i in range(n_classes):
            mask  = (gdf[col] >= bins[i]) & (gdf[col] < bins[i + 1])
            area  = gdf.loc[mask, "area_ha"].sum()
            vol_t = (gdf.loc[mask, col] * gdf.loc[mask, "area_ha"]).sum() / 1_000
            lbl   = f"{int(bins[i])}–{int(bins[i+1]-1)}"
            cls_data.append({"label": lbl, "area_ha": area, "volume_t": vol_t})
    else:
        n_classes  = len(doses_unicas)
        dose_map   = {d: float(i) for i, d in enumerate(doses_unicas)}
        gdf["class_idx"] = gdf[col].map(dose_map)
        cls_data = []
        for i, d in enumerate(doses_unicas):
            mask  = gdf[col] == d
            area  = gdf.loc[mask, "area_ha"].sum()
            vol_t = float(d) * area / 1_000
            cls_data.append({"label": str(d), "area_ha": area, "volume_t": vol_t})

    # Cores discretas: uma por índice de classe
    color_vals = [base_cmap(i / max(n_classes - 1, 1)) for i in range(n_classes)]
    cmap_disc  = mcolors.ListedColormap(color_vals)
    # BoundaryNorm com boundaries em -0.5, 0.5, 1.5 … para mapear inteiros exatos
    norm_disc  = mcolors.BoundaryNorm(
        np.arange(-0.5, n_classes + 0.5, 1.0), n_classes
    )

    fig, ax = plt.subplots(figsize=(12, 10))
    contorno_utm.boundary.plot(ax=ax, color="black", linewidth=1.5, zorder=3)
    gdf.plot(
        ax=ax, column="class_idx",
        cmap=cmap_disc, norm=norm_disc,
        edgecolor="none", zorder=2,
    )

    patches = []
    for i, row in enumerate(cls_data):
        cor = color_vals[i]
        lbl = f"{row['label']} kg/ha | {row['area_ha']:.1f} ha | {row['volume_t']:.1f} t"
        patches.append(mpatches.Patch(color=cor, label=lbl))

    ax.legend(handles=patches, loc="lower right", fontsize=8,
              title="Dose | Área | Volume",
              title_fontsize=9, framealpha=0.9)
    ax.set_title(f"Prescrição por Classes — {meta['nome']}\nTalhão T_29 | AGROP Lagoa de Prata", fontsize=13)
    ax.set_xlabel("Longitude (m UTM)")
    ax.set_ylabel("Latitude (m UTM)")
    ax.text(0.01, 0.99, anotacao_vol, transform=ax.transAxes,
            fontsize=9, verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.8))
    ax.ticklabel_format(style="plain", axis="both")
    plt.tight_layout()
    out2 = os.path.join(BASE_DIR, f"mapa_prescricao_classes_{base}.png")
    fig.savefig(out2, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Mapa por classes salvo: {out2}")

print("\nProcessamento concluído com sucesso!")
