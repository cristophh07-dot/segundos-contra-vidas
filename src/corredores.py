"""
src/corredores.py — geometría de los 12 corredores y asignación de incidentes a corredores.

Usa lo que ya está en el repositorio:
- los sensores del SIMM (velocidad_simm), que marcan por dónde va cada corredor;
- los límites de cada tramo de Google Traffic (docs/limites_tramos.txt, Johan);
- el catálogo y los alias de src/velocidad.py (Johan);
- los incidentes graves limpios de src/seguridad.limpiar_itm() (Josué).

Funciones:
- geometria_corredores(): llena geometria_wkt del catálogo con un MULTIPOINT por corredor, cortado al
  tramo de Google Traffic, con los dos extremos incluidos y los puntos ordenados de INICIO a FIN.
- asignar_corredor(df): agrega corredor_id y metodo_asignacion a cualquier tabla con lat, lon y dirección
  (sirve para limpiar_itm(), victimas_limpias() y mortalidad_distrito()).

Uso (desde la carpeta principal del repo):  python -m src.corredores
Escribe docs/geometria_corredores.txt: pega ese archivo en el chat.
"""
from __future__ import annotations

import pathlib
import re

import numpy as np
import pandas as pd
import shapely
from pyproj import Transformer
from scipy.sparse.csgraph import minimum_spanning_tree, shortest_path
from scipy.spatial.distance import cdist
from shapely.geometry import LineString, MultiPoint, Point
from shapely.ops import nearest_points

from src.descarga import leer
from src.velocidad import CORREDORES, catalogo_corredores

PROCESSED = pathlib.Path("data/processed")
REPORTE = pathlib.Path("docs/geometria_corredores.txt")

CRS_M = 3116                                     # coordenadas del SIMM, en metros (validado por Johan)
A_METROS = Transformer.from_crs(4326, CRS_M, always_xy=True)
A_GRADOS = Transformer.from_crs(CRS_M, 4326, always_xy=True)

MAX_AJUSTE_M = 250       # un extremo se acepta si queda a esta distancia o menos del eje del corredor
MAX_EXTENSION_M = 2500   # un extremo ubicado más allá de la última estación se acepta hasta esta distancia,
MAX_ANGULO = 30          # si queda en la prolongación del eje (desvío de máximo 30 grados)
TOL_CORTE_M = 100        # margen al cortar la cadena de sensores en los extremos
RADIO_M = 50             # radio de asignación por defecto (se reporta también 30 y 100 m)

# Extremos de cada tramo, en el orden INICIO -> FIN de docs/limites_tramos.txt (primer tramo del corredor).
#   ("cruce", "CL 65"):     cruce de la vía del corredor con esa calle, ubicado con las direcciones del ITM.
#   ("corredor", "AV_80"):  punto donde se cruzan los ejes de los dos corredores (se usa cuando el otro corredor
#                           no tiene número propio, o cuando su número no es único en la ciudad).
#   ("sitio", "Tugo"):      lugar sin coordenadas en los datos: se ubica con la longitud del tramo de Google Traffic.
EXTREMOS = {
    "AV_REGIONAL":    (("sitio", "Tugo"),               ("corredor", "AV_SAN_JUAN")),
    "AUT_SUR":        (("sitio", "CTI"),                ("cruce", "CL 10")),
    "AUT_NORTE":      (("sitio", "Solla"),              ("cruce", "CL 67")),        # Punto Cero = CR 64 C con CL 67
    "AV_80":          (("cruce", "CL 65"),              ("cruce", "CL 30")),
    "AV_PALMAS":      (("sitio", "Sandiego"),           ("sitio", "Chuscalito")),
    "AV_POBLADO":     (("cruce", "CL 30"),              ("cruce", "CL 12 SUR")),
    "AV_GUAYABAL":    (("cruce", "CL 30"),              ("cruce", "CL 12 SUR")),
    "AV_33":          (("corredor", "AUT_SUR"),         ("corredor", "AV_80")),
    "CL_30":          (("cruce", "CR 80"),              ("sitio", "Industriales")),
    "AV_SAN_JUAN":    (("cruce", "CR 80"),              ("corredor", "AV_REGIONAL")),
    "AV_FERROCARRIL": (("cruce", "CL 67"),              ("cruce", "CL 44")),        # Barranquilla = CL 67
    "AV_ORIENTAL":    (("cruce", "CL 44"),              ("sitio", "Villanueva")),
}
# Si los dos extremos son sitios, el tramo arranca en la punta de la cadena de sensores más cercana al centro
# de la ciudad (centroide de todos los sensores del SIMM) y sigue la longitud del tramo. Aquí se dice cuál
# de los dos extremos es el urbano: Sandiego (INICIO) en Las Palmas.
# Punto Cero y Barranquilla no son sitios: el puente Punto Cero está en la Carrera 64C (Autopista Norte) con la
# Calle 67, que es la calle Barranquilla (El Colombiano, "Plomada de Punto Cero no volverá al puente").
PUNTA_URBANA = {"AV_PALMAS": "inicio"}

