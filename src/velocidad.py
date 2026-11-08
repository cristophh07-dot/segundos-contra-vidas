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