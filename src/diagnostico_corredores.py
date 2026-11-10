"""src/diagnostico_corredores.py — concentración de muertes por corredor y mapa de los 12 corredores."""
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shapely

from src import seguridad as seg
from src.corredores import geometria_corredores

FIG = pathlib.Path("figuras")
TAB = pathlib.Path("data/processed")
ROJO, GRIS, AZUL = "#C0392B", "#95A5A6", "#2C3E50"


def generar():
    cat, _ = geometria_corredores()
    mor = seg.mortalidad_con_corredor(geometria=cat)
    total = len(mor)

    ids = list(cat["corredor_id"])
    por = (mor.dropna(subset=["corredor_id"]).groupby("corredor_id").size()
              .reindex(ids, fill_value=0).sort_values(ascending=False))
    asignados = int(por.sum())
    k = max(1, int(round(len(por) * 0.25)))
    top = int(por.iloc[:k].sum())
    tabla = pd.DataFrame({"muertos": por, "pct_de_asignados": por / asignados * 100,
                          "pct_acumulado": por.cumsum() / asignados * 100})
    tabla.to_csv(TAB / "muertos_por_corredor.csv")
    print(tabla.round(1).to_string())
    print(f"\nFRASE: el {k / len(por):.0%} de los corredores ({k} de {len(por)}) concentra el "
          f"{top / asignados:.0%} de las muertes en los 12 corredores ({top} de {asignados}); "
          f"sobre los {total} fallecidos de la ciudad: {top / total:.1%}. "
          f"Los 12 corredores suman {asignados / total:.0%} de los fallecidos.")

    # Figura 07: muertos por corredor
    fig, ax = plt.subplots(figsize=(16, 9))
    colores = [ROJO if i < k else AZUL for i in range(len(por))]
    ax.bar(por.index, por.values, color=colores)
    ax.set_xlabel("Corredor")
    ax.set_ylabel("Fallecidos (2019–2024)")
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right")
    ax.set_title(f"{k} de {len(por)} corredores concentran el {top / asignados:.0%} de las muertes "
                 f"en los corredores estudiados (2019–2024)", fontsize=18)
    fig.tight_layout()
    fig.savefig(FIG / "07_muertos_por_corredor.png", dpi=100)
    plt.close(fig)

    # Figura 08: mapa con los 12 corredores
    fig, ax = plt.subplots(figsize=(16, 9))
    d = mor.dropna(subset=["lat", "lon"])
    ax.scatter(d.lon, d.lat, s=6, color=GRIS, label="Fallecidos fuera de los corredores")
    a = d.dropna(subset=["corredor_id"])
    ax.scatter(a.lon, a.lat, s=16, color=ROJO, label="Fallecidos a 50 m o menos de un corredor")
    for cid, w in zip(cat["corredor_id"], cat["geometria_wkt"]):
        p = np.array([(g.x, g.y) for g in shapely.from_wkt(w).geoms])
        ax.plot(p[:, 0], p[:, 1], color=AZUL, lw=2.5)
        m = p[len(p) // 2]
        ax.annotate(cid, (m[0], m[1]), fontsize=9, color=AZUL, weight="bold")
    ax.set_aspect("equal")
    ax.set_xlabel("Longitud (grados)")
    ax.set_ylabel("Latitud (grados)")
    ax.legend(fontsize=12, loc="upper left")
    ax.set_title(f"{asignados} de los {total:,} fallecidos (2019–2024) ocurrieron sobre los "
                 f"{len(por)} corredores estudiados", fontsize=18)
    fig.tight_layout()
    fig.savefig(FIG / "08_mapa_12_corredores.png", dpi=100)
    plt.close(fig)
    print("figuras guardadas: 07 y 08")


if __name__ == "__main__":
    generar()