# Incidentes sin coordenadas: solo los corredores cuyo tramo va entre dos calles numeradas se asignan por
# dirección. La dirección debe nombrar la vía del corredor y una calle dentro del tramo.
RANGO_CALLES = {
    "AV_80":       {"CL": (30, 65)},                    # Calle 30 a Calle 65
    "AV_POBLADO":  {"CL": (1, 30), "CL SUR": (1, 12)},  # Calle 12 Sur a Calle 30
    "AV_GUAYABAL": {"CL": (1, 30), "CL SUR": (1, 12)},  # Calle 12 Sur a Calle 30
}
CALLE = re.compile(r"^(CL) (\d+)(?: [A-Z]{1,2})?( SUR)?$")


# ---------------------------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------------------------
def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype(str).str.replace(",", ".", regex=False), errors="coerce")


def _parte(p: str) -> str:
    """'CR 43A' -> 'CR 43 A'; espacios simples y mayúsculas."""
    p = re.sub(r"(\d)([A-Z])", r"\1 \2", str(p).strip().upper())
    return re.sub(r"\s+", " ", p)


def _partes(direccion: pd.Series) -> pd.Series:
    """'CR 80 CON CL 65' -> ['CR 80', 'CL 65'] (formato de seguridad.limpiar_itm)."""
    return direccion.fillna("").astype(str).str.split(" CON ").map(lambda ps: [_parte(p) for p in ps if p.strip()])


def _tokens_alias(cid: str) -> set[str]:
    """Formas abreviadas del alias de un corredor ('CR 80', 'CL 33', 'CL 37')."""
    return {_parte(a) for a in CORREDORES[cid][1].split("|") if re.match(r"^(CR|CL) \d", a)}


def _a_metros(lat: pd.Series, lon: pd.Series) -> np.ndarray:
    x, y = A_METROS.transform(lon.values, lat.values)
    return np.column_stack([x, y])


# ---------------------------------------------------------------------------------------------
# Geometría
# ---------------------------------------------------------------------------------------------
def sensores_simm() -> pd.DataFrame:
    """Sensores únicos del SIMM con su corredor_id (vacío si el corredor no es uno de los 12), en metros."""
    df = leer("velocidad_simm", usecols=["corredor", "carril", "longitud", "latitud"])
    df["corredor"] = df["corredor"].astype(str).str.strip()
    df["x"], df["y"] = _num(df["longitud"]), _num(df["latitud"])
    df = df.dropna(subset=["x", "y"]).drop_duplicates(["corredor", "carril"]).reset_index(drop=True)
    df["corredor_id"] = df["corredor"].map({v[2]: k for k, v in CORREDORES.items()})
    return df


def _vertebra(xy: np.ndarray):
    """Eje del corredor: el camino más largo del árbol de mínima expansión de sus sensores.
    Funciona con vías curvas y con sensores en las dos calzadas. Devuelve el eje y la posición de cada
    sensor a lo largo de él (metros desde el primer extremo)."""
    if len(xy) == 1:
        return LineString([xy[0], xy[0] + 1]), np.zeros(1)
    arbol = minimum_spanning_tree(cdist(xy, xy))
    grafo = arbol + arbol.T
    a = int(np.argmax(shortest_path(grafo, indices=0, directed=False)))
    dist, pred = shortest_path(grafo, indices=a, directed=False, return_predecessors=True)
    b = int(np.argmax(dist))
    camino = [b]
    while camino[-1] != a:
        camino.append(int(pred[camino[-1]]))
    eje = LineString(xy[camino[::-1]])
    pos = shapely.line_locate_point(eje, shapely.points(xy))
    return eje, pos


