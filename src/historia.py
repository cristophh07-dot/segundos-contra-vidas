"""
src/historia.py — datos del notebook final (Segundos contra vidas).

Cada función devuelve una tabla lista para graficar. Si la tabla ya fue guardada en data/processed/
por los notebooks 01 a 06, la lee de ahí (rápido); si no, la calcula desde las fuentes con las
funciones de src/ (más lento la primera vez, porque descarga los datos).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

PROCESADOS = Path("data/processed")


def _seg():
    from src import seguridad
    return seguridad


def _cache(nombre: str, calcular):
    ruta = PROCESADOS / f"{nombre}.csv"
    if ruta.exists():
        return pd.read_csv(ruta, low_memory=False)
    return calcular()


def incidentes() -> pd.DataFrame:
    """Todos los incidentes del ITM (graves y solo daños), con año y gravedad."""
    df = _cache("incidentes_limpios", lambda: _seg().incidentes_limpios())
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["anio"] = df["fecha"].dt.year
    return df


def victimas() -> pd.DataFrame:
    """Víctimas de MEData (2014 – sep 2021), con año."""
    df = _cache("victimas_limpias", lambda: _seg().victimas_limpias())
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["anio"] = df["fecha"].dt.year
    return df


def mortalidad() -> pd.DataFrame:
    """Fallecidos del Distrito (2019–2024), con año."""
    df = _cache("mortalidad_distrito", lambda: _seg().mortalidad_distrito())
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["anio"] = df["fecha"].dt.year
    return df


def catalogo() -> pd.DataFrame:
    """Los 12 corredores con su geometría (D27)."""
    ruta = PROCESADOS / "catalogo_corredores.csv"
    cat = pd.read_csv(ruta) if ruta.exists() else None
    if (cat is None or "geometria_wkt" not in cat or cat["geometria_wkt"].isna().any()
            or "longitud_km" not in cat or cat["longitud_km"].isna().any()):
        from src.corredores import geometria_corredores
        cat = geometria_corredores()[0]
    return cat


def mortalidad_corredor() -> pd.DataFrame:
    """Fallecidos del Distrito con su corredor (D30)."""
    df = _cache("mortalidad_con_corredor", lambda: _seg().mortalidad_con_corredor(geometria=catalogo()))
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["anio"] = df["fecha"].dt.year
    return df


def muertes_por_anio(vic: pd.DataFrame, mor: pd.DataFrame) -> pd.DataFrame:
    """Serie oficial de muertos: víctimas de MEData hasta 2018 y Distrito desde 2019.
    Devuelve también 2019 en las dos fuentes, para mostrar que coinciden."""
    v = vic[vic["gravedad_victima"].eq("muerto") & vic["anio"].between(2014, 2020)].groupby("anio").size()
    m = mor[mor["anio"].between(2019, 2024)].groupby("anio").size()
    serie = pd.concat([v[v.index <= 2018], m]).rename("muertos").to_frame()
    serie["fuente"] = ["MEData · víctimas" if a <= 2018 else "Distrito · mortalidad" for a in serie.index]
    serie.attrs["empalme_2019"] = (int(v.get(2019, 0)), int(m.get(2019, 0)))
    return serie


def graves_y_danos(inc: pd.DataFrame) -> pd.DataFrame:
    """Incidentes por año en la base del ITM: graves (herido o muerto) y solo daños. Sin 2025 (incompleto, D9)."""
    d = inc[inc["anio"].between(2008, 2024)].copy()
    d["tipo"] = d["gravedad"].map(lambda g: "graves" if g in ("herido", "muerto") else "solo daños")
    return d.groupby(["anio", "tipo"]).size().unstack(fill_value=0)


# =====================================================================================
# Resultados de los notebooks 03 a 06 (el notebook final no repite esos cálculos)
# =====================================================================================
REQUISITOS = {
    "betas_bootstrap.npy": "03_exponente_medellin (bootstrap)",
    "betas_bootstrap_A.npy": "03_exponente_medellin (bootstrap)",
    "proyeccion_12_meses.csv": "05_prediccion (sección 5)",
    "mc_comparacion.csv": "06_montecarlo (sección 5)",
    "mc_muertos_corredor.csv": "06_montecarlo (1.1)",
    "mc_graves_corredor.csv": "06_montecarlo (1.3)",
}


def revisar_requisitos() -> list[str]:
    """Lista los resultados que faltan en data/processed/ y qué notebook los genera."""
    faltan = [f"{a}  →  correr {nb}" for a, nb in REQUISITOS.items() if not (PROCESADOS / a).exists()]
    print("Resultados de los anexos: todo listo." if not faltan else "Faltan:\n  " + "\n  ".join(faltan))
    return faltan


def exponentes():
    """Bootstrap del exponente de Medellín (notebook 03): modelo A (sin la hora) y C (con la hora)."""
    import numpy as np
    return np.load(PROCESADOS / "betas_bootstrap_A.npy"), np.load(PROCESADOS / "betas_bootstrap.npy")


def proyeccion() -> pd.DataFrame:
    return pd.read_csv(PROCESADOS / "proyeccion_12_meses.csv", index_col=0)


def comparacion() -> pd.DataFrame:
    return pd.read_csv(PROCESADOS / "mc_comparacion.csv", index_col=[0, 1])


def dia_noche_corredores() -> pd.DataFrame:
    """Incidentes graves y muertos de día y de noche en los 12 corredores (notebook 06, 1.1 y 1.3)."""
    m = pd.read_csv(PROCESADOS / "mc_muertos_corredor.csv", index_col=0)
    g = pd.read_csv(PROCESADOS / "mc_graves_corredor.csv", index_col=0)
    return pd.DataFrame({"muertos": m[["día", "noche"]].sum(), "incidentes graves": g[["día", "noche"]].sum()}).T


# =====================================================================================
# Tablas que el notebook final sí calcula (rápidas)
# =====================================================================================
def victimas_modelo() -> pd.DataFrame:
    """Víctimas con las variables del modelo logístico (src.modelos.preparar_victimas, D12, D22)."""
    from src.modelos import preparar_victimas
    return preparar_victimas()


def por_actor(m: pd.DataFrame) -> pd.DataFrame:
    """Víctimas, muertos y muertos por cada 100 víctimas según el actor."""
    grupos = {"Moto": "Moto", "Peatón": "Peatón", "Ciclista": "Ciclista"}
    a = m["actor"].map(grupos).fillna("Carro (conductor o pasajero)")
    t = m.groupby(a).agg(victimas=("muerto", "size"), muertos=("muerto", "sum"))
    t["por_100"] = t["muertos"] / t["victimas"] * 100
    return t.sort_values("muertos", ascending=False)


def muertos_peaton_moto(m: pd.DataFrame) -> pd.DataFrame:
    d = m[m["muerto"].eq(1) & m["actor"].isin(["Peatón", "Moto"])]
    return d.groupby(["ano", "actor"]).size().unstack(fill_value=0).loc[2014:2021]


def letalidad_diseno() -> pd.DataFrame:
    """Letalidad de los incidentes graves con moto según el diseño de la vía, un registro por incidente (D14)."""
    def calcular():
        from src.descarga import leer
        from src.utilidades import normalizar_columnas
        mo = normalizar_columnas(leer("motos_medata"))
        mo["gravedad_incidente"] = mo["gravedad_incidente"].str.replace(r"SOLO DA.*OS", "SOLO DAÑOS", regex=True)
        mo["diseno_via"] = (mo["diseno_via"].astype(str).str.replace(r"\\r$", "", regex=True)
                            .str.replace(r"\\xF3", "ó", regex=True).str.strip())
        mo = mo.drop_duplicates("nro_radicado")
        t = pd.crosstab(mo["diseno_via"], mo["gravedad_incidente"])
        t["graves"] = t["HERIDO"] + t["MUERTO"]
        t["letalidad_%"] = t["MUERTO"] / t["graves"] * 100
        t = t[t["graves"] >= 500].sort_values("letalidad_%", ascending=False)
        PROCESADOS.mkdir(parents=True, exist_ok=True)
        t.to_csv(PROCESADOS / "letalidad_diseno.csv")
        return t.reset_index()
    t = _cache("letalidad_diseno", calcular)
    return t.set_index(t.columns[0])


def dos_velocidades() -> pd.DataFrame:
    """Google Traffic 2017–2019, 6:00–19:59, con el tope de 50 aplicado registro por registro (D29)."""
    import numpy as np
    def calcular():
        from src.velocidad import tiempo_viaje_gt
        return tiempo_viaje_gt()
    tv = _cache("tiempo_viaje_gt", calcular)
    tv["ano"] = pd.to_datetime(tv["fecha"]).dt.year
    tv = tv[tv["ano"].between(2017, 2019) & tv["hora"].between(6, 19) & (tv["velocidad_gt_kmh"] > 0)].copy()
    largo = catalogo().set_index("corredor_id")["longitud_km"]
    v = tv["velocidad_gt_kmh"]
    tv["sobre_50"] = v > 50
    tv["seg_extra"] = (tv["corredor_id"].map(largo) * 3600 * (1 / np.minimum(v, 50) - 1 / v)).clip(lower=0)
    return tv


def cobertura_coordenadas(inc: pd.DataFrame) -> pd.Series:
    """% de los incidentes graves del ITM con coordenadas, por año (D32)."""
    g = inc[inc["gravedad"].isin(["herido", "muerto"]) & inc["anio"].between(2015, 2025)]
    return g.groupby("anio")["lat"].apply(lambda s: s.notna().mean() * 100)
