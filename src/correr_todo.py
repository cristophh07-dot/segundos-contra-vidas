"""
Corre los notebooks del proyecto en orden, uno a la vez, y guarda cada uno ya ejecutado.

Uso (desde la carpeta principal del repositorio):
    python -m src.correr_todo

Hace lo mismo que abrir cada notebook en Jupyter y elegir "Run All Cells", pero sin riesgo de
correr dos al mismo tiempo. Al terminar, el resultado se ve en notebooks/segundos_contra_vidas.ipynb.
"""
from __future__ import annotations

import pathlib
import sys
import time

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

ORDEN = [
    ("03_exponente_medellin.ipynb", "efecto de la velocidad"),
    ("05_prediccion.ipynb", "qué pasa si no se hace nada"),
    ("06_montecarlo.ipynb", "vidas salvadas y segundos"),
    ("segundos_contra_vidas.ipynb", "notebook principal: la historia completa"),
]


def correr(ruta: pathlib.Path) -> None:
    nb = nbformat.read(ruta, as_version=4)
    total = sum(c.cell_type == "code" for c in nb.cells)
    hechas = {"n": 0}

    def al_empezar(cell, cell_index):
        if cell.cell_type == "code":
            hechas["n"] += 1
            print(f"      celda {hechas['n']} de {total}…", end="\r", flush=True)

    cliente = NotebookClient(nb, timeout=None, kernel_name="python3",
                             resources={"metadata": {"path": str(ruta.parent)}},
                             on_cell_start=al_empezar)
    cliente.execute()
    nbformat.write(nb, ruta)


def main() -> int:
    carpeta = pathlib.Path(__file__).resolve().parent.parent / "notebooks"
    print("Se corren 4 notebooks en orden. La primera vez se descargan unos 370 MB de datos:")
    print("puede tardar bastante. No cierre esta ventana.\n")
    inicio = time.time()
    for i, (nombre, que) in enumerate(ORDEN, 1):
        print(f"[{i}/{len(ORDEN)}] {nombre}  ({que})", flush=True)
        t0 = time.time()
        try:
            correr(carpeta / nombre)
        except CellExecutionError as e:
            print(f"\n\nFALLÓ {nombre}. El error fue:\n")
            print(str(e)[-1500:])
            print("\nRevise la sección 'Si algo sale mal' de instrucciones.txt y vuelva a correr este comando.")
            return 1
        print(f"      listo en {(time.time() - t0) / 60:.1f} min" + " " * 20)
    print(f"\nTodo corrió bien en {(time.time() - inicio) / 60:.0f} min.")
    print("Para ver el resultado:  python -m notebook   y abrir notebooks/segundos_contra_vidas.ipynb")
    return 0


if __name__ == "__main__":
    sys.exit(main())
