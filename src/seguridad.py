"""src/seguridad.py — limpieza de datos de seguridad vial (Josué)."""
from __future__ import annotations

import pathlib
import re
import unicodedata

import numpy as np
import pandas as pd

from src.descarga import leer

PROCESSED = pathlib.Path("data/processed")
PROCESSED.mkdir(parents=True, exist_ok=True)

LAT_MIN, LAT_MAX = 6.1, 6.4
LON_MIN, LON_MAX = -75.75, -75.45

# Valores de relleno que cuentan como faltante (D10)
FALTANTES = {"", "N/D", "SIN INF", "SIN INFORMACION", "SIN DATO", "NAN", "NONE", "0"}

COLS_INC = ["incidente_id", "fuente", "fecha", "hora", "anio", "mes", "dia_semana", "gravedad",
            "clase", "hay_moto", "hay_peaton", "lat", "lon", "direccion_normalizada", "comuna",
            "barrio", "corredor_id", "metodo_asignacion"]
COLS_VIC = ["incidente_id", "fecha", "hora", "gravedad_victima", "condicion", "edad", "sexo",
            "comuna", "lat", "lon", "corredor_id"]
COLS_MOR = ["id", "fecha", "hora", "clase", "edad", "sexo", "comuna", "lat", "lon", "corredor_id"]

_ABREV = [
    (r"\b(CARRERA|KRA|CRA|CARR)\b", "CR"),
    (r"\b(CALLE|CLL)\b", "CL"),
    (r"\b(AVENIDA|AVE)\b", "AV"),
    (r"\b(TRANSVERSAL|TRANSV|TRV)\b", "TV"),
    (r"\b(DIAGONAL|DIAG)\b", "DG"),
]


# ---------------------------------------------------------------- utilidades
def sin_tildes(s: pd.Series) -> pd.Series:
    return s.astype("string").str.normalize("NFKD").str.encode("ascii", "ignore").str.decode("ascii")


def _col(df: pd.DataFrame, nombre: str) -> pd.Series:
    """Busca una columna ignorando tildes, mayúsculas y espacios (p. ej. 'Año' -> 'ANO')."""
    for c in df.columns:
        k = unicodedata.normalize("NFKD", str(c)).encode("ascii", "ignore").decode().upper()
        if re.sub(r"[^A-Z0-9_]", "", k) == nombre:
            return df[c]
    raise KeyError(nombre)


def texto_limpio(s: pd.Series) -> pd.Series:
    """Texto sin espacios sobrantes; N/D, Sin inf, 0, etc. pasan a vacío."""
    t = s.astype("string").str.strip()
    clave = sin_tildes(t).str.upper()
    return t.where(~clave.isin(FALTANTES))


def a_fecha(s: pd.Series) -> pd.Series:
    """Texto d/mm/aaaa -> datetime (NaT si no se puede)."""
    return pd.to_datetime(s, format="%d/%m/%Y", errors="coerce")


def a_hora(s: pd.Series) -> pd.Series:
    """'13:58:00' -> 13 (entero 0-23, vacío si no se puede)."""
    h = pd.to_numeric(s.astype(str).str.extract(r"^\s*(\d{1,2})\s*:")[0], errors="coerce")
    return h.where(h.between(0, 23)).astype("Int64")


def a_numero(s: pd.Series) -> pd.Series:
    """Número con coma o punto decimal -> float."""
    return pd.to_numeric(s.astype("string").str.replace(",", ".", regex=False), errors="coerce")


def limpiar_coords(lat: pd.Series, lon: pd.Series):
    """Fuera de Medellín o vacías -> vacías (la fila NO se borra)."""
    ok = lat.between(LAT_MIN, LAT_MAX) & lon.between(LON_MIN, LON_MAX)
    return lat.where(ok), lon.where(ok)


def normalizar_direccion(s: pd.Series) -> pd.Series:
    t = sin_tildes(s).str.upper().str.strip()
    t = t.where(~t.str.contains("999", na=False))          # 'CALLE 999 CON CARRERA 999'
    t = t.where(~t.isin(list(FALTANTES)))
    for patron, abrev in _ABREV:
        t = t.str.replace(patron, abrev, regex=True)
    t = t.str.replace(r"\s+", " ", regex=True).str.strip()
    return t.where(t.notna() & (t != ""))


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


def mapear_gravedad(s: pd.Series) -> pd.Series:
    t = sin_tildes(s).str.upper().str.strip()
    out = pd.Series(np.nan, index=s.index, dtype="object")
    out[t.str.contains("SOLO", na=False)] = "solo_danos"
    out[t.str.contains("HERID", na=False)] = "herido"
    out[t.str.contains("MUERT", na=False)] = "muerto"
    return out


