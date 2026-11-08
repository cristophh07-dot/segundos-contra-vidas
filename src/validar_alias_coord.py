"""
src/validar_alias_coord.py — identifica con qué número de vía aparece cada corredor, usando coordenadas.

Para cada corredor toma las víctimas de victimas_medata que ocurrieron a menos de RADIO_M metros de
sus sensores del SIMM y cuenta qué números de calle o carrera aparecen en sus direcciones. El número
que aparece en una parte grande de esas direcciones es la vía del corredor. Si una vía cambia de número
entre tramos, aparecen dos números altos.

Uso (desde la carpeta principal del repo):  python -m src.validar_alias_coord
Escribe docs/validacion_alias_coord.txt. Pega ese archivo en el chat.
Solo lee con src.descarga.leer(); no modifica datos.
"""
import pathlib
import re
from collections import Counter

import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree

from src.descarga import leer
from src.velocidad import CORREDORES

# Las coordenadas del SIMM vienen en metros. Hipótesis: MAGNA-SIRGAS / Colombia Bogotá (EPSG:3116).
# El script la comprueba: si los sensores no caen en Medellín al convertirlos, se detiene.
CRS_METROS = 3116
RADIO_M = 100
SALIDA = pathlib.Path("docs/validacion_alias_coord.txt")
EXTRAS = {"LAS_VEGAS (fuera de los 12, para contraste)": "Avenida Las Vegas"}

# Un token es "CR 80", "CL 44" o "CR 43 A". Una sigla de vía (CR, CL, DG...) no cuenta como letra de sufijo.
NO_SUFIJO = "CR|CL|DG|TV|AV|CQ|AC|AK|AU"
TOKEN = re.compile(r"\b(?:CR|CL)\s\d+(?:\s(?!(?:%s)(?:\s|$))[A-Z]{1,2}(?=\s|$))?" % NO_SUFIJO)

lineas = []


def log(txt=""):
    print(txt)
    lineas.append(str(txt))


def numero(serie):
    return pd.to_numeric(serie.astype(str).str.replace(",", ".", regex=False), errors="coerce")


def en_medellin(lat, lon):
    return (lat > 6.0) & (lat < 6.5) & (lon > -75.8) & (lon < -75.3)


def cargar_sensores():
    df = leer("velocidad_simm", usecols=["corredor", "carril", "longitud", "latitud"])
    df["corredor"] = df["corredor"].astype(str).str.strip()
    df["x"] = numero(df["longitud"])
    df["y"] = numero(df["latitud"])
    df = df.dropna(subset=["x", "y"]).drop_duplicates(["corredor", "carril"]).reset_index(drop=True)
    lon, lat = Transformer.from_crs(CRS_METROS, 4326, always_xy=True).transform(df["x"].values, df["y"].values)
    dentro = float(en_medellin(lat, lon).mean())
    log(f"Sensores únicos: {len(df):,} · dentro de Medellín tras convertir (EPSG:{CRS_METROS}): {dentro:.0%}")
    if dentro < 0.95:
        raise ValueError("La conversión no cae en Medellín: hay que probar otro sistema de coordenadas.")
    return df


def cargar_victimas():
    v = leer("victimas_medata", usecols=lambda c: any(k in str(c).lower() for k in ("direccion", "lat", "lon")))
    log(f"Columnas usadas de victimas_medata: {list(v.columns)}")
    c_dir = [c for c in v.columns if "direccion" in str(c).lower()]
    c_lat = [c for c in v.columns if "lat" in str(c).lower()]
    c_lon = [c for c in v.columns if "lon" in str(c).lower()]
    if len(c_dir) != 1 or len(c_lat) != 1 or len(c_lon) != 1:
        raise KeyError(f"No pude identificar dirección y coordenadas: {list(v.columns)}")
    v = pd.DataFrame({
        "direccion": v[c_dir[0]].astype(str).str.upper().str.strip(),
        "lat": numero(v[c_lat[0]]),
        "lon": numero(v[c_lon[0]]),
    }).dropna(subset=["lat", "lon"])
    v = v[en_medellin(v["lat"], v["lon"])].reset_index(drop=True)
    log(f"Víctimas con coordenadas dentro de Medellín: {len(v):,}")
    return v


def analizar(nombre, nombre_simm, sens, vic, pts):
    s = sens[sens["corredor"] == nombre_simm]
    log(f"\n== {nombre} (SIMM: '{nombre_simm}') · sensores: {len(s)}")
    if s.empty:
        log("   sin sensores con ese nombre")
        return
    distancia, _ = cKDTree(s[["x", "y"]].values).query(pts)
    cerca = vic[distancia <= RADIO_M]
    n = len(cerca)
    log(f"   víctimas a menos de {RADIO_M} m de algún sensor: {n:,}")
    if n == 0:
        return
    conteo = Counter()
    for dire in cerca["direccion"]:
        conteo.update(set(TOKEN.findall(dire)))
    for tok, c in conteo.most_common(6):
        marca = "  <--" if c / n >= 0.30 else ""
        log(f"   {tok}: {c:,} ({c / n:.0%}){marca}")
    log("   ejemplos: " + " | ".join(cerca["direccion"].drop_duplicates().head(4).tolist()))


def main():
    sens = cargar_sensores()
    vic = cargar_victimas()
    x, y = Transformer.from_crs(4326, CRS_METROS, always_xy=True).transform(vic["lon"].values, vic["lat"].values)
    pts = np.column_stack([x, y])
    for cid, (_, alias, nombre_simm) in CORREDORES.items():
        analizar(f"{cid} (alias actual: {alias})", nombre_simm, sens, vic, pts)
    for nombre, nombre_simm in EXTRAS.items():
        analizar(nombre, nombre_simm, sens, vic, pts)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("\n".join(lineas), encoding="utf-8")
    print(f"\nReporte guardado en {SALIDA}")


if __name__ == "__main__":
    main()
