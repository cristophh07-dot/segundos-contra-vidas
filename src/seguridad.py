"""src/seguridad.py — limpieza de datos de seguridad vial (Josué)."""
from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd

from src.descarga import leer

PROCESSED = pathlib.Path("data/processed")
PROCESSED.mkdir(parents=True, exist_ok=True)

LAT_MIN, LAT_MAX = 6.1, 6.4
LON_MIN, LON_MAX = -75.75, -75.45


def sin_tildes(s: pd.Series) -> pd.Series:
    return s.astype("string").str.normalize("NFKD").str.encode("ascii", "ignore").str.decode("ascii")


def a_fecha(s: pd.Series) -> pd.Series:
    """Texto d/mm/aaaa -> datetime (NaT si no se puede)."""
    return pd.to_datetime(s, format="%d/%m/%Y", errors="coerce")


def a_hora(s: pd.Series) -> pd.Series:
    """'13:58:00' -> 13 (entero 0-23, vacío si no se puede)."""
    h = pd.to_numeric(s.astype(str).str.extract(r"^\s*(\d{1,2})\s*:")[0], errors="coerce")
    return h.where(h.between(0, 23)).astype("Int64")


def limpiar_coords(lat: pd.Series, lon: pd.Series):
    """Fuera de Medellín o vacías -> vacías (la fila NO se borra)."""
    ok = lat.between(LAT_MIN, LAT_MAX) & lon.between(LON_MIN, LON_MAX)
    return lat.where(ok), lon.where(ok)


def mapear_clase(s: pd.Series) -> pd.Series:
    t = sin_tildes(s).str.upper().str.strip()
    out = pd.Series("otro", index=s.index, dtype="object")
    out[t.str.contains("CHOQUE", na=False)] = "choque"
    out[t.str.contains("ATROPELL", na=False)] = "atropello"
    out[t.str.contains("VOLCA", na=False)] = "volcamiento"
    out[t.str.contains("CAIDA", na=False)] = "caida_ocupante"
    out[t.str.contains("INCENDIO", na=False)] = "incendio"
    out[t.isna()] = np.nan
    return out


def mortalidad_distrito() -> pd.DataFrame:
    raw = leer("mortalidad_distrito")
    lat = pd.to_numeric(raw["lat_wgs84"], errors="coerce")
    lon = pd.to_numeric(raw["lon_wgs84"], errors="coerce")
    lat, lon = limpiar_coords(lat, lon)

    edad = pd.to_numeric(raw["edad_fallecido"], errors="coerce")
    edad = edad.where(edad.between(0, 110)).astype("Int64")

    sexo = raw["sexo_fallecido"].astype("string").str.strip().str.upper().str[:1]
    sexo = sexo.where(sexo.isin(["F", "M"]))

    df = pd.DataFrame({
        "id": raw["id"].astype("string").str.strip(),
        "fecha": a_fecha(raw["fecha_ocurrencia"]),
        "hora": a_hora(raw["hora_ocurrencia"]),
        "clase": mapear_clase(raw["clase"]),
        "edad": edad,
        "sexo": sexo,
        "comuna": raw["nom_comuna"].astype("string").str.strip(),
        "lat": lat,
        "lon": lon,
        "corredor_id": pd.Series(np.nan, index=raw.index, dtype="object"),
    })

    n0 = len(df)
    df = df.drop_duplicates()
    n_dup = n0 - len(df)
    n1 = len(df)
    df = df[df["fecha"].notna()].copy()
    n_sin_fecha = n1 - len(df)
    print(f"mortalidad_distrito: {n0} filas leídas | duplicados eliminados: {n_dup} | "
          f"sin fecha válida eliminados: {n_sin_fecha} | final: {len(df)}")

    df["fecha"] = df["fecha"].dt.strftime("%Y-%m-%d")
    df.to_csv(PROCESSED / "mortalidad_distrito.csv", index=False, encoding="utf-8")
    return df