def mapear_condicion(s: pd.Series) -> pd.Series:
    t = sin_tildes(s).str.upper().str.strip()
    out = pd.Series("otro", index=s.index, dtype="object")
    # El orden importa: 'MOTOCICLISTA' contiene 'CICLISTA'
    out[t.str.contains("CICLISTA", na=False)] = "ciclista"
    out[t.str.contains("MOTOCICLISTA", na=False)] = "conductor_moto"
    out[t.str.contains("ACOMPA", na=False)] = "parrillero"
    out[t.str.contains("PEATON", na=False)] = "peaton"
    out[t.str.contains("PASAJERO", na=False)] = "pasajero"
    out[t.str.startswith("CONDUCTOR", na=False)] = "conductor_carro"
    out[t.isna()] = np.nan
    return out


def limpiar_sexo(s: pd.Series) -> pd.Series:
    t = sin_tildes(s).str.upper().str.strip().str[:1]
    return t.where(t.isin(["F", "M"]))


def limpiar_edad(s: pd.Series) -> pd.Series:
    e = pd.to_numeric(s, errors="coerce")
    return e.where(e.between(0, 110)).astype("Int64")


# ---------------------------------------------------------------- incidentes
def incidentes_limpios() -> pd.DataFrame:
    raw = leer("incidentes_itm", sheet_name="BD")
    n0 = len(raw)

    fecha = pd.to_datetime(raw["FECHA_INCIDENTE"], errors="coerce")
    lat, lon = limpiar_coords(pd.to_numeric(raw["Latitud"], errors="coerce"),
                              pd.to_numeric(raw["Longitud"], errors="coerce"))
    clase = mapear_clase(raw["CLASE_INCIDENTE"])
    hay_moto = pd.Series(pd.NA, index=raw.index, dtype="Int64")
    hay_peaton = pd.Series(pd.NA, index=raw.index, dtype="Int64").mask(clase == "atropello", 1)

    df = pd.DataFrame({
        "incidente_id": raw["LLAVE"].astype("string"),
        "fuente": "itm",
        "fecha": fecha,
        "hora": a_hora(raw["HORA_INCIDENTE"]),
        "anio": fecha.dt.year.astype("Int64"),
        "mes": fecha.dt.month.astype("Int64"),
        "dia_semana": fecha.dt.dayofweek.astype("Int64"),
        "gravedad": mapear_gravedad(raw["GRAVEDAD_INCIDENTE"]),
        "clase": clase,
        "hay_moto": hay_moto,
        "hay_peaton": hay_peaton,
        "lat": lat,
        "lon": lon,
        "direccion_normalizada": normalizar_direccion(raw["DIRECCION_INTERPOLADA"]),
        "comuna": texto_limpio(raw["Comuna Planeacion"]),
        "barrio": texto_limpio(raw["Barrio Planeacion"]),
        "corredor_id": pd.Series(np.nan, index=raw.index, dtype="object"),
        "metodo_asignacion": "sin_asignar",
    })

    df = df[df["fecha"].notna() & df["gravedad"].notna()].copy()
    print(f"incidentes_limpios: {n0} leídas | eliminadas (sin fecha o sin gravedad): {n0 - len(df)} | "
          f"final: {len(df)} | sin coordenadas: {int(df['lat'].isna().sum())} | "
          f"sin dirección: {int(df['direccion_normalizada'].isna().sum())}")

    df["fecha"] = df["fecha"].dt.strftime("%Y-%m-%d")
    df = df[COLS_INC]
    df.to_csv(PROCESSED / "incidentes_limpios.csv", index=False, encoding="utf-8")
    return df


