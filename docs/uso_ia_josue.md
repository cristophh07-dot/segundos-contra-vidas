# Uso de IA – Josué

**Herramienta:** Claude (Anthropic), asistente de conversación.
**Periodo:** noviembre de 2026.

## En qué se usó
| Tarea | Cómo ayudó la IA |
|---|---|
| Configuración | Pasos para el entorno (Python 3.11, entorno virtual, git, Visual Studio) |
| Exploración de datos | Script para ver columnas, años y valores de las 4 fuentes |
| Limpieza (`src/seguridad.py`) | Escribió el código de las tres funciones según el contrato |
| Diagnóstico (`src/diagnostico.py`) | Escribió el código de las 6 primeras figuras |
| Documentación | Borradores de `limpieza_seguridad.md` y `diccionario_seguridad.md` |

## Qué hice yo
- Ejecuté todo el código en mi computador y revisé los resultados.
- Compré las cifras contra los datos originales y las decisiones del equipo (`docs/DECISIONES.md`).
- Detecté y corregí problemas con los datos reales, por ejemplo: los 27 `id` repetidos en mortalidad eran fallecidos distintos y no se eliminaron.
- Revisé las figuras y sus títulos antes de subirlas.

## Datos
No se generaron datos sintéticos ni coordenadas inventadas. Todo se lee desde las URLs de `src/fuentes.py`.