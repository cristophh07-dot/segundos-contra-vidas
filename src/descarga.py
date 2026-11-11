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
import time
import os
import io
import pathlib
import zipfile

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.fuentes import FUENTES

CACHE = pathlib.Path("data/cache")
CACHE.mkdir(parents=True, exist_ok=True)
HEADERS = {"User-Agent": "hackathon-itm-2026"}

# Sesión con reintentos automáticos: si falla la conexión o el DNS (pasa a veces
# en la primera petición), espera 1, 2, 4, 8... segundos y vuelve a intentar.
_reintentos = Retry(total=6, connect=6, read=3, backoff_factor=1,
                    status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET", "HEAD"])
SESION = requests.Session()
SESION.headers.update(HEADERS)
SESION.mount("https://", HTTPAdapter(max_retries=_reintentos))
SESION.mount("http://", HTTPAdapter(max_retries=_reintentos))


def _descargar(url: str, destino: pathlib.Path) -> None:
    """Descarga `url` y la deja en `destino` de forma segura aunque dos notebooks la pidan a la vez.

    - Cada proceso escribe en su propio archivo temporal y, al terminar, lo pone en `destino` de un
      solo golpe (os.replace): nadie puede leer un archivo a medio descargar.
    - Si otro proceso ya está descargando el mismo archivo (hay un `.lock` reciente), se espera a que
      termine en vez de descargarlo dos veces.
    - En Windows, el antivirus puede tener el archivo abierto unos segundos: se reintenta.
    """
    candado = destino.with_name(destino.name + ".lock")
    propio, avisado = False, False
    while not propio:
        try:
            os.close(os.open(candado, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
            propio = True
        except FileExistsError:
            try:
                viejo = time.time() - candado.stat().st_mtime > 180      # quedó de una corrida interrumpida
            except FileNotFoundError:
                continue
            if viejo:
                try:
                    candado.unlink()
                except OSError:
                    pass
                continue
            if not avisado:
                print(f"Otro notebook ya está descargando {destino.name}; se espera a que termine…")
                avisado = True
            time.sleep(2)
            if destino.exists():
                return
    tmp = destino.with_name(f"{destino.name}.{os.getpid()}.part")
    try:
        if destino.exists():                                             # lo dejó listo el otro proceso
            return
        with SESION.get(url, stream=True, timeout=600) as r:
            r.raise_for_status()
            with open(tmp, "wb") as f:
                for bloque in r.iter_content(chunk_size=1 << 20):
                    f.write(bloque)
                    os.utime(candado)                                    # el candado sigue vivo
        for intento in range(30):
            try:
                os.replace(tmp, destino)
                return
            except PermissionError:
                if intento == 29:
                    raise PermissionError(
                        f"Windows no deja guardar {destino.name}: otro programa lo tiene abierto (por ejemplo "
                        "el antivirus, u otro notebook corriendo a la vez). Cierre los demás notebooks, espere "
                        "un momento y vuelva a correr la celda.") from None
                time.sleep(2)
    finally:
        for sobrante in (tmp, candado):
            try:
                sobrante.unlink(missing_ok=True)
            except OSError:
                pass


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
        r = SESION.get(url, params=params, timeout=120)
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
    Ejemplos: leer("victimas_medata") · leer("velocidad_simm", usecols=["corredor", "hora", "intensidad"])
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
        tmp = destino.with_name(f"{destino.name}.{os.getpid()}.part")
        df.to_csv(tmp, index=False)
        os.replace(tmp, destino)                                         # nadie lee un archivo a medias
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
