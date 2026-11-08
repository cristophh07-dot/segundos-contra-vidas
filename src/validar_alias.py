"""
src/validar_alias.py — Tarea 2: prueba cuántas direcciones de incidentes caen en cada alias candidato.
Uso (desde la carpeta principal del repo):  python -m src.validar_alias
Genera docs/validacion_alias.txt. Pega ese archivo en el chat.
Solo lee con src.descarga.leer(); no modifica datos.
"""
import pathlib
import re

from src.descarga import leer

SALIDA = pathlib.Path("docs/validacion_alias.txt")

# Candidatos propuestos (por validar con los datos). Las direcciones vienen como
# cruces en nomenclatura numérica: "CR 80 CL 62", "CR 43 A CL 34".
CANDIDATOS = {
    "AV_80": ["CR 80", "AV 80", "AVENIDA 80"],
    "AV_33": ["CL 33", "AV 33", "AVENIDA 33"],
    "CL_30": ["CL 30"],
    "AV_POBLADO": ["CR 43 A", "AV POBLADO", "AVENIDA EL POBLADO"],
    "AV_SAN_JUAN": ["CL 44", "AV SAN JUAN", "AVENIDA SAN JUAN"],
    "AV_ORIENTAL": ["CR 46", "AV ORIENTAL", "AVENIDA ORIENTAL"],
    "AV_GUAYABAL": ["CR 52", "AV GUAYABAL", "AVENIDA GUAYABAL"],
    "AUT_NORTE": ["CR 64 C", "AUTOPISTA NORTE", "AUT NORTE"],
    "AUT_SUR": ["CR 48", "AUTOPISTA SUR", "AUT SUR"],
    "AV_REGIONAL": ["CR 55", "AVENIDA REGIONAL", "AV REGIONAL"],
    "AV_FERROCARRIL": ["CR 57", "AV FERROCARRIL", "AVENIDA FERROCARRIL"],
    "AV_PALMAS": ["AV LAS PALMAS", "AVENIDA LAS PALMAS", "LAS PALMAS"],
}


def main():
    s = (leer("victimas_medata", usecols=["Direccion_incidente"])["Direccion_incidente"]
         .dropna().astype(str).str.upper().str.strip())
    s = s[s != ""]
    lineas = [f"Direcciones no vacías: {len(s):,}", ""]
    for cid, patrones in CANDIDATOS.items():
        lineas.append(f"== {cid}")
        for p in patrones:
            rx = r"(?<![A-Z0-9])" + re.escape(p) + r"(?![0-9])"
            m = s[s.str.contains(rx, regex=True)]
            con_letra = int(m.str.contains(rx + r"\s[A-Z](?=\s|$)", regex=True).sum())
            ej = " | ".join(m.drop_duplicates().head(4).tolist())
            lineas.append(f"  '{p}': {len(m):,} filas (con sufijo de una letra A/B/C: {con_letra:,}) · ej: {ej}")
        lineas.append("")
    texto = "\n".join(lineas)
    print(texto)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(texto, encoding="utf-8")
    print(f"Reporte guardado en {SALIDA}")


if __name__ == "__main__":
    main()
