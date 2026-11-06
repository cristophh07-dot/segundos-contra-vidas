# Decisiones del proyecto

> **Para el equipo y para su IA:** este archivo manda. Si algo aquí contradice un contrato,
> vale lo que diga este archivo. Antes de cada sesión de trabajo: `git pull` y leer esto.
> Solo Cristopher (líder) agrega o cambia decisiones. Las más recientes van arriba.

## Pendientes (todavía no decidir por cuenta propia)

- **P1 · ¿Sacar `conteo_simm` de `src/fuentes.py`?** No aporta datos nuevos y pesa 856 MB.
- **P2 · Riesgo de motos (Tarea 6 de Johan).** Ninguna fuente trae una columna clara de motos.
  Johan revisa el diccionario de `velocidad_simm` (categoria_1/2/3). Mientras tanto, no avanzar en el módulo de motos.

## Decisiones tomadas

| Fecha | # | Decisión | Afecta a |
|---|---|---|---|
| 2026-11-06 | D7 | Google Traffic tiene **12 corredores** (no 11). El catálogo usa los 12. | Johan, Josué |
| 2026-11-06 | D6 | Google Traffic no tiene datos de noche. **La velocidad nocturna sale de `velocidad_simm`**, que trae las 24 horas. | Johan |
| 2026-11-06 | D5 | `conteo_simm` solo trae enero de 2021. **No se usa por ahora.** | Johan |
| 2026-11-05 | D4 | Ventana de los modelos: **2017–2019**. 2020 aparte (pandemia). 2021–2025 para diagnóstico y backtest. | Todos |
| 2026-11-05 | D3 | Base principal de siniestros: **base del ITM (Mendeley)**. Respaldo: `incidentes_medata`. | Josué |
| 2026-11-05 | D2 | Los datos se leen **solo con `leer("clave")`** desde `src/fuentes.py`. No se cambian las URLs. | Todos |
| 2026-11-05 | D1 | Proyecto: *Segundos contra vidas*. Análisis de datos · Transporte y movilidad. | Todos |

## Cómo se agrega una decisión
1. Se escribe una fila nueva arriba de la tabla, con fecha, número siguiente (D8, D9…), la decisión en una línea y a quién afecta.
2. Si resuelve un pendiente, se borra de la lista de pendientes.
3. Commit con mensaje `Decisión D8: …` y aviso corto en el grupo: "hay decisión nueva, hagan git pull".