# ---------------------------------------------------------------- víctimas
def victimas_limpias() -> pd.DataFrame:
    raw = leer("victimas_medata")
    n0 = len(raw)

    # D12: solo 235.843 filas son reales; el resto está vacío
    raw = raw[pd.to_numeric(_col(raw, "ANO"), errors="coerce").notna()].copy()
    n_vacias = n0 - len(raw)

    fecha = a_fecha(raw["Fecha_incidente"])
    lat, lon = limpiar_coords(a_numero(raw["Latitud"]), a_numero(raw["Longitud"]))
    g = sin_tildes(raw["Gravedad_victima"]).str.upper()
    gravedad = pd.Series(np.nan, index=raw.index, dtype="object")
    gravedad[g.str.contains("HERID", na=False)] = "herido"
    gravedad[g.str.contains("MUERT", na=False)] = "muerto"
    comuna = texto_limpio(raw["Comuna"]).str.replace(r"^\d+\s*-\s*", "", regex=True)

    df = pd.DataFrame({
        "incidente_id": pd.Series(pd.NA, index=raw.index, dtype="string"),  # no se une con el ITM (D12)
        "fecha": fecha,
        "hora": a_hora(raw["Hora_incidente"]),
        "gravedad_victima": gravedad,
        "condicion": mapear_condicion(raw["Condicion"]),
        "edad": limpiar_edad(raw["Edad"]),
        "sexo": limpiar_sexo(raw["Sexo"]),
        "comuna": comuna,
        "lat": lat,
        "lon": lon,
        "corredor_id": pd.Series(np.nan, index=raw.index, dtype="object"),
    })

    n1 = len(df)
    df = df[df["fecha"].notna() & df["gravedad_victima"].notna()].copy()
    print(f"victimas_limpias: {n0} leídas | filas vacías eliminadas: {n_vacias} | "
          f"sin fecha o gravedad eliminadas: {n1 - len(df)} | final: {len(df)} | "
          f"sin coordenadas: {int(df['lat'].isna().sum())}")

    df["fecha"] = df["fecha"].dt.strftime("%Y-%m-%d")
    df = df[COLS_VIC]
    df.to_csv(PROCESSED / "victimas_limpias.csv", index=False, encoding="utf-8")
    return df


# ---------------------------------------------------------------- mortalidad
def mortalidad_distrito() -> pd.DataFrame:
    raw = leer("mortalidad_distrito")
    lat, lon = limpiar_coords(pd.to_numeric(raw["lat_wgs84"], errors="coerce"),
                              pd.to_numeric(raw["lon_wgs84"], errors="coerce"))
    comuna = texto_limpio(raw["nom_comuna"]).replace({"La Calendaria": "La Candelaria"})

    df = pd.DataFrame({
        "id": raw["id"].astype("string").str.strip(),
        "fecha": a_fecha(raw["fecha_ocurrencia"]),
        "hora": a_hora(raw["hora_ocurrencia"]),
        "clase": mapear_clase(raw["clase"]),
        "edad": limpiar_edad(raw["edad_fallecido"]),
        "sexo": limpiar_sexo(raw["sexo_fallecido"]),
        "comuna": comuna,
        "lat": lat,
        "lon": lon,
        "corredor_id": pd.Series(np.nan, index=raw.index, dtype="object"),
    })

    n0 = len(df)
    df = df.drop_duplicates()   # un mismo id puede tener varios fallecidos distintos
    n_dup = n0 - len(df)
    n1 = len(df)
    df = df[df["fecha"].notna()].copy()
    print(f"mortalidad_distrito: {n0} filas leídas | duplicados exactos eliminados: {n_dup} | "
          f"sin fecha válida eliminados: {n1 - len(df)} | final: {len(df)}")

    df["fecha"] = df["fecha"].dt.strftime("%Y-%m-%d")
    df = df[COLS_MOR]
    df.to_csv(PROCESSED / "mortalidad_distrito.csv", index=False, encoding="utf-8")
    return df
def limpiar_itm(umbral_relleno: int = 100) -> pd.DataFrame:
    """Incidentes graves del ITM (solo herido y muerto, D8), mismo formato que incidentes_limpios().
    Direcciones de relleno y coordenadas fuera de Medellín quedan vacías (D10).
    Reporta las coordenadas que se repiten más de `umbral_relleno` veces (posible relleno)."""
    raw = leer("incidentes_itm", sheet_name="BD")
    lat0 = pd.to_numeric(raw["Latitud"], errors="coerce")
    lon0 = pd.to_numeric(raw["Longitud"], errors="coerce")
    fuera = (lat0.notna() & lon0.notna()) & ~(lat0.between(LAT_MIN, LAT_MAX) & lon0.between(LON_MIN, LON_MAX))
    print(f"limpiar_itm: coordenadas fuera de Medellín (pasan a vacío): {int(fuera.sum())}")

    df = incidentes_limpios()
    n0 = len(df)
    df = df[df["gravedad"].isin(["herido", "muerto"])].copy()
    print(f"limpiar_itm: {n0} incidentes -> {len(df)} graves (se quitan {n0 - len(df)} de solo daños)")

    rep = (df.dropna(subset=["lat", "lon"]).groupby(["lat", "lon"]).size()
             .sort_values(ascending=False))
    sospechosas = rep[rep > umbral_relleno]
    print(f"limpiar_itm: coordenadas repetidas más de {umbral_relleno} veces: {len(sospechosas)} "
          f"({int(sospechosas.sum())} incidentes)")
    if len(sospechosas):
        print(sospechosas.head(15).to_string())
    sospechosas.rename("repeticiones").reset_index().to_csv(
        PROCESSED / "coordenadas_repetidas_itm.csv", index=False, encoding="utf-8")

    df.to_csv(PROCESSED / "incidentes_graves_itm.csv", index=False, encoding="utf-8")
    return df


