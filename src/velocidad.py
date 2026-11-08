"""
src/velocidad.py — entregas de Johan: velocidad, tráfico, costo en tiempo y motos.
Todo se lee con src.descarga.leer() desde las URLs de src/fuentes.py.
Los resultados también se guardan en data/processed/ (carpeta regenerable).

Cómo buscar los alias en las direcciones de los incidentes (para Josué):
- Las direcciones vienen como cruces en nomenclatura numérica ("CR 80 CL 62", "CR 43 A CL 34").
- Cada corredor trae dos formas: la abreviada (victimas_medata) y la completa ("CARRERA 80", "CALLE 44"),
  que es la de la base del ITM según la decisión D10. La forma completa aún no se ha contrastado con
  los datos del ITM: Josué puede confirmarla con incidentes_limpios().
- Busca cada alias con límites de palabra (regex) para que "CR 80" no atrape "CR 800".
- Una letra suelta después del alias ("CR 80 B", "CL 30 A") es OTRA calle: exclúyela,
  salvo que el alias ya incluya la letra (por ejemplo "CR 43 A").
- Un cruce entre dos corredores (por ejemplo "CR 80 CL 30") coincide con ambos.
- Un alias cubre toda la calle, pero el tramo medido por Google Traffic es solo una parte
  (por ejemplo Av. 80 va de Calle 30 a Calle 60/65): filtra por las calles que cruzan.
- AV_PALMAS casi no aparece en las direcciones ("VIA LAS PALMAS KM 8 + 620 MTS"): asignar por coordenadas.
"""
from __future__ import annotations

import pathlib

import pandas as pd

from src.descarga import leer

PROCESSED = pathlib.Path("data/processed")
PROCESSED.mkdir(parents=True, exist_ok=True)

# Id de tramo en velocidad_gt (columna CORREDOR) -> corredor_id.
# Se usa el id y no NOMBRE_CORREDOR porque ~30 filas de los tramos 13 y 14 (El Poblado)
# traen el nombre "Avenida Guayabal".
TRAMO_A_CORREDOR = {
    2: "AV_REGIONAL",
    4: "AUT_SUR",
    5: "AUT_NORTE", 6: "AUT_NORTE",
    7: "AV_80", 9: "AV_80",
    11: "AV_PALMAS", 12: "AV_PALMAS",
    13: "AV_POBLADO", 14: "AV_POBLADO",
    15: "AV_GUAYABAL", 16: "AV_GUAYABAL",
    17: "AV_33", 18: "AV_33",
    19: "CL_30", 20: "CL_30",
    21: "AV_SAN_JUAN", 22: "AV_SAN_JUAN",
    23: "AV_FERROCARRIL", 24: "AV_FERROCARRIL",
    25: "AV_ORIENTAL", 26: "AV_ORIENTAL",
}

# nombre legible, alias de dirección (mayúscula, sin tildes) y nombre del corredor en el SIMM.
CORREDORES = {
    "AV_80": ("Avenida 80", "CR 80|CARRERA 80|AV 80|AVENIDA 80", "Avenida 80"),
    "AV_33": ("Avenida 33", "CL 33|CALLE 33|AV 33|AVENIDA 33", "Avenida 33"),
    "CL_30": ("Calle 30", "CL 30|CALLE 30", "Calle 30"),
    "AV_POBLADO": ("Avenida El Poblado", "CR 43 A|CARRERA 43 A|CARRERA 43A", "Avenida El Poblado"),
    "AV_SAN_JUAN": ("Avenida San Juan", "CL 44|CALLE 44", "San Juan"),
    "AV_ORIENTAL": ("Avenida Oriental", "CR 46|CARRERA 46", "Avenida Oriental"),
    "AV_GUAYABAL": ("Avenida Guayabal", "CR 52|CARRERA 52", "Avenida Guayabal"),
    "AUT_NORTE": ("Autopista Norte", "CR 64 C|CARRERA 64 C|CARRERA 64C", "Autopista Norte"),
    "AUT_SUR": ("Autopista Sur", "CR 48|CARRERA 48", "Autopista Sur"),
    "AV_REGIONAL": ("Avenida Regional", "CR 55|CARRERA 55", "Avenida Regional"),
    "AV_FERROCARRIL": ("Avenida Ferrocarril", "CR 57|CARRERA 57", "Avenida Ferrocarril"),
    "AV_PALMAS": ("Avenida Las Palmas", "LAS PALMAS", "Avenida Las Palmas"),
}


def catalogo_corredores() -> pd.DataFrame:
    """Catálogo de corredores. Guarda data/processed/catalogo_corredores.csv."""
    gt = leer("velocidad_gt", usecols=["CORREDOR", "LONGITUD_KM"])
    gt["corredor_id"] = gt["CORREDOR"].map(TRAMO_A_CORREDOR)
    sin_corredor = sorted(gt.loc[gt["corredor_id"].isna(), "CORREDOR"].unique())
    if sin_corredor:
        raise ValueError(f"Tramos de velocidad_gt sin corredor_id: {sin_corredor}")

    # La longitud de un mismo tramo cambia entre registros: se usa la mediana por tramo
    # y, si el corredor tiene dos sentidos, el promedio de las dos medianas.
    por_tramo = gt.groupby(["corredor_id", "CORREDOR"])["LONGITUD_KM"].median().reset_index()
    longitud = por_tramo.groupby("corredor_id")["LONGITUD_KM"].mean().round(2)

    nombres_simm = set(
        leer("velocidad_simm", usecols=["corredor"])["corredor"].dropna().astype(str).str.strip().unique()
    )

    filas = []
    for cid, (nombre, alias, nombre_simm) in CORREDORES.items():
        filas.append({
            "corredor_id": cid,
            "nombre": nombre,
            "alias_direccion": alias,
            "longitud_km": float(longitud[cid]),
            "fuente_longitud": "Mediana de LONGITUD_KM por tramo en velocidad_gt (Google Traffic 2017-2020); promedio de sentidos",
            "geometria_wkt": None,
            "tiene_simm": int(nombre_simm in nombres_simm),
            "tiene_gt": 1,
        })
    cat = pd.DataFrame(filas)
    cat.to_csv(PROCESSED / "catalogo_corredores.csv", index=False, encoding="utf-8")
    return cat


