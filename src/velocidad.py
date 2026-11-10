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
  Los límites de cada tramo (INICIO y FIN de Google Traffic) están en docs/limites_tramos.txt.
- AV_PALMAS y AV_REGIONAL no tienen un número de vía propio: ubicarlas por coordenadas.
  Las Palmas casi no aparece en las direcciones ("VIA LAS PALMAS KM 8"); en la Regional el número
  más frecuente cerca de sus sensores (CR 62) llega solo al 32 %.
- Los alias de los demás corredores se confirmaron con coordenadas (docs/validacion_alias_coord.txt):
  en las víctimas a menos de 100 m de sus sensores del SIMM, el número aparece entre el 60 % y el 93 %.
  AUT_SUR es la Carrera 50 (no la 48: la Carrera 48 es la Avenida Las Vegas, otro corredor del SIMM).
  AV_33 tiene dos números según el tramo (Calle 33 y Calle 37).
- Una misma carrera o calle recorre toda la ciudad (la Carrera 50 llega hasta la Calle 97 y la 52 hasta
  la 107): para quedarse con el tramo medido hay que filtrar por la calle que cruza.
"""
from __future__ import annotations

import pathlib

import numpy as np
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
    "AV_33": ("Avenida 33", "CL 33|CALLE 33|CL 37|CALLE 37|AV 33|AVENIDA 33", "Avenida 33"),
    "CL_30": ("Calle 30", "CL 30|CALLE 30", "Calle 30"),
    "AV_POBLADO": ("Avenida El Poblado", "CR 43 A|CARRERA 43 A|CARRERA 43A", "Avenida El Poblado"),
    "AV_SAN_JUAN": ("Avenida San Juan", "CL 44|CALLE 44", "San Juan"),
    "AV_ORIENTAL": ("Avenida Oriental", "CR 46|CARRERA 46", "Avenida Oriental"),
    "AV_GUAYABAL": ("Avenida Guayabal", "CR 52|CARRERA 52", "Avenida Guayabal"),
    "AUT_NORTE": ("Autopista Norte", "CR 64 C|CARRERA 64 C|CARRERA 64C", "Autopista Norte"),
    "AUT_SUR": ("Autopista Sur", "CR 50|CARRERA 50", "Autopista Sur"),
    # Regional: no tiene un número propio (el más alto cerca de sus sensores es CR 62, con 32 %).
    # Estos alias son de baja confianza: ubicar por coordenadas.
    "AV_REGIONAL": ("Avenida Regional", "CR 62|CARRERA 62|CR 49|CARRERA 49", "Avenida Regional"),
    "AV_FERROCARRIL": ("Avenida Ferrocarril", "CR 57|CARRERA 57", "Avenida Ferrocarril"),
    "AV_PALMAS": ("Avenida Las Palmas", "LAS PALMAS", "Avenida Las Palmas"),
}

# Caja aproximada de Medellín en grados (lon mín, lon máx, lat mín, lat máx): solo para detectar
# coordenadas mal convertidas o fuera de la ciudad.
BBOX_MEDELLIN = (-75.75, -75.40, 6.10, 6.45)

# Sitios que son extremos de tramos de Google Traffic (INICIO o FIN) y no son cruces de calles.
# Coordenadas WGS84 en grados decimales, (latitud, longitud), ubicadas a mano en un mapa
# (Google Maps: clic derecho sobre el punto y copiar las coordenadas). Anota en el comentario de
# cada una de dónde salió. Mientras un sitio esté en None, el corredor que lo usa no se corta.
SITIOS = {
    "Tugo": (6.187786215142357, -75.58340414980118),  # Google Maps, ubicado a mano (Johan): inicio de la Regional
    "San Juan x Regional": (6.2477074673587545, -75.57970548257146),  # Google Maps, cruce de la Av. San Juan con la Av. Regional (la Regional no tiene número de vía): fin de la Regional y de San Juan
    "CTI": (6.261757414854626, -75.57375758415924),  # Google Maps, ubicado a mano (Johan): inicio de la Autopista Sur
    "Solla": (6.311375800567043, -75.55857839758872),  # Google Maps, ubicado a mano (Johan): inicio de la Autopista Norte
    "Punto Cero": (6.264705174959943, -75.57182229498812),  # Google Maps, ubicado a mano (Johan): fin de la Autopista Norte
    "Sandiego": (6.236490359430701, -75.56862066558021),  # Google Maps, ubicado a mano (Johan): inicio de Las Palmas
    "Chuscalito": (6.216096327935572, -75.55257657239848),  # Google Maps, ubicado a mano (Johan): fin de Las Palmas
    "Industriales": (6.231861354083098, -75.57439526122091),  # Google Maps, ubicado a mano (Johan): fin de la Calle 30
    "Barranquilla": (6.264445, -75.567607),  # Google Maps, ubicado a mano (Johan): inicio del Ferrocarril (confirmó el punto anterior, a 18 m)
    "Villanueva": (6.2532258783749795, -75.56251360175715),  # Google Maps, ubicado a mano (Johan): fin de la Av. Oriental
    "Av. 33 x Autopista Sur": (6.239936, -75.578612),  # Google Maps, ubicado a mano (Johan): inicio de la Av. 33 (la mediana del ITM daba una recta de 3,07 km contra 2,55 km del tramo)
}


def _geometria_simm(simm: pd.DataFrame) -> dict[str, str]:
    """Ubicación de los puntos de medición del SIMM por corredor, como MULTIPOINT WKT en WGS84.

    Las coordenadas del SIMM vienen en metros (EPSG:3116, MAGNA-SIRGAS Colombia Bogotá) con coma
    decimal: longitud = este (x) y latitud = norte (y). Se pasan a grados (EPSG:4326, orden lon lat).
    Son puntos, no una línea, y solo cubren donde hay sensores. Devuelve {nombre del corredor en el
    SIMM: WKT}.
    """
    try:
        from pyproj import Transformer  # viene con geopandas
    except ImportError as e:
        raise ImportError("Falta pyproj (viene con geopandas): pip install -r requirements.txt") from e

    pts = simm[["corredor", "longitud", "latitud"]].drop_duplicates().copy()
    pts["x"] = _numero(pts["longitud"])
    pts["y"] = _numero(pts["latitud"])
    pts = pts.dropna(subset=["x", "y"])

    tr = Transformer.from_crs("EPSG:3116", "EPSG:4326", always_xy=True)
    lon, lat = tr.transform(pts["x"].to_numpy(), pts["y"].to_numpy())
    pts["lon"], pts["lat"] = pd.Series(lon, index=pts.index).round(6), pd.Series(lat, index=pts.index).round(6)

    x0, x1, y0, y1 = BBOX_MEDELLIN
    dentro = pts["lon"].between(x0, x1) & pts["lat"].between(y0, y1)
    print(f"geometria_wkt: {int(dentro.sum())} ubicaciones del SIMM dentro de Medellín · "
          f"{int((~dentro).sum())} descartadas por quedar fuera de la caja de la ciudad")

    geom = {}
    for nombre, g in pts[dentro].groupby("corredor"):
        puntos = sorted(set(zip(g["lon"], g["lat"])))
        geom[nombre] = "MULTIPOINT (" + ", ".join(f"({x:.6f} {y:.6f})" for x, y in puntos) + ")"
    return geom


def catalogo_corredores() -> pd.DataFrame:
    """Catálogo de corredores. Guarda data/processed/catalogo_corredores.csv.

    geometria_wkt: MULTIPOINT con las ubicaciones de los puntos de medición del SIMM de cada corredor
    (WGS84). Google Traffic no trae coordenadas (INICIO y FIN son nombres), así que no hay línea.
    Los puntos cubren solo donde hay sensores, no necesariamente todo el tramo de Google Traffic.
    """
    gt = leer("velocidad_gt", usecols=["CORREDOR", "LONGITUD_KM"])
    gt["corredor_id"] = gt["CORREDOR"].map(TRAMO_A_CORREDOR)
    sin_corredor = sorted(gt.loc[gt["corredor_id"].isna(), "CORREDOR"].unique())
    if sin_corredor:
        raise ValueError(f"Tramos de velocidad_gt sin corredor_id: {sin_corredor}")

    # La longitud de un mismo tramo cambia entre registros: se usa la mediana por tramo
    # y, si el corredor tiene dos sentidos, el promedio de las dos medianas.
    por_tramo = gt.groupby(["corredor_id", "CORREDOR"])["LONGITUD_KM"].median().reset_index()
    longitud = por_tramo.groupby("corredor_id")["LONGITUD_KM"].mean().round(2)

    simm = leer("velocidad_simm", usecols=["corredor", "latitud", "longitud"])
    simm = simm.dropna(subset=["corredor"]).copy()
    simm["corredor"] = simm["corredor"].astype(str).str.strip()
    nombres_simm = set(simm["corredor"].unique())
    geometrias = _geometria_simm(simm)

    filas = []
    for cid, (nombre, alias, nombre_simm) in CORREDORES.items():
        filas.append({
            "corredor_id": cid,
            "nombre": nombre,
            "alias_direccion": alias,
            "longitud_km": float(longitud[cid]),
            "fuente_longitud": "Mediana de LONGITUD_KM por tramo en velocidad_gt (Google Traffic 2017-2020); promedio de sentidos",
            "geometria_wkt": geometrias.get(nombre_simm),
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


# Nombres posibles de las columnas de velocidad_simm (en minúscula). Si el archivo real usa otro,
# el error de _buscar_col lista las columnas y basta con agregar el nombre aquí.
# Columnas reales del archivo: carril, fecha_trafico, fecha, hora, dia, dia_num, mes_num, mes, ano,
# velocidad_km_h, corredor, sentido, operacion, intensidad, categoria_1/2/3, ocupacion, tipo_subsistema,
# longitud, latitud, identificador_f_v, comuna, codigo_comuna, nombre_comuna. No hay columna de sensor:
# el punto de medición se define con latitud + longitud + sentido.
COLS_SIMM = {
    "corredor": ["corredor"],
    "fecha": ["fecha", "fecha_hora", "fechahora", "fecha_y_hora"],
    "hora": ["hora"],  # opcional: si no existe, la hora sale de la fecha
    "velocidad": ["velocidad", "velocidad_km_h", "velocidad_kmh"],
    "intensidad": ["intensidad", "intensidad_vehicular"],
}
V_MAX_VALIDA = 150  # D21: se descartan velocidades 0 y mayores de 150


def _buscar_col(df: pd.DataFrame, clave: str, obligatoria: bool = True):
    mapa = {str(c).strip().lower(): c for c in df.columns}
    for cand in COLS_SIMM[clave]:
        if cand in mapa:
            return mapa[cand]
    if obligatoria:
        raise KeyError(
            f"No encuentro la columna '{clave}' en velocidad_simm. Probé {COLS_SIMM[clave]}. "
            f"Columnas reales: {list(df.columns)}. Agrega el nombre correcto a COLS_SIMM."
        )
    return None


def _numero(serie: pd.Series) -> pd.Series:
    """Convierte a número aceptando coma decimal ('44019,79167')."""
    return pd.to_numeric(serie.astype(str).str.strip().str.replace(",", ".", regex=False), errors="coerce")


def _fechas_simm(serie: pd.Series) -> pd.Series:
    """Fechas mezcladas: texto día/mes/año y números de Excel (días desde 1899-12-30, con coma decimal)."""
    s = serie.astype(str).str.strip()
    es_texto = s.str.contains("/", regex=False)
    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    if es_texto.any():
        try:
            out.loc[es_texto] = pd.to_datetime(s[es_texto], dayfirst=True, format="mixed", errors="coerce")
        except (ValueError, TypeError):  # pandas antiguo sin format="mixed"
            out.loc[es_texto] = pd.to_datetime(s[es_texto], dayfirst=True, errors="coerce")
    dias = _numero(s[~es_texto])
    out.loc[~es_texto] = pd.Timestamp("1899-12-30") + pd.to_timedelta(dias, unit="D")
    return out


def velocidad_corredor_hora() -> pd.DataFrame:
    """Velocidad e intensidad por corredor, fecha y hora, solo desde velocidad_simm (jul-ago 2020).
    Guarda data/processed/velocidad_corredor_hora.csv.

    - Lectura válida: velocidad mayor que 0 y hasta 150 km/h (el archivo no trae indicador de validez).
    - velocidad_media_kmh: promedio de las lecturas válidas ponderado por intensidad; si la intensidad
      válida suma 0 en esa hora, promedio simple.
    - Punto de medición: el archivo no trae columna de sensor (la columna carril es el medidor de cada
      carril), así que se define con latitud + longitud + sentido.
    - intensidad_veh_h: por punto de medición se suman los carriles y luego se promedian los puntos
      (lecturas válidas).
    - motos_veh_h: vacío (el SIMM no tiene columna de motos, D15).
    - n_sensores: puntos de medición con al menos una lectura válida. pct_valido: lecturas válidas /
      lecturas totales.
    Solo entran los corredores del catálogo que coinciden por nombre con el SIMM.
    """
    simm = leer("velocidad_simm")
    c_cor, c_fec = _buscar_col(simm, "corredor"), _buscar_col(simm, "fecha")
    c_hora = _buscar_col(simm, "hora", obligatoria=False)
    c_vel, c_int = (_buscar_col(simm, k) for k in ("velocidad", "intensidad"))

    nombre_a_id = {nombre_simm: cid for cid, (_, _, nombre_simm) in CORREDORES.items()}
    df = pd.DataFrame({
        "corredor_id": simm[c_cor].astype(str).str.strip().map(nombre_a_id),
        "dt": _fechas_simm(simm[c_fec]),
        "sensor": (simm["latitud"].astype(str).str.strip() + "|" + simm["longitud"].astype(str).str.strip()
                   + "|" + simm["sentido"].astype(str).str.strip()),
        "v": _numero(simm[c_vel]),
        "w": _numero(simm[c_int]),
    })
    print(f"velocidad_corredor_hora: carriles distintos = {simm['carril'].nunique()} · "
          f"puntos de medición (lat, lon, sentido) = {df['sensor'].nunique()}")
    if c_hora is not None:
        df["hora"] = pd.to_numeric(simm[c_hora].astype(str).str.split(":").str[0], errors="coerce")

    sin_fecha = int(df["dt"].isna().sum())
    if sin_fecha > 0.005 * len(df):
        raise ValueError(f"{sin_fecha:,} filas con fecha que no se pudo leer: revisa los formatos de la columna '{c_fec}'")
    df = df.dropna(subset=["dt"])
    df["dt"] = df["dt"].dt.round("min")  # evita 18:59:59 por decimales de Excel
    if c_hora is None:
        df["hora"] = df["dt"].dt.hour
    df = df.dropna(subset=["hora"])
    df["hora"] = df["hora"].astype(int)
    df["fecha"] = df["dt"].dt.normalize()

    encontrados = set(df["corredor_id"].dropna().unique())
    faltan = sorted(set(CORREDORES) - encontrados)
    print(f"velocidad_corredor_hora: corredores del catálogo en el SIMM: {len(encontrados)}"
          + (f" · sin datos SIMM: {faltan}" if faltan else ""))
    df = df.dropna(subset=["corredor_id"])  # los otros corredores del SIMM no entran (limitación)

    df["valido"] = df["v"].gt(0) & df["v"].le(V_MAX_VALIDA)
    claves = ["corredor_id", "fecha", "hora"]
    val = df[df["valido"]].copy()

    total = df.groupby(claves).size().rename("n_total")
    n_val = val.groupby(claves).size().rename("n_val")
    n_sensores = val.groupby(claves)["sensor"].nunique().rename("n_sensores")

    # Intensidad: suma de carriles por punto de medición, luego promedio de puntos.
    por_sensor = val.groupby(claves + ["sensor"])["w"].sum(min_count=1).reset_index()
    intensidad = por_sensor.groupby(claves)["w"].mean().rename("intensidad_veh_h")

    # Velocidad ponderada por intensidad (solo lecturas con intensidad positiva); respaldo: promedio simple.
    pos = val[val["w"] > 0].copy()
    pos["vw"] = pos["v"] * pos["w"]
    num = pos.groupby(claves)["vw"].sum()
    den = pos.groupby(claves)["w"].sum()
    ponderada = (num / den).rename("v_pond")
    simple = val.groupby(claves)["v"].mean().rename("v_simple")

    out = pd.concat([total, n_val, n_sensores, intensidad, ponderada, simple], axis=1).reset_index()
    out["velocidad_media_kmh"] = out["v_pond"].fillna(out["v_simple"]).round(2)
    out["intensidad_veh_h"] = out["intensidad_veh_h"].round(2)
    out["n_sensores"] = out["n_sensores"].fillna(0).astype(int)
    out["pct_valido"] = (100 * out["n_val"].fillna(0) / out["n_total"]).round(2)
    out["motos_veh_h"] = float("nan")
    out["fecha"] = out["fecha"].dt.strftime("%Y-%m-%d")
    out = out[["corredor_id", "fecha", "hora", "velocidad_media_kmh", "intensidad_veh_h",
               "motos_veh_h", "n_sensores", "pct_valido"]].sort_values(["corredor_id", "fecha", "hora"]).reset_index(drop=True)
    out.to_csv(PROCESSED / "velocidad_corredor_hora.csv", index=False, encoding="utf-8")
    return out


# =====================================================================
# VELOCIDAD NOCTURNA POR CORREDOR (D21)
# Usa sensores_simm() de src/corredores.py para asignar cada sensor a uno de los 12 corredores.
# =====================================================================
_PROC = pathlib.Path("data/processed")
_DOCS = pathlib.Path("docs")
V_MAX_NOCTURNA = 150          # D21: se descartan velocidades 0 y mayores de 150
LIMITE_KMH = 50               # D18: tope evaluado
Q_P85 = 0.85
HORA_DIA_DESDE, HORA_DIA_HASTA = 6, 20   # franja "dia": 6 <= hora < 20
HORAS_NOCHE = [0, 1, 2, 3, 4, 5, 20, 21, 22, 23]
RAZON_P85_ESPERADA = 1.04     # D20: de noche el p85 sube ~4 %
RAZON_P85_TOLERANCIA = 0.03   # fuera de 1,04 +/- 0,03 se avisa


def _num_simm(serie: pd.Series) -> pd.Series:
    """Número desde texto con coma decimal ('34,5') o desde una columna ya numérica."""
    if pd.api.types.is_numeric_dtype(serie):
        return serie.astype(float)
    return pd.to_numeric(serie.astype(str).str.strip().str.replace(",", ".", regex=False), errors="coerce")


def _col_exacta(df: pd.DataFrame, nombre: str, origen: str):
    for c in df.columns:
        if str(c).strip().lower() == nombre:
            return c
    raise KeyError(f"{origen}: no encuentro la columna '{nombre}'. Columnas reales: {list(df.columns)}")


def _clave_texto(serie: pd.Series) -> pd.Series:
    return serie.astype(str).str.strip().str.upper()


def _clave_carril(serie: pd.Series) -> pd.Series:
    """Carril como texto comparable: 1, 1.0 y '1' dan todos '1'; si no es número, el texto en mayúsculas."""
    s = serie.astype(str).str.strip()
    num = pd.to_numeric(s.str.replace(",", ".", regex=False), errors="coerce")
    entero = num.notna() & (num == num.round())
    out = s.str.upper()
    out[entero] = num[entero].astype("int64").astype(str)
    return out


def velocidad_simm_limpia() -> pd.DataFrame:
    """Mediciones del SIMM de los 12 corredores, a nivel de medición (el Monte Carlo aplica el tope de
    50 km/h medición por medición). Une velocidad_simm con sensores_simm() por (corredor, carril).
    Filtros (D21): sin velocidad 0, sin velocidad > 150, sin intensidad <= 0 o faltante.
    Además se quitan las filas sin velocidad numérica (no se pueden ponderar); se cuentan aparte.
    Guarda data/processed/velocidad_simm_limpia.csv."""
    from src.corredores import sensores_simm

    simm = leer("velocidad_simm")
    print(f"velocidad_simm: {len(simm):,} filas")
    c = {n: _col_exacta(simm, n, "velocidad_simm")
         for n in ("corredor", "carril", "fecha", "hora", "velocidad_km_h", "intensidad", "operacion")}

    # La columna fecha viene mezclada: texto día/mes/año y números de Excel con coma decimal.
    # _fechas_simm() (la misma de velocidad_corredor_hora) lee los dos formatos.
    fecha = _fechas_simm(simm[c["fecha"]]).dt.normalize()
    if fecha.isna().any():
        print(f"  AVISO: {int(fecha.isna().sum()):,} filas con fecha que no se pudo leer")

    df = pd.DataFrame({
        "corredor": _clave_texto(simm[c["corredor"]]),
        "carril": _clave_carril(simm[c["carril"]]),
        "fecha": fecha,
        "hora": _num_simm(simm[c["hora"]]),
        "velocidad_km_h": _num_simm(simm[c["velocidad_km_h"]]),
        "intensidad": _num_simm(simm[c["intensidad"]]),
        "operacion": simm[c["operacion"]],
    })
    del simm

    # --- Asignación a los 12 corredores: la de src/corredores.py (no se inventa otra) ---
    sens = sensores_simm()
    s_corr = _col_exacta(sens, "corredor", "sensores_simm()")
    s_car = _col_exacta(sens, "carril", "sensores_simm()")
    s_id = _col_exacta(sens, "corredor_id", "sensores_simm()")
    ids = sens[s_id].astype("string").fillna("").str.strip()
    llave = pd.DataFrame({"corredor": _clave_texto(sens[s_corr]), "carril": _clave_carril(sens[s_car]),
                          "corredor_id": ids})
    llave = llave[(llave["corredor_id"] != "") & (llave["corredor_id"].str.lower() != "nan")]
    llave["corredor_id"] = llave["corredor_id"].astype(str)
    dup = llave.duplicated(["corredor", "carril"], keep=False)
    if dup.any():
        if (llave[dup].groupby(["corredor", "carril"])["corredor_id"].nunique() > 1).any():
            raise ValueError("sensores_simm(): hay (corredor, carril) con más de un corredor_id")
        llave = llave.drop_duplicates(["corredor", "carril"])
    vistos = df[["corredor", "carril"]].drop_duplicates()
    sin_filas = llave.merge(vistos, on=["corredor", "carril"], how="left", indicator=True)
    n_sin = int((sin_filas["_merge"] == "left_only").sum())
    print(f"sensores_simm(): {len(llave):,} sensores con corredor_id; {n_sin:,} no aparecen en velocidad_simm")

    print("\nFiltros:")
    df = df.merge(llave, on=["corredor", "carril"], how="left", validate="many_to_one")
    sin_id = df["corredor_id"].isna()
    print(f"  sin corredor_id (no son uno de los 12 corredores): {int(sin_id.sum()):,} filas fuera")
    df = df[~sin_id].copy()
    if df.empty:
        raise ValueError("Ninguna fila de velocidad_simm quedó asignada a un corredor: revisa la unión por "
                         "(corredor, carril) con sensores_simm()")
    print(f"  quedan {len(df):,} filas de los 12 corredores")
    print("\nDistribución de 'operacion' (sin filtrar), filas de los 12 corredores:")
    print(df["operacion"].value_counts(dropna=False).to_string())
    print()

    def quitar(d: pd.DataFrame, mascara: pd.Series, texto: str) -> pd.DataFrame:
        print(f"  filtro {texto}: quita {int(mascara.sum()):,} filas")
        return d[~mascara]

    df = quitar(df, df["velocidad_km_h"].isna(), "velocidad faltante o no numérica (no está en D21; no se puede ponderar)")
    df = quitar(df, df["velocidad_km_h"] == 0, "velocidad_km_h == 0")
    df = quitar(df, df["velocidad_km_h"] > V_MAX_NOCTURNA, f"velocidad_km_h > {V_MAX_NOCTURNA}")
    df = quitar(df, df["intensidad"].isna() | (df["intensidad"] <= 0), "intensidad <= 0 o faltante")
    print(f"  quedan {len(df):,} filas")
    bajas = int((df["velocidad_km_h"] < 1).sum())
    if bajas:
        print(f"  OJO: {bajas:,} filas con velocidad entre 0 y 1 km/h (o negativa) siguen dentro: no es un filtro de D21")

    hora = df["hora"]
    mala = hora.isna() | (hora != hora.round()) | (hora < 0) | (hora > 23)
    if mala.any():
        raise ValueError(f"{int(mala.sum()):,} filas con hora fuera de 0-23 o no entera: hay que decidir qué hacer con ellas")
    df["hora"] = hora.astype(int)
    df["franja"] = np.where((df["hora"] >= HORA_DIA_DESDE) & (df["hora"] < HORA_DIA_HASTA), "dia", "noche")

    out = (df[["corredor_id", "carril", "fecha", "hora", "franja", "velocidad_km_h", "intensidad"]]
           .sort_values(["corredor_id", "fecha", "hora", "carril"]).reset_index(drop=True))
    _PROC.mkdir(parents=True, exist_ok=True)
    out.to_csv(_PROC / "velocidad_simm_limpia.csv", index=False, encoding="utf-8")
    fmin, fmax = out["fecha"].min(), out["fecha"].max()
    print(f"\nvelocidad_simm_limpia: {len(out):,} filas · día {int((out['franja'] == 'dia').sum()):,} · "
          f"noche {int((out['franja'] == 'noche').sum()):,} · fechas {fmin:%Y-%m-%d} a {fmax:%Y-%m-%d}"
          if pd.notna(fmin) else f"\nvelocidad_simm_limpia: {len(out):,} filas")
    return out


def _p_ponderado(v: np.ndarray, w: np.ndarray, q: float = Q_P85) -> float:
    """Percentil q ponderado por intensidad: la menor velocidad cuyo peso acumulado alcanza q del total
    (sin interpolar)."""
    if len(v) == 0:
        return float("nan")
    orden = np.argsort(v, kind="stable")
    v, w = v[orden], w[orden]
    acum = np.cumsum(w)
    i = int(np.searchsorted(acum, q * acum[-1], side="left"))
    return float(v[min(i, len(v) - 1)])


def _medidas(g: pd.DataFrame) -> dict:
    v = g["velocidad_km_h"].to_numpy(dtype=float)
    w = g["intensidad"].to_numpy(dtype=float)
    total = float(w.sum())
    return {
        "n_mediciones": int(len(g)),
        "intensidad_total": total,
        "v_media_ponderada": float((v * w).sum() / total),
        "p85": _p_ponderado(v, w, Q_P85),
        "pct_sobre_50": float(100 * w[v > LIMITE_KMH].sum() / total),
    }


def _tabla_medidas(df: pd.DataFrame, claves: list[str]) -> pd.DataFrame:
    filas = []
    for k, g in df.groupby(claves, sort=True):
        k = k if isinstance(k, tuple) else (k,)
        fila = dict(zip(claves, k))
        fila.update(_medidas(g))
        filas.append(fila)
    out = pd.DataFrame(filas)
    for col in ("v_media_ponderada", "p85", "pct_sobre_50"):
        out[col] = out[col].round(4)
    return out


def perfil_horario_corredor(limpia: pd.DataFrame | None = None) -> pd.DataFrame:
    """Mismas medidas por corredor_id y hora (0-23), para graficar el perfil del día.
    Guarda data/processed/perfil_horario_corredor.csv."""
    if limpia is None:
        limpia = velocidad_simm_limpia()
    out = _tabla_medidas(limpia, ["corredor_id", "hora"])
    _PROC.mkdir(parents=True, exist_ok=True)
    out.to_csv(_PROC / "perfil_horario_corredor.csv", index=False, encoding="utf-8")
    return out


def velocidad_nocturna_corredor(limpia: pd.DataFrame | None = None) -> pd.DataFrame:
    """Una fila por corredor_id y franja (dia, noche): n_mediciones, intensidad_total, v_media_ponderada,
    p85, pct_sobre_50 (ponderados por intensidad) y, por corredor, razon_noche_dia_media y
    razon_noche_dia_p85 (se repiten en las dos filas del corredor; vacías si falta una franja).
    Guarda data/processed/velocidad_nocturna_corredor.csv y también perfil_horario_corredor.csv."""
    if limpia is None:
        limpia = velocidad_simm_limpia()
    out = _tabla_medidas(limpia, ["corredor_id", "franja"])
    idx = out.set_index(["corredor_id", "franja"])

    def razon(cid: str, col: str) -> float:
        try:
            return float(idx.loc[(cid, "noche"), col] / idx.loc[(cid, "dia"), col])
        except KeyError:
            return float("nan")

    out["razon_noche_dia_media"] = out["corredor_id"].map(lambda c: razon(c, "v_media_ponderada")).round(4)
    out["razon_noche_dia_p85"] = out["corredor_id"].map(lambda c: razon(c, "p85")).round(4)
    _PROC.mkdir(parents=True, exist_ok=True)
    out.to_csv(_PROC / "velocidad_nocturna_corredor.csv", index=False, encoding="utf-8")
    perfil_horario_corredor(limpia)
    return out


def _p4_autopista_sur() -> str:
    """P4: ¿la Autopista Sur aparece en el norte de la ciudad con alias CR 62-63? Una línea, con los números."""
    import re

    from src.corredores import CORREDORES as _C
    from src.corredores import sensores_simm

    sens = sensores_simm()
    cols = {str(c).strip().lower(): c for c in sens.columns}
    c_id = cols.get("corredor_id")
    c_lat = next((cols[k] for k in ("lat", "latitud", "lat_wgs84", "latitude") if k in cols), None)
    c_lon = next((cols[k] for k in ("lon", "longitud", "lon_wgs84", "longitude") if k in cols), None)
    if c_id is None or c_lat is None or c_lon is None:
        return f"P4: no se pudo comprobar: sensores_simm() no trae corredor_id/latitud/longitud (columnas: {list(sens.columns)})."
    lat, lon = _num_simm(sens[c_lat]), _num_simm(sens[c_lon])
    if lat.abs().max() > 1000:   # vienen en metros (MAGNA-SIRGAS Bogotá, EPSG:3116): x = longitud, y = latitud
        from pyproj import Transformer
        ok = lat.notna() & lon.notna()
        x, y = Transformer.from_crs("EPSG:3116", "EPSG:4326", always_xy=True).transform(
            lon[ok].to_numpy(), lat[ok].to_numpy())
        lat_g, lon_g = pd.Series(np.nan, index=sens.index), pd.Series(np.nan, index=sens.index)
        lon_g[ok], lat_g[ok] = x, y
        lat = lat_g
    ids = sens[c_id].astype("string").fillna("").str.strip()

    def rango(cid: str):
        m = (ids == cid) & lat.notna()
        return (float(lat[m].min()), float(lat[m].max()), int(m.sum())) if m.any() else None

    sur, norte = rango("AUT_SUR"), rango("AUT_NORTE")
    if sur is None:
        return "P4: no se pudo comprobar: sensores_simm() no tiene sensores con corredor_id AUT_SUR."
    texto = f"P4: AUT_SUR tiene {sur[2]} sensores entre latitud {sur[0]:.4f} y {sur[1]:.4f}"
    if norte is None:
        texto += "; no hay sensores de AUT_NORTE para comparar"
    else:
        al_norte = int(((ids == "AUT_SUR") & (lat >= norte[0])).sum())
        texto += (f"; AUT_NORTE va de {norte[0]:.4f} a {norte[1]:.4f} → "
                  + ("NO aparece en el norte (todos sus sensores quedan al sur del sensor más al sur de AUT_NORTE)"
                     if al_norte == 0 else f"SÍ: {al_norte} de sus sensores quedan al norte del sensor más al sur de AUT_NORTE"))
    alias = str(_C.get("AUT_SUR")) if hasattr(_C, "get") else ""
    tiene = re.search(r"(?:CR|CARRERA)\s?6[23]\b", alias.upper()) is not None
    texto += f"; el alias de AUT_SUR en CORREDORES {'SÍ' if tiene else 'NO'} contiene CR 62-63 ({alias})."
    return texto


def _pruebas_nocturna() -> None:
    """Pruebas de aceptación de la velocidad nocturna. Escribe docs/velocidad_nocturna.txt."""
    from src.corredores import CORREDORES as _C

    print("\n=== Velocidad nocturna por corredor (D21) ===")
    limpia = velocidad_simm_limpia()
    franja = velocidad_nocturna_corredor(limpia)
    horas = perfil_horario_corredor(limpia)
    todo_ok = True
    avisos: list[str] = []
    notas: list[str] = []

    ids12 = list(_C.keys()) if hasattr(_C, "keys") else list(_C)
    if not all(isinstance(i, str) for i in ids12):
        ids12 = sorted(limpia["corredor_id"].unique())
    noche = limpia[limpia["franja"] == "noche"]
    n_med = noche.groupby("corredor_id").size()
    n_sen = noche.groupby("corredor_id")["carril"].nunique()
    n_sen_total = limpia.groupby("corredor_id")["carril"].nunique()
    con_noche = [c for c in ids12 if c in n_med.index]
    sin_noche = [c for c in ids12 if c not in n_med.index]
    print(f"\n1) Corredores con mediciones de noche: {len(con_noche)} de {len(ids12)}")
    for c in ids12:
        if c in n_med.index:
            print(f"   {c:15s} {int(n_med[c]):>8,} mediciones · {int(n_sen[c])} sensores (carriles) de noche "
                  f"· {int(n_sen_total[c])} en total")
    if sin_noche:
        msg = f"SIN mediciones de noche (no se rellena): {sin_noche}"
        print("   " + msg)
        avisos.append(msg)
        todo_ok = False

    print("\n2) Horas de noche (0-5 y 20-23) con datos, por corredor:")
    for c in con_noche:
        presentes = set(horas.loc[horas["corredor_id"] == c, "hora"].tolist())
        faltan = [h for h in HORAS_NOCHE if h not in presentes]
        if faltan:
            msg = f"{c}: faltan las horas {faltan}"
            avisos.append(msg)
            todo_ok = False
        else:
            msg = f"{c}: las 10 horas de noche tienen datos"
        print("   " + msg)

    dia_g = limpia[limpia["franja"] == "dia"]
    if len(noche) and len(dia_g):
        md, mn = _medidas(dia_g), _medidas(noche)
        r85, rmed = mn["p85"] / md["p85"], mn["v_media_ponderada"] / md["v_media_ponderada"]
        print("\n3) Razón noche/día, 12 corredores juntos (ponderada por intensidad):")
        print(f"   p85: día {md['p85']:.1f} · noche {mn['p85']:.1f} · razón {r85:.3f} ({(r85 - 1) * 100:+.1f} %)")
        print(f"   media: día {md['v_media_ponderada']:.1f} · noche {mn['v_media_ponderada']:.1f} · razón {rmed:.3f} ({(rmed - 1) * 100:+.1f} %)")
        resol = 1.0 / md["p85"]  # el p85 viene en km/h enteros: 1 km/h es esta fracción del p85
        if round(abs(r85 - 1), 3) <= round(resol, 3):
            lectura = "igual de día y de noche (la diferencia queda dentro de la resolución de 1 km/h)"
        else:
            lectura = "distinta de día y de noche (la diferencia supera la resolución de 1 km/h)"
        notas.append(
            f"Nota de lectura (p85): los km/h son enteros, así que 1 km/h equivale a ~{resol * 100:.0f} % del p85. "
            f"La razón noche/día del p85 es {r85:.3f}: la velocidad alta (p85) es {lectura}."
        )
        notas.append(
            f"Nota de lectura (media): la media ponderada es continua y no tiene esa limitación; "
            f"{'bajó' if rmed < 1 else 'subió'} {abs(rmed - 1) * 100:.1f} % de noche en el periodo medido "
            f"(2020, pandemia), así que no se describe como 'igual'."
        )
        for n in notas:
            print("   " + n)
        por_c = franja.drop_duplicates("corredor_id")[["corredor_id", "razon_noche_dia_media", "razon_noche_dia_p85"]]
        print("\n   Razón por corredor:")
        print(por_c.to_string(index=False))

    pcts = pd.concat([franja["pct_sobre_50"], horas["pct_sobre_50"]])
    ok_pct = bool(pcts.between(0, 100).all())
    cols_v = ["v_media_ponderada", "p85"]
    vs = pd.concat([franja[c] for c in cols_v] + [horas[c] for c in cols_v])
    ok_v = bool(vs.between(1, V_MAX_NOCTURNA).all())
    n_fuera = int((~limpia["velocidad_km_h"].between(1, V_MAX_NOCTURNA)).sum())
    print("\n4) Rangos:")
    print(f"   porcentajes entre 0 y 100: {'✔' if ok_pct else '✘'}")
    print(f"   medias y p85 entre 1 y {V_MAX_NOCTURNA} km/h: {'✔' if ok_v else '✘'}")
    print(f"   mediciones limpias con velocidad fuera de 1-{V_MAX_NOCTURNA}: {n_fuera:,} {'✔' if n_fuera == 0 else '✘'}")
    if not (ok_pct and ok_v and n_fuera == 0):
        todo_ok = False
        avisos.append("Algún rango no se cumple (ver punto 4)")

    p4 = _p4_autopista_sur()
    print("\n" + p4)

    fmin, fmax = limpia["fecha"].min(), limpia["fecha"].max()
    periodo = f"{fmin:%Y-%m-%d} a {fmax:%Y-%m-%d}" if pd.notna(fmin) else "periodo no determinado"
    texto = "\n".join([
        "Velocidad nocturna por corredor (D21)",
        "=" * 60,
        f"Fuente: velocidad_simm (SIMM), periodo medido: {periodo} (según la columna fecha), 24 horas.",
        "Franjas: dia = 6 <= hora < 20; noche = las demás horas (20-23 y 0-5).",
        "Medidas ponderadas por intensidad, sin velocidades 0 ni mayores de 150 km/h y sin intensidad <= 0 o faltante.",
        "p85 ponderado: la menor velocidad cuyo peso acumulado alcanza el 85 % de la intensidad (sin interpolar).",
        "pct_sobre_50: % de la intensidad medida a más de 50 km/h.",
        "",
        "ADVERTENCIA: las mediciones son de 2020, con restricciones por la pandemia (D19: cuarentena mar-ago 2020, "
        "velocidades ~29 % más altas). El nivel absoluto de velocidad puede estar inflado respecto a un año normal; "
        "lo que se usa es la razón noche/día (razon_noche_dia_media y razon_noche_dia_p85), no los niveles.",
        "",
        *(notas + [""] if notas else []),
        "Tabla por corredor y franja:",
        franja.to_string(index=False),
        "",
        ("Avisos: " + " | ".join(avisos)) if avisos else "Avisos: ninguno.",
        "",
        p4,
    ])
    _DOCS.mkdir(exist_ok=True)
    (_DOCS / "velocidad_nocturna.txt").write_text(texto + "\n", encoding="utf-8")
    print("\nResumen guardado en docs/velocidad_nocturna.txt")
    print("Pruebas de velocidad nocturna: todo bien ✔" if todo_ok else "Pruebas de velocidad nocturna: REVISAR los avisos de arriba")


# ---------------------------------------------------------------------------
# Costo en tiempo de un límite de velocidad (Tarea 5)
# ---------------------------------------------------------------------------
VIAS_RAPIDAS = ("AV_REGIONAL", "AUT_NORTE", "AUT_SUR", "AV_PALMAS")  # D18: vías de flujo continuo
FRANJAS_GT = {"pico_am": range(6, 9), "valle": range(9, 17), "pico_pm": range(17, 20)}
HORA_A_FRANJA = {h: f for f, horas in FRANJAS_GT.items() for h in horas}
LIMITES_ESCENARIO = {"limite_50": 50.0, "limite_40": 40.0}
ANIOS_COSTO = (2017, 2018, 2019)  # D4: ventana de los modelos


def _observaciones_costo() -> pd.DataFrame:
    """Velocidad de Google Traffic por tramo (sentido), fecha y hora de las vías rápidas, 2017-2019.

    Primero promedia las lecturas repetidas de cada tramo y hora (como tiempo_viaje_gt). La longitud
    de cada corredor se define igual que en el catálogo: promedio de las medianas de sus tramos.
    La hora 20 se deja fuera porque pertenece a la franja 'noche', que Google Traffic no cubre.
    """
    gt = leer("velocidad_gt", usecols=["CORREDOR", "FECHA", "HORA", "LONGITUD_KM", "VELOCIDAD_KM/H"])
    gt["corredor_id"] = gt["CORREDOR"].map(TRAMO_A_CORREDOR)
    sin_corredor = sorted(gt.loc[gt["corredor_id"].isna(), "CORREDOR"].unique())
    if sin_corredor:
        raise ValueError(f"Tramos de velocidad_gt sin corredor_id: {sin_corredor}")
    gt["fecha"] = pd.to_datetime(gt["FECHA"], format="%d/%m/%Y", errors="coerce")
    if gt["fecha"].isna().any():
        raise ValueError("Hay fechas de velocidad_gt que no siguen el formato día/mes/año")

    longitud = (gt.groupby(["corredor_id", "CORREDOR"])["LONGITUD_KM"].median()
                  .groupby("corredor_id").mean().round(2))

    obs = gt[gt["corredor_id"].isin(VIAS_RAPIDAS)
             & gt["fecha"].dt.year.isin(list(ANIOS_COSTO))
             & gt["HORA"].isin(list(HORA_A_FRANJA))]
    por_tramo = (obs.groupby(["corredor_id", "CORREDOR", "fecha", "HORA"], as_index=False)["VELOCIDAD_KM/H"]
                    .mean().rename(columns={"VELOCIDAD_KM/H": "v", "HORA": "hora"}))
    por_tramo = por_tramo[por_tramo["v"].notna() & (por_tramo["v"] > 0)].copy()
    por_tramo["franja"] = por_tramo["hora"].map(HORA_A_FRANJA)
    por_tramo["longitud_km"] = por_tramo["corredor_id"].map(longitud)
    return por_tramo.reset_index(drop=True)


def costo_tiempo_escenarios(escenarios=("limite_50",)) -> pd.DataFrame:
    """Segundos extra por viaje que costaría un límite de velocidad en las vías rápidas.
    Guarda data/processed/costo_tiempo_escenarios.csv.

    Para cada tramo, fecha y hora:  v_escenario = min(v_actual, límite)
    segundos_extra = (longitud_km / v_escenario - longitud_km / v_actual) * 3600
    segundos_extra_viaje es el promedio de ese costo en la franja (cada hora pesa igual: Google Traffic
    no trae volumen). Así un límite solo cuesta tiempo en las horas en que hoy se anda por encima.
    No se aplica la fórmula a la velocidad media de la franja: una media por debajo del límite
    esconde las horas en que sí se pasa.
    Franjas: pico_am (6-9), valle (9-17), pico_pm (17-20), con Google Traffic 2017-2019 (D4).
    La franja 'noche' y el escenario nocturno_40 no se calculan (Google Traffic no tiene noche).
    """
    for esc in escenarios:
        if esc not in LIMITES_ESCENARIO:
            raise ValueError(f"Escenario no soportado: {esc}. Opciones: {list(LIMITES_ESCENARIO)}")
    obs = _observaciones_costo()
    partes = []
    for esc in escenarios:
        o = obs.copy()
        o["v_esc"] = o["v"].clip(upper=LIMITES_ESCENARIO[esc])
        o["extra_s"] = (o["longitud_km"] / o["v_esc"] - o["longitud_km"] / o["v"]) * 3600
        g = o.groupby(["corredor_id", "franja"]).agg(
            v_actual_kmh=("v", "mean"),
            v_escenario_kmh=("v_esc", "mean"),
            segundos_extra_viaje=("extra_s", "mean"),
        ).reset_index()
        g["escenario"] = esc
        partes.append(g)
    out = pd.concat(partes, ignore_index=True)
    out["franja"] = pd.Categorical(out["franja"], categories=list(FRANJAS_GT), ordered=True)
    out = out.sort_values(["corredor_id", "escenario", "franja"]).reset_index(drop=True)
    out["franja"] = out["franja"].astype(str)
    cols_num = ["v_actual_kmh", "v_escenario_kmh", "segundos_extra_viaje"]
    out[cols_num] = out[cols_num].round(2)
    out = out[["corredor_id", "franja", "escenario"] + cols_num]
    out.to_csv(PROCESSED / "costo_tiempo_escenarios.csv", index=False, encoding="utf-8")
    return out


def _pruebas_costo() -> None:
    """Pruebas de aceptación del costo en tiempo. Escribe docs/costo_tiempo.txt."""
    print("\n=== Costo en tiempo de un límite de 50 km/h (Tarea 5) ===")
    obs = _observaciones_costo()
    tabla = costo_tiempo_escenarios()

    columnas = ["corredor_id", "franja", "escenario", "v_actual_kmh", "v_escenario_kmh", "segundos_extra_viaje"]
    assert list(tabla.columns) == columnas, f"Columnas distintas al contrato: {list(tabla.columns)}"
    assert set(tabla["corredor_id"]) == set(VIAS_RAPIDAS), "Faltan vías rápidas en el resultado"
    assert set(tabla["franja"]) <= set(FRANJAS_GT), "Franja fuera de las permitidas"
    assert not tabla.duplicated(["corredor_id", "franja", "escenario"]).any(), "Filas duplicadas"
    assert tabla[columnas[3:]].notna().all().all(), "Hay valores vacíos"
    assert (tabla["v_escenario_kmh"] <= tabla["v_actual_kmh"] + 1e-9).all(), "v_escenario mayor que v_actual"
    assert (tabla["segundos_extra_viaje"] >= 0).all(), "Costo negativo"
    print("   Formato del contrato (columnas, sin duplicados ni vacíos, costo >= 0): ✔")

    periodo = f"{obs['fecha'].min():%Y-%m-%d} a {obs['fecha'].max():%Y-%m-%d}"
    print(f"   Observaciones (tramo-hora): {len(obs):,} · {periodo} · horas {int(obs['hora'].min())} a {int(obs['hora'].max())}")

    sobre = ((obs.assign(sobre=obs["v"] > 50.0).groupby(["corredor_id", "franja"])["sobre"].mean() * 100)
             .round(1).unstack()[list(FRANJAS_GT)])
    pivote = tabla.pivot(index="corredor_id", columns="franja", values="segundos_extra_viaje")[list(FRANJAS_GT)]

    g = obs.groupby(["corredor_id", "franja"]).agg(v=("v", "mean"), L=("longitud_km", "first"))
    literal = ((g["L"] / g["v"].clip(upper=50.0) - g["L"] / g["v"]) * 3600).round(2).rename("segundos_formula_literal")
    comp = (tabla.set_index(["corredor_id", "franja"])[["segundos_extra_viaje"]]
            .rename(columns={"segundos_extra_viaje": "segundos_hora_a_hora"}).join(literal).reset_index())

    print("\n   % de observaciones con velocidad sobre 50 km/h:")
    print(sobre.to_string())
    print("\n   Segundos extra por viaje con limite_50:")
    print(pivote.to_string())
    print("\n   Comparación: promedio hora a hora (el que se entrega) contra la fórmula literal a la velocidad media:")
    print(comp.to_string(index=False))

    texto = "\n".join([
        "Costo en tiempo de un límite de velocidad (Tarea 5)",
        "=" * 60,
        "Vías evaluadas: Regional, Autopista Norte, Autopista Sur y Las Palmas (D18: vías de flujo continuo).",
        f"Fuente: velocidad_gt (Google Traffic), {periodo}, horas 6 a 19, todos los días.",
        "Escenario calculado: limite_50 (50 km/h todo el día). limite_40 y la franja noche no se calculan: "
        "pendientes de decisión.",
        "",
        "Método: para cada tramo (sentido), fecha y hora, v_escenario = min(v_actual, límite) y "
        "segundos_extra = (longitud_km / v_escenario - longitud_km / v_actual) x 3600. "
        "segundos_extra_viaje es el promedio de ese costo en la franja; cada hora pesa igual porque "
        "Google Traffic no trae volumen. No se aplica la fórmula a la velocidad media de la franja: una media "
        "por debajo de 50 km/h esconde las horas en que sí se pasa. v_actual_kmh y v_escenario_kmh son los "
        "promedios de las velocidades observadas y de las velocidades con el límite.",
        "",
        "Limitaciones: (1) la velocidad de Google Traffic es la del flujo en el tramo, no la de cada vehículo; "
        "los vehículos más rápidos no se ven, así que el costo real de un límite es mayor: estas cifras son "
        "una cota inferior. (2) La hora 20 pertenece a la franja noche y Google Traffic no la cubre; la franja "
        "noche se omite. (3) Longitud del corredor: promedio de las medianas de sus tramos (la misma del "
        "catálogo). (4) Se usan todos los días de 2017 a 2019 (D4), sin separar fines de semana.",
        "",
        "Tabla (formato del contrato, sección 6.4):",
        tabla.to_string(index=False),
        "",
        "% de observaciones sobre 50 km/h:",
        sobre.to_string(),
        "",
        "Comparación con la fórmula literal a la velocidad media de la franja:",
        comp.to_string(index=False),
    ])
    carpeta = pathlib.Path("docs")
    carpeta.mkdir(exist_ok=True)
    (carpeta / "costo_tiempo.txt").write_text(texto + "\n", encoding="utf-8")
    print("\nResumen guardado en docs/costo_tiempo.txt")
    print("Pruebas de costo en tiempo: todo bien ✔")


if __name__ == "__main__":
    cat = catalogo_corredores()
    print(cat.drop(columns=["fuente_longitud", "geometria_wkt"]).to_string())
    assert cat["corredor_id"].is_unique
    assert cat["corredor_id"].str.fullmatch(r"[A-Z0-9_]+").all()
    assert cat["alias_direccion"].notna().all()
    assert (cat["longitud_km"] > 0).all()
    print("\nCatálogo: pruebas de aceptación OK ✔")

    assert cat["geometria_wkt"].notna().all() and cat["geometria_wkt"].str.startswith("MULTIPOINT").all(), \
        "Algún corredor quedó sin geometría: revisa las coordenadas del SIMM"
    puntos = cat.set_index("corredor_id")["geometria_wkt"].str.count(",") + 1
    print("\ngeometria_wkt: puntos de medición por corredor")
    print(puntos.sort_values().to_string())
    print(f"Ejemplo ({cat['corredor_id'].iloc[0]}): {cat['geometria_wkt'].iloc[0][:90]}…")

    gt = tiempo_viaje_gt()
    assert gt["corredor_id"].isin(cat["corredor_id"]).all()
    assert not gt.duplicated(["corredor_id", "fecha", "hora"]).any()
    assert gt["hora"].between(0, 23).all()
    assert gt["velocidad_gt_kmh"].dropna().between(1, 120).all()
    print(f"\ntiempo_viaje_gt: {len(gt):,} filas · {gt['fecha'].min()} a {gt['fecha'].max()} · "
          f"horas {gt['hora'].min()} a {gt['hora'].max()} · {gt['corredor_id'].nunique()} corredores")
    print(gt.groupby("corredor_id")[["velocidad_gt_kmh", "tiempo_viaje_min"]].mean().round(1).to_string())
    print("\ntiempo_viaje_gt: pruebas OK ✔")

    vel = velocidad_corredor_hora()
    assert vel["corredor_id"].isin(cat["corredor_id"]).all()
    assert not vel.duplicated(["corredor_id", "fecha", "hora"]).any()
    assert vel["hora"].between(0, 23).all()
    assert vel["velocidad_media_kmh"].dropna().between(1, 120).all()
    assert vel["pct_valido"].between(0, 100).all()
    print(f"\nvelocidad_corredor_hora: {len(vel):,} filas · {vel['fecha'].min()} a {vel['fecha'].max()} · "
          f"{vel['corredor_id'].nunique()} corredores · horas {vel['hora'].min()} a {vel['hora'].max()}")
    print(vel.groupby("corredor_id")[["velocidad_media_kmh", "intensidad_veh_h", "pct_valido"]].mean().round(1).to_string())
    print("\nContrato cumplido ✔")

    try:
        _pruebas_nocturna()
    except ModuleNotFoundError as e:
        if "src.corredores" not in str(e):
            raise
        print("\nVelocidad nocturna: falta src/corredores.py. Haz git pull (o trae la rama que lo tiene) y vuelve a correr.")


if __name__ == "__main__":
    _pruebas_costo()