def _cruce_por_direccion(inc: pd.DataFrame, cid: str, calle: str):
    """Mediana de las coordenadas de los incidentes cuya dirección es la vía del corredor con esa calle."""
    alias, calle = _tokens_alias(cid), _parte(calle)
    if not alias:
        return None
    m = inc["partes"].map(lambda ps: calle in ps and bool(alias.intersection(ps)))
    if m.sum() < 3:
        return None
    return inc.loc[m, ["x", "y"]].median().values, int(m.sum())


def _ubicar(eje, punto, largo):
    """Posición de un punto a lo largo del eje. Devuelve (posición, punto_extra, nota).

    Si el punto queda más allá de la última estación pero en la prolongación del eje, la geometría se extiende
    hasta él (punto_extra). Las estaciones del SIMM están separadas 1 o 2 km y a veces no llegan al extremo.
    """
    p = Point(punto)
    s, d = eje.project(p), eje.distance(p)
    if d <= MAX_AJUSTE_M:
        return s, None, f"a {d:.0f} m del eje"
    if s < 1 or s > largo - 1:
        c = np.array(eje.coords)
        punta, previo = (c[0], c[1]) if s < 1 else (c[-1], c[-2])
        u, v = punta - previo, np.asarray(punto) - punta
        ang = np.degrees(np.arccos(np.clip(u @ v / (np.linalg.norm(u) * np.linalg.norm(v) + 1e-9), -1, 1)))
        if d <= MAX_EXTENSION_M and ang <= MAX_ANGULO:
            return s, np.asarray(punto), f"a {d:.0f} m más allá de la última estación, en la prolongación del eje: se extiende"
        return s, None, f"a {d:.0f} m más allá de la última estación (desvío {ang:.0f}°): se corta en la última estación"
    return None, None, f"a {d:.0f} m del eje: no se usa"