# ---------------------------------------------------------------- corredores
CRS_METROS = 3116          # MAGNA-SIRGAS / Colombia Bogotá, en metros
RADIOS = (30, 50, 100)     # metros; el oficial es 50
CORREDORES_COORD = ["regional", "autopista_norte", "las_palmas", "autopista_sur",
                    "calle_30", "ferrocarril", "oriental"]   # AJUSTAR a los corredor_id reales


def _lineas_corredor(geometria: pd.DataFrame) -> dict:
    """geometria: columnas corredor_id y geometria_wkt (MULTIPOINT ordenado) -> LineString en metros."""
    import geopandas as gpd
    from shapely import wkt
    from shapely.geometry import LineString

    lineas = {}
    for cid, w in zip(geometria["corredor_id"], geometria["geometria_wkt"]):
        g = wkt.loads(w)
        pts = [(p.x, p.y) for p in g.geoms] if g.geom_type == "MultiPoint" else list(g.coords)
        lineas[cid] = LineString(pts) if len(pts) > 1 else g
    serie = gpd.GeoSeries(lineas, crs=4326).to_crs(CRS_METROS)
    return dict(serie.items())


def _asignar_por_coordenadas(df, geometria, lat="lat", lon="lon"):
    import geopandas as gpd
    import shapely

    lineas = _lineas_corredor(geometria)
    ok = df[lat].notna() & df[lon].notna()
    pts = gpd.GeoSeries(gpd.points_from_xy(df.loc[ok, lon], df.loc[ok, lat]),
                        crs=4326).to_crs(CRS_METROS).values
    D = pd.DataFrame({cid: shapely.distance(pts, ln) for cid, ln in lineas.items()},
                     index=df.index[ok])
    mas_cercano, dmin = D.idxmin(axis=1), D.min(axis=1)

    print("Asignación por coordenadas (distancia al corredor más cercano):")
    for r in RADIOS:
        print(f"  a {r:>3} m o menos: {int((dmin <= r).sum())} de {int(ok.sum())}")
    ambiguos = int(((D <= 50).sum(axis=1) >= 2).sum())
    print(f"  cerca (≤ 50 m) de dos o más corredores: {ambiguos} (van al más cercano)")

    corredor = pd.Series(np.nan, index=df.index, dtype="object")
    corredor[ok] = mas_cercano.where(dmin <= 50)
    return corredor


def asignar_corredor_propio(df: pd.DataFrame, geometria: pd.DataFrame | None = None,
                     direccion: pd.Series | None = None,
                     lat: str = "lat", lon: str = "lon") -> pd.DataFrame:
    """Devuelve df con corredor_id y metodo_asignacion ('coordenadas', 'direccion' o 'sin_asignar').
    - geometria: tabla con corredor_id y geometria_wkt (MULTIPOINT). Si es None, solo asigna por dirección.
    - direccion: serie normalizada; por defecto df['direccion_normalizada'].
    Sirve igual para limpiar_itm(), victimas_limpias() y mortalidad_distrito()."""
    out = df.copy()
    out["corredor_id"] = pd.Series(np.nan, index=out.index, dtype="object")
    out["metodo_asignacion"] = "sin_asignar"

    if geometria is not None:
        c = _asignar_por_coordenadas(out, geometria, lat, lon)
        hay = c.notna()
        out.loc[hay, "corredor_id"] = c[hay]
        out.loc[hay, "metodo_asignacion"] = "coordenadas"

    if direccion is None and "direccion_normalizada" in out.columns:
        direccion = out["direccion_normalizada"]
    if direccion is not None:
        d = _asignar_por_direccion(direccion)          # se escribe cuando vea los límites
        libre = out["corredor_id"].isna() & d.notna()
        out.loc[libre, "corredor_id"] = d[libre]
        out.loc[libre, "metodo_asignacion"] = "direccion"

    print("\nIncidentes por corredor y método:")
    print(pd.crosstab(out["corredor_id"].fillna("(sin asignar)"), out["metodo_asignacion"]).to_string())
    return out

