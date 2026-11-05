"""
src/descarga.py — lectura de datos SIEMPRE desde la URL de src/fuentes.py.

Uso:
    from src.descarga import leer
    df = leer("victimas_medata")

- La primera vez descarga a data/cache/ (no se sube al repo). Después reutiliza la caché.
- Si se borra data/cache/, todo se vuelve a descargar desde las URLs.
- forzar=True vuelve a descargar aunque exista la caché.
"""
from __future__ import annotations

import hashlib
import io
import pathlib
import zipfile

import pandas as pd
import requests

from src.fuentes import FUENTES

CACHE = pathlib.Path("data/cache")
CACHE.mkdir(parents=True, exist_ok=True)
HEADERS = {"User-Agent": "hackathon-itm-2026"}


def _descargar(url: str, destino: pathlib.Path) -> None:
    with requests.get(url, headers=HEADERS, stream=True, timeout=600) as r:
        r.raise_for_status()
        tmp = destino.with_suffix(destino.suffix + ".part")
        with open(tmp, "wb") as f:
            for bloque in r.iter_content(chunk_size=1 << 20):
                f.write(bloque)
        tmp.rename(destino)


def _verificar_sha256(ruta: pathlib.Path, esperado: str | None) -> None:
    if not esperado:
        return
    h = hashlib.sha256(ruta.read_bytes()).hexdigest()
    if h != esperado:
        raise ValueError(f"El archivo {ruta.name} no coincide con el sha256 esperado. Bórralo de data/cache y vuelve a correr.")


def _leer_csv(fuente, **kwargs):
    """Detecta separador (',' o ';') y codificación (utf-8 o latin-1).
    Acepta los argumentos de pd.read_csv (usecols, chunksize, nrows, decimal...).
    Con chunksize devuelve un iterador de DataFrames en vez de un DataFrame."""
    if "sep" not in kwargs:
        with open(fuente, "rb") as f:
            primera = f.readline().decode("latin-1")
        kwargs["sep"] = ";" if primera.count(";") > primera.count(",") else ","
    if "encoding" in kwargs:
        return pd.read_csv(fuente, low_memory=False, **kwargs)
    try:
        return pd.read_csv(fuente, encoding="utf-8", low_memory=False, **kwargs)
    except UnicodeDecodeError:
        return pd.read_csv(fuente, encoding="latin-1", low_memory=False, **kwargs)


def _leer_zip(ruta: pathlib.Path, archivo: str | None = None, **kwargs) -> pd.DataFrame:
    with zipfile.ZipFile(ruta) as z:
        nombres = [n for n in z.namelist() if n.lower().endswith((".xlsx", ".xls", ".csv"))]
        if not nombres:
            raise ValueError(f"El zip no trae .xlsx ni .csv: {z.namelist()}")
        nombre = archivo or nombres[0]
        datos = z.read(nombre)
    if nombre.lower().endswith(".csv"):
        tmp = CACHE / pathlib.Path(nombre).name
        tmp.write_bytes(datos)
        return _leer_csv(tmp, **kwargs)
    return pd.read_excel(io.BytesIO(datos), **kwargs)


def _leer_arcgis(url: str) -> pd.DataFrame:
    """Pagina un servicio ArcGIS (máx. 2.000 registros por consulta) y devuelve un DataFrame en WGS84."""
    filas, offset, paso = [], 0, 2000
    while True:
        params = {
            "where": "1=1", "outFields": "*", "outSR": 4326, "f": "geojson",
            "resultOffset": offset, "resultRecordCount": paso, "orderByFields": "objectid",
        }
        r = requests.get(url, params=params, headers=HEADERS, timeout=120)
        r.raise_for_status()
        js = r.json()
        feats = js.get("features", [])
        for ft in feats:
            p = dict(ft.get("properties") or {})
            geom = ft.get("geometry") or {}
            coords = geom.get("coordinates") or [None, None]
            p["lon_wgs84"], p["lat_wgs84"] = coords[0], coords[1]
            filas.append(p)
        if not feats or not js.get("exceededTransferLimit") and not js.get("properties", {}).get("exceededTransferLimit"):
            break
        offset += paso
    return pd.DataFrame(filas)


def leer(nombre: str, forzar: bool = False, **kwargs):
    """Lee la fuente `nombre` de src/fuentes.py desde su URL (con caché local).
    Ejemplos: leer("victimas_medata") · leer("conteo_simm", usecols=["FECHAHORA","VELOCIDAD"], chunksize=500_000)
    · leer("incidentes_itm", archivo="…/Data_Dictionary_Fatal_Road_Traffic.xlsx") para el diccionario."""
    if nombre not in FUENTES:
        raise KeyError(f"'{nombre}' no está en src/fuentes.py. Opciones: {list(FUENTES)}")
    f = FUENTES[nombre]
    if not f.get("url"):
        raise ValueError(f"La fuente '{nombre}' todavía no tiene URL en src/fuentes.py")

    if f["formato"] == "arcgis":
        destino = CACHE / f"{nombre}.csv"
        if destino.exists() and not forzar:
            return pd.read_csv(destino, dtype=str)
        df = _leer_arcgis(f["url"])
        df.to_csv(destino, index=False)
        return df

    destino = CACHE / f"{nombre}.{f['formato']}"
    if forzar or not destino.exists():
        print(f"Descargando {nombre} (~{f.get('tamano_mb')} MB) desde la URL…")
        _descargar(f["url"], destino)
        _verificar_sha256(destino, f.get("sha256"))

    if f["formato"] == "csv":
        return _leer_csv(destino, **kwargs)
    if f["formato"] == "zip":
        return _leer_zip(destino, archivo=kwargs.pop("archivo", f.get("archivo")), **kwargs)
    if f["formato"] == "xlsx":
        return pd.read_excel(destino, **kwargs)
    raise ValueError(f"Formato no soportado: {f['formato']}")


def citar(nombre: str) -> str:
    """Texto de cita para instrucciones.txt y la guía de entrega."""
    f = FUENTES[nombre]
    return f"{f['fuente']}. {f['pagina'] or f['url']}. Licencia: {f['licencia']}."