def geometria_corredores(inc: pd.DataFrame | None = None, guardar: bool = True):
    """Llena geometria_wkt del catálogo de Johan. Devuelve (catálogo, reporte por corredor).

    inc: incidentes con lat, lon y direccion_normalizada (por defecto, seguridad.limpiar_itm()).
    """
    if inc is None:
        from src.seguridad import limpiar_itm
        inc = limpiar_itm()
    cat = catalogo_corredores()
    sens = sensores_simm()
    centro = sens[["x", "y"]].mean().values

    con = inc.dropna(subset=["lat", "lon"]).copy()
    con[["x", "y"]] = _a_metros(_num(con["lat"]), _num(con["lon"]))
    con["partes"] = _partes(con["direccion_normalizada"])

    ejes = {}
    for cid in CORREDORES:
        xy = sens.loc[sens["corredor_id"] == cid, ["x", "y"]].round(1).drop_duplicates().values
        if len(xy) == 0:
            raise ValueError(f"{cid}: no hay sensores del SIMM con el nombre '{CORREDORES[cid][2]}'")
        eje, pos = _vertebra(xy)
        ejes[cid] = (eje, xy, pos)

    filas, wkt = [], {}
    for cid, (eje, xy, pos) in ejes.items():
        largo = eje.length
        L = float(cat.loc[cat["corredor_id"] == cid, "longitud_km"].iloc[0]) * 1000
        posiciones, notas, extras = [], [], []
        for tipo, ref in EXTREMOS[cid]:
            if tipo == "cruce":
                r = _cruce_por_direccion(con, cid, ref)
                if r is None:
                    posiciones.append(None)
                    extras.append(None)
                    notas.append(f"{ref}: cruce no encontrado en las direcciones")
                    continue
                s, ex, nota = _ubicar(eje, r[0], largo)
                extras.append(ex)
                notas.append(f"{ref}: cruce en las direcciones ({r[1]} incidentes), {nota}")
            elif tipo == "corredor":
                p_eje, p_otro = nearest_points(eje, ejes[ref][0])
                sep = p_eje.distance(p_otro)
                s, ex, nota = _ubicar(eje, np.array(p_otro.coords[0]) if sep > MAX_AJUSTE_M else np.array(p_eje.coords[0]), largo)
                extras.append(ex)
                notas.append(f"{ref}: cruce de los ejes (separación {sep:.0f} m), {nota}")
            else:
                s = None
                extras.append(None)
                notas.append(f"{ref}: sitio sin coordenadas")
            posiciones.append(s)

        ini, fin = posiciones
        if ini is not None and fin is not None:
            regla = "los dos extremos ubicados con datos"
        elif ini is None and fin is None:
            d0 = Point(eje.coords[0]).distance(Point(centro))
            d1 = Point(eje.coords[-1]).distance(Point(centro))
            urbano = 0.0 if d0 <= d1 else largo
            lejano = urbano + L if urbano == 0.0 else urbano - L
            ini, fin = (lejano, urbano) if PUNTA_URBANA.get(cid, "fin") == "fin" else (urbano, lejano)
            regla = "ningún extremo ubicado: desde la punta más cercana al centro, con la longitud de Google Traffic"
            if cid not in PUNTA_URBANA:
                regla += " ⚠ REVISAR: se esperaba ubicar al menos un extremo con datos"
        else:
            k = ini if ini is not None else fin
            otro = k + L if (largo - k) >= k else k - L
            ini, fin = (k, otro) if ini is not None else (otro, k)
            regla = "un extremo ubicado; el otro, con la longitud de Google Traffic"
        ini, fin = float(np.clip(ini, 0, largo)), float(np.clip(fin, 0, largo))
        lo, hi = min(ini, fin), max(ini, fin)

        dentro = (pos >= lo - TOL_CORTE_M) & (pos <= hi + TOL_CORTE_M)
        orden = np.argsort(pos[dentro]) if ini <= fin else np.argsort(-pos[dentro])
        p_ini = extras[0] if extras[0] is not None else np.array(eje.interpolate(ini).coords[0])
        p_fin = extras[1] if extras[1] is not None else np.array(eje.interpolate(fin).coords[0])
        puntos = np.vstack([p_ini, xy[dentro][orden], p_fin])
        lon, lat = A_GRADOS.transform(puntos[:, 0], puntos[:, 1])
        wkt[cid] = shapely.to_wkt(MultiPoint(np.column_stack([lon, lat])), rounding_precision=6)
        hueco = np.linalg.norm(np.diff(puntos, axis=0), axis=1).max()
        extension = sum(float(np.linalg.norm(e - np.array(eje.interpolate(t).coords[0])))
                        for e, t in ((extras[0], ini), (extras[1], fin)) if e is not None)
        largo_final = (hi - lo) + extension            # a lo largo del eje, más lo extendido

        filas.append({
            "corredor_id": cid, "estaciones": len(xy), "dentro": int(dentro.sum()), "fuera": int((~dentro).sum()),
            "cadena_km": round(largo / 1000, 2), "tramo_gt_km": round(L / 1000, 2), "geometria_km": round(largo_final / 1000, 2),
            "hueco_max_m": round(float(hueco)), "inicio": notas[0], "fin": notas[1], "regla": regla,
        })

    cat["geometria_wkt"] = cat["corredor_id"].map(wkt)
    rep = pd.DataFrame(filas).set_index("corredor_id")
    if guardar:
        cat.to_csv(PROCESSED / "catalogo_corredores.csv", index=False, encoding="utf-8")
    return cat, rep


# ---------------------------------------------------------------------------------------------
# Asignación
# ---------------------------------------------------------------------------------------------
def coordenadas_relleno(df: pd.DataFrame, umbral: int = 100, min_direcciones: int = 10) -> pd.Series:
    """True en las filas cuya coordenada es probablemente de relleno.

    En la base del ITM las coordenadas se interpolan desde la dirección, así que una esquina con muchos
    incidentes repite su coordenada y eso es normal. Es relleno cuando una misma coordenada se repite más
    de `umbral` veces con al menos `min_direcciones` direcciones distintas.
    """
    con = df.dropna(subset=["lat", "lon"])
    g = con.groupby(["lat", "lon"])["direccion_normalizada"].agg(["size", "nunique"])
    malas = g[(g["size"] > umbral) & (g["nunique"] >= min_direcciones)].index
    return pd.Series(pd.MultiIndex.from_frame(df[["lat", "lon"]]).isin(malas), index=df.index)


def _por_direccion(partes: list[str]):
    for cid, rangos in RANGO_CALLES.items():
        if not _tokens_alias(cid).intersection(partes):
            continue
        for p in partes:
            m = CALLE.match(p)
            if m:
                clave = "CL SUR" if m.group(3) else "CL"
                if clave in rangos and rangos[clave][0] <= int(m.group(2)) <= rangos[clave][1]:
                    return cid
    return None