# ---------------------------------------------------------------- asignación por dirección
# (tipo de calle que cruza, mínimo, máximo). Calles "Sur" cuentan como negativas.
LIMITES_DIRECCION = {
    "AV_80":       ("CL", 30, 65),
    "AV_POBLADO":  ("CL", -12, 30),
    "AV_GUAYABAL": ("CL", -12, 30),
    "AV_33":       ("CR", 50, 80),   # CONFIRMAR con Johan
    "AV_SAN_JUAN": ("CR", 62, 80),   # CONFIRMAR con Johan
}
_VIA = re.compile(r"\b(CR|CL|AV|TV|DG)\s+(\d+)(?:\s+([A-Z])\b)?(\s+SUR\b)?")


def _vias(texto):
    """'CR 80 CON CL 44 B' -> [('CR', 80, '', False), ('CL', 44, 'B', False)]"""
    return [(t, int(n), l or "", bool(s)) for t, n, l, s in _VIA.findall(texto or "")]


def _asignar_por_direccion(direccion: pd.Series) -> pd.Series:
    from src.velocidad import CORREDORES

    reglas = {}
    for cid, (_, alias, _) in CORREDORES.items():
        if cid in LIMITES_DIRECCION:
            reglas[cid] = ([v[:3] for v in _vias(alias.replace("CARRERA", "CR").replace("AVENIDA", "AV")
                                                   .replace("CALLE", "CL"))], *LIMITES_DIRECCION[cid])
    out, ambiguos = [], 0
    for d in direccion.fillna("").astype(str):
        vias = _vias(d)
        hallados = []
        for cid, (alias_vias, tipo, lo, hi) in reglas.items():
            for i, (t, n, l, sur) in enumerate(vias):
                if (t, n, l) not in alias_vias and (("CR" if t == "AV" else t), n, l) not in alias_vias:
                    continue
                otras = [v for j, v in enumerate(vias) if j != i and v[0] == tipo]
                if any(lo <= (-v[1] if v[3] else v[1]) <= hi for v in otras):
                    hallados.append(cid)
                    break
        if len(hallados) > 1:
            ambiguos += 1
        out.append(hallados[0] if hallados else np.nan)
    print(f"Asignación por dirección: {sum(isinstance(x, str) for x in out)} asignadas | "
          f"{ambiguos} en cruces de dos corredores (se toma el primero)")
    return pd.Series(out, index=direccion.index, dtype="object")

def victimas_con_corredor(geometria=None) -> pd.DataFrame:
    """victimas_limpias() + direccion_normalizada + corredor_id, alineadas fila a fila."""
    raw = leer("victimas_medata")
    raw = raw[pd.to_numeric(_col(raw, "ANO"), errors="coerce").notna()]
    df = victimas_limpias()
    # mismas filas y mismo orden que dentro de victimas_limpias(): se filtra igual
    fecha = a_fecha(raw["Fecha_incidente"])
    g = sin_tildes(raw["Gravedad_victima"]).str.upper()
    ok = fecha.notna() & (g.str.contains("HERID", na=False) | g.str.contains("MUERT", na=False))
    direccion = normalizar_direccion(raw.loc[ok, "Direccion_incidente"])
    assert len(direccion) == len(df), "las filas no coinciden"
    df = df.reset_index(drop=True)
    df["direccion_normalizada"] = direccion.reset_index(drop=True)
    out = asignar_corredor(df, geometria=geometria)
    out.to_csv(PROCESSED / "victimas_con_corredor.csv", index=False, encoding="utf-8")
    return out


def mortalidad_con_corredor(geometria=None) -> pd.DataFrame:
    """mortalidad_distrito() + direccion_normalizada + corredor_id."""
    raw = leer("mortalidad_distrito")
    df = mortalidad_distrito().reset_index(drop=True)
    assert len(raw) == len(df), "las filas no coinciden"
    df["direccion_normalizada"] = normalizar_direccion(raw["direccion_ocurrencia"]).reset_index(drop=True)
    out = asignar_corredor(df, geometria=geometria)
    out.to_csv(PROCESSED / "mortalidad_con_corredor.csv", index=False, encoding="utf-8")
    return out

def asignar_corredor(df, geometria=None, **kw):
    """Delega en src.corredores para que ITM, víctimas y mortalidad usen el mismo método (P3)."""
    from src.corredores import asignar_corredor as asignar
    return asignar(df, catalogo=geometria)