def tiempo_viaje_gt() -> pd.DataFrame:
    """Velocidad y tiempo de viaje de Google Traffic por corredor, fecha y hora (6 a 20 h).
    Guarda data/processed/tiempo_viaje_gt.csv.

    Google Traffic registra varias lecturas por tramo y hora (lo normal son 1 o 2, hasta 13): primero
    se promedian las lecturas de cada tramo y hora, para que un sentido con más lecturas no pese más.
    Cuando un corredor tiene varios tramos (uno por sentido), se promedian ponderando por la
    longitud mediana de cada tramo. Se usa la mediana y no la longitud de cada fila porque la
    longitud registrada de un mismo tramo cambia entre filas (hay valores raros, como 8,0 km en
    Ferrocarril). tiempo_viaje_min es el tiempo promedio de recorrer el corredor en un sentido.
    """
    gt = leer("velocidad_gt", usecols=["CORREDOR", "FECHA", "HORA", "LONGITUD_KM", "TV_MINUTOS", "VELOCIDAD_KM/H"])
    gt["corredor_id"] = gt["CORREDOR"].map(TRAMO_A_CORREDOR)
    sin_corredor = sorted(gt.loc[gt["corredor_id"].isna(), "CORREDOR"].unique())
    if sin_corredor:
        raise ValueError(f"Tramos de velocidad_gt sin corredor_id: {sin_corredor}")

    # FECHA viene como día/mes/año ("1/02/2017" = 1 de febrero de 2017).
    gt["fecha"] = pd.to_datetime(gt["FECHA"], format="%d/%m/%Y", errors="coerce")
    if gt["fecha"].isna().any():
        raise ValueError("Hay fechas de velocidad_gt que no siguen el formato día/mes/año")

    longitud_tramo = gt.groupby("CORREDOR")["LONGITUD_KM"].median()

    # Paso 1: promedio simple de las lecturas repetidas de cada tramo en cada hora.
    por_tramo = gt.groupby(["corredor_id", "CORREDOR", "fecha", "HORA"], as_index=False).agg(
        v=("VELOCIDAD_KM/H", "mean"), t=("TV_MINUTOS", "mean"),
    )
    por_tramo["peso"] = por_tramo["CORREDOR"].map(longitud_tramo)

    # Paso 2: promedio de los tramos del corredor ponderado por longitud. Los pesos solo cuentan
    # donde hay dato (no se asume 0 donde falta).
    por_tramo["peso_v"] = por_tramo["peso"].where(por_tramo["v"].notna())
    por_tramo["peso_t"] = por_tramo["peso"].where(por_tramo["t"].notna())
    por_tramo["v_x_peso"] = por_tramo["v"] * por_tramo["peso"]
    por_tramo["t_x_peso"] = por_tramo["t"] * por_tramo["peso"]
    g = por_tramo.groupby(["corredor_id", "fecha", "HORA"], as_index=False).agg(
        v=("v_x_peso", "sum"), pv=("peso_v", "sum"), t=("t_x_peso", "sum"), pt=("peso_t", "sum"),
    )
    out = pd.DataFrame({
        "corredor_id": g["corredor_id"],
        "fecha": g["fecha"].dt.strftime("%Y-%m-%d"),
        "hora": g["HORA"].astype(int),
        "velocidad_gt_kmh": (g["v"] / g["pv"].where(g["pv"] > 0)).round(2),
        "tiempo_viaje_min": (g["t"] / g["pt"].where(g["pt"] > 0)).round(2),
    }).sort_values(["corredor_id", "fecha", "hora"]).reset_index(drop=True)
    out.to_csv(PROCESSED / "tiempo_viaje_gt.csv", index=False, encoding="utf-8")
    return out


if __name__ == "__main__":
    cat = catalogo_corredores()
    print(cat.drop(columns=["fuente_longitud", "geometria_wkt"]).to_string())
    assert cat["corredor_id"].is_unique
    assert cat["corredor_id"].str.fullmatch(r"[A-Z0-9_]+").all()
    assert cat["alias_direccion"].notna().all()
    assert (cat["longitud_km"] > 0).all()
    print("\nCatálogo: pruebas de aceptación OK ✔")

    gt = tiempo_viaje_gt()
    assert gt["corredor_id"].isin(cat["corredor_id"]).all()
    assert not gt.duplicated(["corredor_id", "fecha", "hora"]).any()
    assert gt["hora"].between(0, 23).all()
    assert gt["velocidad_gt_kmh"].dropna().between(1, 120).all()
    print(f"\ntiempo_viaje_gt: {len(gt):,} filas · {gt['fecha'].min()} a {gt['fecha'].max()} · "
          f"horas {gt['hora'].min()} a {gt['hora'].max()} · {gt['corredor_id'].nunique()} corredores")
    print(gt.groupby("corredor_id")[["velocidad_gt_kmh", "tiempo_viaje_min"]].mean().round(1).to_string())
    print("\ntiempo_viaje_gt: pruebas OK ✔")
