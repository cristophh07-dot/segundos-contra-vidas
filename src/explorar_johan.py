"""
src/explorar_johan.py — Tarea 1: columnas, años, horas y corredores de las fuentes de Johan.
Uso (desde la carpeta principal del repo):  python -m src.explorar_johan
Genera docs/exploracion_johan.txt. Pega ese archivo en el chat.
No modifica datos: solo lee con src.descarga.leer().
"""
import pathlib
from collections import Counter

import pandas as pd

from src.descarga import leer

CLAVES = ["velocidad_gt", "velocidad_simm", "conteo_simm"]
SALIDA = pathlib.Path("docs/exploracion_johan.txt")
PISTAS_FECHA = ("fecha", "date", "time", "inicio", "fin")
PISTAS_HORA = ("hora", "hour")
PISTAS_CATEG = ("corredor", "nombre", "via", "calle", "direccion", "sentido",
                "dispositivo", "tramo", "name", "carril", "categoria", "valid",
                "device", "clasific", "operacion", "flujo", "identificador", "tipo_")
PISTAS_NUM = ("veloc", "speed", "intens", "longitud", "tiempo", "conteo", "count",
              "tv_", "ocupacion", "headway", "registros")
MAX_UNICOS = 300

lineas = []


def log(txt=""):
    print(txt)
    lineas.append(str(txt))


def cols_con(columnas, pistas):
    return [c for c in columnas if any(p in c.lower() for p in pistas)]


def explorar(clave):
    log("=" * 70)
    log(f"FUENTE: {clave}")
    log("=" * 70)

    muestra = leer(clave, nrows=2000)
    log(f"Columnas ({len(muestra.columns)}):")
    for c in muestra.columns:
        log(f"  - {c}  [{muestra[c].dtype}]  ej: {muestra[c].dropna().iloc[0] if muestra[c].notna().any() else 'vacía'}")

    c_fecha = cols_con(muestra.columns, PISTAS_FECHA)
    c_hora = [c for c in cols_con(muestra.columns, PISTAS_HORA) if c not in c_fecha]
    c_anio = [c for c in muestra.columns if c.lower() in ("ano", "año")]
    c_categ = [c for c in cols_con(muestra.columns, PISTAS_CATEG) if c not in c_fecha]
    c_num = [c for c in cols_con(muestra.columns, PISTAS_NUM)]
    usar = list(dict.fromkeys(c_fecha + c_hora + c_anio + c_categ + c_num))
    log(f"\nColumnas de fecha detectadas: {c_fecha}")
    log(f"Columnas de hora detectadas: {c_hora}")
    log(f"Columnas categóricas detectadas: {c_categ}")
    log(f"Columnas numéricas detectadas: {c_num}")

    filas = 0
    fmin, fmax = {}, {}
    ok_fecha = Counter()
    horas_col = {c: Counter() for c in c_hora}
    horas_dt = Counter()
    anios = Counter()
    unicos = {c: Counter() for c in c_categ}
    nulos = Counter()
    desc_num = {c: [] for c in c_num}

    for trozo in leer(clave, usecols=usar, chunksize=500_000):
        filas += len(trozo)
        for c in usar:
            nulos[c] += int(trozo[c].isna().sum())
        for i, c in enumerate(c_fecha):
            serie = trozo[c].dropna()
            dayfirst = bool(len(serie)) and "/" in str(serie.iloc[0])  # 1/02/2017 = 1 de febrero
            f = pd.to_datetime(trozo[c], errors="coerce", dayfirst=dayfirst)
            if getattr(f.dt, "tz", None) is not None:
                f = f.dt.tz_convert("America/Bogota")  # FECHAHORA viene en UTC (Z)
            ok_fecha[c] += int(f.notna().sum())
            if f.notna().any():
                fmin[c] = min(fmin.get(c, f.min()), f.min())
                fmax[c] = max(fmax.get(c, f.max()), f.max())
                if i == 0:
                    horas_dt.update(f.dt.hour.dropna().astype(int).tolist())
        for c in c_anio:
            anios.update(trozo[c].dropna().astype(str).tolist())
        for c in c_hora:
            horas_col[c].update(trozo[c].dropna().astype(str).tolist())
        for c in c_categ:
            if len(unicos[c]) < MAX_UNICOS:
                unicos[c].update(trozo[c].dropna().astype(str).tolist())
        for c in c_num:
            x = pd.to_numeric(trozo[c].astype(str).str.replace(",", ".", regex=False), errors="coerce")
            if x.notna().any():
                desc_num[c].append((x.min(), x.max(), x.sum(), int(x.notna().sum())))

    log(f"\nFilas totales: {filas:,}")
    log("\nRango de fechas (parseadas):")
    for c in c_fecha:
        log(f"  {c}: {fmin.get(c)}  →  {fmax.get(c)}   (fechas válidas: {ok_fecha[c]:,})")
    if anios:
        log("\nFilas por año (columna de año de la fuente):")
        log("  " + ", ".join(f"{k}:{v:,}" for k, v in sorted(anios.items())))
    if horas_dt:
        log("\nHoras (extraídas de la 1.ª columna de fecha), conteo por hora 0–23:")
        log("  " + ", ".join(f"{h}:{horas_dt.get(h, 0):,}" for h in range(24)))
        log(f"  ¿Hay datos entre 20:00 y 5:59? {'SÍ' if any(horas_dt.get(h, 0) for h in list(range(20, 24)) + list(range(0, 6))) else 'NO'}")
    for c, cnt in horas_col.items():
        log(f"\nValores de '{c}': " + ", ".join(f"{k}:{v:,}" for k, v in sorted(cnt.items())[:40]))
    log("\nColumnas categóricas (valores únicos, máx. %d):" % MAX_UNICOS)
    for c, cnt in unicos.items():
        log(f"  {c}: {len(cnt)} únicos" + (" (¡tope alcanzado!)" if len(cnt) >= MAX_UNICOS else ""))
        for k, v in cnt.most_common(40):
            log(f"      {k}  ({v:,})")
    log("\nColumnas numéricas (mín, máx, promedio):")
    for c, parts in desc_num.items():
        if parts:
            n = sum(p[3] for p in parts)
            log(f"  {c}: {min(p[0] for p in parts)} , {max(p[1] for p in parts)} , {sum(p[2] for p in parts) / n:.2f}")
    log("\nNulos por columna:")
    for c in usar:
        log(f"  {c}: {nulos[c]:,} ({100 * nulos[c] / max(filas, 1):.1f} %)")
    log()


if __name__ == "__main__":
    for k in CLAVES:
        try:
            explorar(k)
        except Exception as e:
            log(f"[ERROR] {k}: {type(e).__name__}: {e}")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("\n".join(lineas), encoding="utf-8")
    print(f"\nReporte guardado en {SALIDA}")