def asignar_corredor(df: pd.DataFrame, catalogo: pd.DataFrame | None = None, radio: float = RADIO_M,
                     excluir_relleno: bool = False) -> pd.DataFrame:
    """Agrega corredor_id, metodo_asignacion, corredor_cercano, dist_corredor_m y ambiguo.

    - Por coordenadas (los 12 corredores): el corredor cuya geometría queda más cerca, si está a `radio` m
      o menos. La geometría se recorre en orden, así que los puntos entre dos sensores también cuentan.
    - Por dirección (solo filas sin coordenadas útiles): Av. 80, El Poblado y Guayabal, cuando la dirección
      nombra la vía del corredor y una calle dentro del tramo.
    - ambiguo = True si otro corredor también queda dentro del radio (se queda con el más cercano).
    - excluir_relleno=False por defecto: en la base del ITM los puntos muy repetidos son intercambios viales
      donde se agrupan varias direcciones cercanas (Calle 67, Calle 78, Calle 10...), no valores de relleno.
    df necesita lat, lon y direccion_normalizada (formato de seguridad.py).
    """
    if catalogo is None:
        ruta = PROCESSED / "catalogo_corredores.csv"
        catalogo = pd.read_csv(ruta) if ruta.exists() else None
        # velocidad.catalogo_corredores() reescribe ese archivo con la geometría vacía: si pasa, se recalcula
        if catalogo is None or catalogo["geometria_wkt"].isna().any():
            catalogo = geometria_corredores()[0]
    lineas = {}
    for cid, w in zip(catalogo["corredor_id"], catalogo["geometria_wkt"]):
        p = np.array([(g.x, g.y) for g in shapely.from_wkt(w).geoms])
        x, y = A_METROS.transform(p[:, 0], p[:, 1])
        lineas[cid] = LineString(np.column_stack([x, y]))
    ids = np.array(list(lineas))

    out = df.copy()
    lat, lon = _num(out["lat"]), _num(out["lon"])
    ok = lat.notna() & lon.notna()
    if excluir_relleno:
        ok &= ~coordenadas_relleno(out.assign(lat=lat, lon=lon))
    for c, v in [("corredor_id", None), ("corredor_cercano", None), ("dist_corredor_m", np.nan),
                 ("ambiguo", False), ("metodo_asignacion", "sin_asignar")]:
        out[c] = v
    out["corredor_id"] = out["corredor_id"].astype(object)
    out["corredor_cercano"] = out["corredor_cercano"].astype(object)

    if ok.any():
        pts = shapely.points(_a_metros(lat[ok], lon[ok]))
        with np.errstate(invalid="ignore"):          # aviso espurio de GEOS; no produce valores vacíos
            D = np.column_stack([shapely.distance(pts, linea) for linea in lineas.values()])
        orden = np.argsort(D, axis=1)
        filas = np.arange(len(D))
        d1, d2 = D[filas, orden[:, 0]], D[filas, orden[:, 1]]
        cercano = ids[orden[:, 0]]
        idx = out.index[ok]
        out.loc[idx, "corredor_cercano"] = cercano
        out.loc[idx, "dist_corredor_m"] = d1
        out.loc[idx, "corredor_id"] = np.where(d1 <= radio, cercano, None)
        out.loc[idx, "ambiguo"] = (d1 <= radio) & (d2 <= radio)
        out.loc[idx[d1 <= radio], "metodo_asignacion"] = "coordenadas"

    sin = ~ok & out["direccion_normalizada"].notna()
    if sin.any():
        por_dir = _partes(out.loc[sin, "direccion_normalizada"]).map(_por_direccion)
        por_dir = por_dir[por_dir.notna()]
        out.loc[por_dir.index, "corredor_id"] = por_dir
        out.loc[por_dir.index, "metodo_asignacion"] = "direccion"
    return out


