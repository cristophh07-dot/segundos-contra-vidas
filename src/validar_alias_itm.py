"""
src/validar_alias_itm.py — confirma los alias de las vías rápidas contra direccion_interpolada
de la base del ITM (hoja BD de incidentes_itm).

Uso (desde la carpeta principal del repo):  python -m src.validar_alias_itm

- La primera vez lee el Excel de 63 MB: tarda varios minutos y usa 2-3 GB de RAM.
  Guarda las direcciones en data/cache/direcciones_itm.csv; las siguientes corridas son rápidas.
- Escribe docs/validacion_alias_itm.txt. Pega ese archivo en el chat.
- Solo lee con src.descarga.leer(); no modifica datos.
"""
import pathlib
import re
import unicodedata

import pandas as pd

from src.descarga import leer

COLUMNA = "direccion_interpolada"
CSV = pathlib.Path("data/cache/direcciones_itm.csv")
SALIDA = pathlib.Path("docs/validacion_alias_itm.txt")

# Números de vía candidatos por corredor. Cada candidato se prueba con su sufijo de letra
# (por ejemplo "CARRERA 64" cubre "CARRERA 64", "CARRERA 64 C", "CARRERA 64 B"...).
CANDIDATOS = {
    "AV_REGIONAL": ["CARRERA 55", "CARRERA 50"],
    "AUT_NORTE": ["CARRERA 64"],
    "AUT_SUR": ["CARRERA 48", "CARRERA 50"],
    "AV_GUAYABAL": ["CARRERA 52", "CARRERA 50"],
}
# Búsqueda por nombre, para ver si el nombre aparece en las direcciones.
NOMBRES = {
    "AV_REGIONAL": ["REGIONAL"],
    "AUT_NORTE": ["AUTOPISTA"],
    "AUT_SUR": ["AUTOPISTA"],
    "AV_PALMAS": ["PALMAS", "TRANSVERSAL SUPERIOR"],
    "AV_GUAYABAL": ["GUAYABAL"],
}

lineas = []


def log(txt=""):
    print(txt)
    lineas.append(str(txt))


def sin_tildes(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))


def cargar() -> pd.Series:
    if CSV.exists():
        s = pd.read_csv(CSV, dtype=str)[COLUMNA]
    else:
        print("Leyendo la hoja BD de incidentes_itm (varios minutos la primera vez)…")
        df = leer("incidentes_itm", sheet_name="BD", usecols=lambda c: "direccion" in str(c).lower())
        print("Columnas con 'direccion':", list(df.columns))
        real = [c for c in df.columns if str(c).lower() == COLUMNA]
        if not real:
            raise KeyError(f"No encontré la columna {COLUMNA}. Columnas con 'direccion': {list(df.columns)}")
        s = df[real[0]].rename(COLUMNA)
        CSV.parent.mkdir(parents=True, exist_ok=True)
        s.to_frame().to_csv(CSV, index=False)
    s = s.dropna().astype(str).map(sin_tildes).str.upper().str.strip()
    return s[s != ""].reset_index(drop=True)


def analizar_candidato(s: pd.Series, base: str) -> None:
    rx = re.compile(r"(?<![A-Z0-9])" + re.escape(base) + r"(?![0-9])(?:\s+([A-Z]{1,2})(?=\s|$))?")
    ext = s.str.extractall(rx)
    if ext.empty:
        log(f"  '{base}': 0 filas")
        return
    idx = ext.index.get_level_values(0).unique()
    filas = s.loc[idx]
    variantes = ext[0].fillna("(sin letra)").value_counts().head(6)
    cruces = pd.to_numeric(filas.str.extract(r"CALLE (\d+)")[0], errors="coerce").dropna()
    log(f"  '{base}': {len(idx):,} filas")
    log("     variantes: " + " · ".join(f"{k}: {v:,}" for k, v in variantes.items()))
    if len(cruces):
        log(f"     calle que cruza (p5 / mediana / p95): {cruces.quantile(.05):.0f} / {cruces.median():.0f} / {cruces.quantile(.95):.0f}")
    log("     ejemplos: " + " | ".join(filas.drop_duplicates().head(4).tolist()))


def main() -> None:
    s = cargar()
    log(f"Direcciones no vacías en {COLUMNA}: {len(s):,}")
    log("Ejemplos al azar: " + " | ".join(s.sample(8, random_state=1).tolist()))

    log("\n=== Números de vía candidatos ===")
    for cid, bases in CANDIDATOS.items():
        log(f"\n== {cid}")
        for b in bases:
            analizar_candidato(s, b)

    log("\n=== Búsqueda por nombre ===")
    for cid, nombres in NOMBRES.items():
        for n in nombres:
            m = s[s.str.contains(n, regex=False)]
            log(f"\n== {cid} · '{n}': {len(m):,} filas")
            for k, v in m.value_counts().head(12 if cid == "AV_PALMAS" else 5).items():
                log(f"     {k}  ({v:,})")

    log("\n=== Carreras más frecuentes en toda la base (con letra) ===")
    top = s.str.extractall(r"CARRERA (\d+(?:\s[A-Z]{1,2}(?=\s|$))?)")[0].value_counts().head(30)
    log(" · ".join(f"{k}: {v:,}" for k, v in top.items()))

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("\n".join(lineas), encoding="utf-8")
    print(f"\nReporte guardado en {SALIDA}")


if __name__ == "__main__":
    main()
