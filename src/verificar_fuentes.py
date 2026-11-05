"""
Verifica que todas las URLs de src/fuentes.py respondan, sin descargar los archivos completos.
Uso (desde la carpeta principal del repo):  python -m src.verificar_fuentes
"""
import requests

from src.fuentes import FUENTES

HEADERS = {"User-Agent": "hackathon-itm-2026"}

for clave, f in FUENTES.items():
    url = f.get("url")
    if not url:
        print(f"[FALTA URL] {clave}")
        continue
    try:
        if f["formato"] == "arcgis":
            r = requests.get(url, params={"where": "1=1", "returnCountOnly": "true", "f": "json"},
                             headers=HEADERS, timeout=60)
            r.raise_for_status()
            print(f"[OK] {clave}: {r.json().get('count')} registros")
            continue
        # Pide solo los primeros bytes para no bajar el archivo entero
        r = requests.get(url, headers={**HEADERS, "Range": "bytes=0-2047"}, timeout=60, stream=True)
        tamano = r.headers.get("Content-Range", "").split("/")[-1] or r.headers.get("Content-Length")
        muestra = next(r.iter_content(2048), b"")
        r.close()
        if r.status_code not in (200, 206):
            print(f"[ERROR {r.status_code}] {clave}")
            continue
        mb = f"{int(tamano) / 1e6:.0f} MB" if tamano and tamano.isdigit() else "tamaño desconocido"
        if f["formato"] == "zip":
            tipo = "zip válido" if muestra[:2] == b"PK" else "NO parece zip"
            print(f"[OK] {clave}: {mb}, {tipo}")
        else:
            encabezado = muestra.decode("latin-1").splitlines()[0][:120]
            print(f"[OK] {clave}: {mb} · encabezado: {encabezado}")
    except Exception as e:
        print(f"[ERROR] {clave}: {e}")
