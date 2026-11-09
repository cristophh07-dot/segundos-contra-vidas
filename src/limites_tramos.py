"""
src/limites_tramos.py — entre qué puntos va cada tramo de Google Traffic (columnas INICIO y FIN).
Guarda data/processed/limites_tramos.csv y docs/limites_tramos.txt.
Uso: python -m src.limites_tramos
"""
from __future__ import annotations

import pathlib

import pandas as pd

from src.descarga import leer
from src.velocidad import PROCESSED, TRAMO_A_CORREDOR

DOCS = pathlib.Path("docs")


def _col(df: pd.DataFrame, nombre: str):
    for c in df.columns:
        if str(c).strip().upper() == nombre:
            return c
    return None


def limites_tramos() -> pd.DataFrame:
    gt = leer("velocidad_gt")
    print("Columnas de velocidad_gt:", list(gt.columns))
    c_ini, c_fin, c_nom = _col(gt, "INICIO"), _col(gt, "FIN"), _col(gt, "NOMBRE_CORREDOR")
    if c_ini is None or c_fin is None:
        raise KeyError(f"No encuentro INICIO/FIN en velocidad_gt. Columnas reales: {list(gt.columns)}")

    gt["corredor_id"] = gt["CORREDOR"].map(TRAMO_A_CORREDOR)
    lineas, filas = [], []
    for tramo, g in gt.groupby("CORREDOR"):
        ini, fin = g[c_ini].dropna().astype(str).str.strip(), g[c_fin].dropna().astype(str).str.strip()
        fila = {
            "tramo": int(tramo),
            "corredor_id": g["corredor_id"].iloc[0],
            "nombre_gt": g[c_nom].dropna().astype(str).mode().iloc[0] if c_nom else None,
            "inicio": ini.mode().iloc[0] if len(ini) else None,
            "n_variantes_inicio": int(ini.nunique()),
            "fin": fin.mode().iloc[0] if len(fin) else None,
            "n_variantes_fin": int(fin.nunique()),
            "longitud_km_mediana": float(g["LONGITUD_KM"].median()),
            "n_filas": int(len(g)),
        }
        filas.append(fila)
        lineas.append(f"Tramo {fila['tramo']} · {fila['corredor_id']} · {fila['nombre_gt']} · "
                      f"{fila['longitud_km_mediana']:.2f} km · {fila['n_filas']:,} filas")
        lineas.append(f"  INICIO: {fila['inicio']}  ({fila['n_variantes_inicio']} variante(s))")
        lineas.append(f"  FIN:    {fila['fin']}  ({fila['n_variantes_fin']} variante(s))")
        if fila["n_variantes_inicio"] > 1:
            lineas.append(f"  variantes INICIO: {ini.value_counts().head(3).to_dict()}")
        if fila["n_variantes_fin"] > 1:
            lineas.append(f"  variantes FIN: {fin.value_counts().head(3).to_dict()}")

    out = pd.DataFrame(filas).sort_values("tramo").reset_index(drop=True)
    out.to_csv(PROCESSED / "limites_tramos.csv", index=False, encoding="utf-8")
    DOCS.mkdir(exist_ok=True)
    (DOCS / "limites_tramos.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas))
    return out


if __name__ == "__main__":
    limites_tramos()
    