# ---------------------------------------------------------------------------------------------
# Reporte
# ---------------------------------------------------------------------------------------------
if __name__ == "__main__":
    from src.seguridad import limpiar_itm

    lineas = []
    def log(t=""):
        print(t)
        lineas.append(str(t))

    itm = limpiar_itm()
    cat, rep = geometria_corredores(itm)

    log("=== 1 · Geometría por corredor ===")
    for cid, r in rep.iterrows():
        log(f"\n{cid} · {CORREDORES[cid][0]}")
        log(f"  estaciones del SIMM: {r['estaciones']} · dentro del tramo: {r['dentro']} · fuera: {r['fuera']}")
        log(f"  eje de las estaciones: {r['cadena_km']} km · tramo de Google Traffic: {r['tramo_gt_km']} km · "
            f"geometría final: {r['geometria_km']} km · hueco máximo entre puntos: {r['hueco_max_m']} m")
        log(f"  INICIO → {r['inicio']}")
        log(f"  FIN    → {r['fin']}")
        log(f"  regla: {r['regla']}")

    a = asignar_corredor(itm, cat)
    log("\n=== 2 · Coordenadas de relleno ===")
    rel = coordenadas_relleno(itm.assign(lat=_num(itm["lat"]), lon=_num(itm["lon"])))
    log(f"Incidentes en puntos repetidos con 10 o más direcciones: {int(rel.sum()):,} "
        "(no se excluyen: son intercambios viales, ver la lista)")

    i2 = itm.assign(lat=_num(itm["lat"]), lon=_num(itm["lon"]))
    g = i2.dropna(subset=["lat", "lon"]).groupby(["lat", "lon"])["direccion_normalizada"]
    top = g.agg(["size", "nunique"])
    top = top[(top["size"] > 100) & (top["nunique"] >= 10)].sort_values("size", ascending=False).head(12)
    log(f"Puntos de relleno: {int(((g.size() > 100) & (g.nunique() >= 10)).sum())} · los 12 más grandes:")
    for (la, lo_), r in top.iterrows():
        dirs = i2.loc[(i2["lat"] == la) & (i2["lon"] == lo_), "direccion_normalizada"].value_counts().head(3)
        log(f"  ({la:.6f}, {lo_:.6f}) · {r['size']} incidentes · {r['nunique']} direcciones · "
            + " | ".join(f"{k} ({v})" for k, v in dirs.items()))
    log("\nLos 5 puntos más repetidos en total (relleno o esquina):")
    for (la, lo_), n in g.size().sort_values(ascending=False).head(5).items():
        sub = i2[(i2["lat"] == la) & (i2["lon"] == lo_)]
        dirs = sub["direccion_normalizada"].value_counts().head(2)
        log(f"  ({la:.6f}, {lo_:.6f}) · {n} incidentes · {sub['direccion_normalizada'].nunique()} direcciones · "
            + " | ".join(f"{k} ({v})" for k, v in dirs.items()))

    log("\n=== 3 · Asignación de los incidentes graves del ITM ===")
    log(f"Incidentes graves: {len(a):,} · asignados (≤{RADIO_M} m o por dirección): {a['corredor_id'].notna().sum():,} "
        f"({a['corredor_id'].notna().mean():.1%})")
    log(a["metodo_asignacion"].value_counts().to_string())
    tabla = pd.DataFrame({f"≤{r} m": a.loc[a["dist_corredor_m"] <= r, "corredor_cercano"].value_counts()
                          for r in (30, 50, 100)})
    tabla["por dirección"] = a.loc[a["metodo_asignacion"] == "direccion", "corredor_id"].value_counts()
    tabla["ambiguos"] = a.loc[a["ambiguo"] == True, "corredor_id"].value_counts()
    log("\n" + tabla.reindex(list(CORREDORES)).fillna(0).astype(int).to_string())

    log("\n=== 4 · Validación: ¿la dirección nombra la vía del corredor asignado por coordenadas? ===")
    c = a[a["metodo_asignacion"] == "coordenadas"].copy()
    c["partes"] = _partes(c["direccion_normalizada"])
    for cid in CORREDORES:
        t = _tokens_alias(cid)
        d = c[c["corredor_id"] == cid]
        if t and len(d):
            log(f"  {cid}: {d['partes'].map(lambda ps: bool(t.intersection(ps))).mean():.0%} de {len(d):,}")
        elif len(d):
            log(f"  {cid}: sin número propio (se ubica solo por coordenadas) · {len(d):,} asignados")

    log("\n=== 5 · Direcciones que NO nombran la vía del corredor (las 6 más frecuentes) ===")
    for cid in CORREDORES:
        t = _tokens_alias(cid)
        d = c[(c["corredor_id"] == cid)]
        if t and len(d):
            otras = d.loc[~d["partes"].map(lambda ps: bool(t.intersection(ps))), "direccion_normalizada"]
            log(f"  {cid} ({len(otras):,}): " + " | ".join(f"{k} ({v})" for k, v in otras.value_counts().head(6).items()))

    a.drop(columns=["corredor_cercano"]).to_csv(PROCESSED / "incidentes_graves_corredor.csv", index=False, encoding="utf-8")
    REPORTE.write_text("\n".join(lineas), encoding="utf-8")
    print(f"\nReporte guardado en {REPORTE}")
