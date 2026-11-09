# Decisiones del proyecto

> **Para el equipo y para su IA:** este archivo manda. Si algo aquí contradice un contrato,
> vale lo que diga este archivo. Antes de cada sesión de trabajo: `git pull` y leer esto.
> Solo Cristopher (líder) agrega o cambia decisiones. Las más recientes van arriba.

## Pendientes (todavía no decidir por cuenta propia)

- (ninguno por ahora)

## Decisiones tomadas

| Fecha | # | Decisión | Afecta a |
|---|---|---|---|
| 2026-11-08 | D26 | **Backtest de la cuarentena (notebook 04):** corregida la composición de las víctimas, el exceso de muertes (O/E = 1,19; IC 0,93–1,50) no se distingue de los placebos 2015–2019 (0,89–1,20). **D19 se ajusta:** la cuarentena no se presenta como evidencia, sino como un resultado en la dirección esperada. El efecto de la velocidad sobre la letalidad entra al Monte Carlo como sensibilidad entre 0 y 2, no fijo en Nilsson. | Cristopher |
| 2026-11-08 | D25 | **`conteo_simm` sale de `src/fuentes.py`** (cierra P1). Solo trae enero de 2021, no se usa en ningún análisis (D5) y pesa 856 MB, lo que alarga la prueba de reproducibilidad. `src/explorar_johan.py` ya no la lee. | Todos |
| 2026-11-08 | D24 | El modelo logístico queda validado (AUC 0,76 en 2020–2021, calibrado, 353 muertos predichos contra 357 observados). Sus probabilidades se usan en el Monte Carlo para convertir incidentes graves en muertes esperadas según el perfil de las víctimas de cada corredor. | Cristopher |
| 2026-11-08 | D23 | La reducción de velocidad se presenta como la medida que protege a los más vulnerables (peatón ×3,4, ciclista ×2,8, 60+ ×5,7). El carril de motos protege por volumen (~75 % de las víctimas). | Todos |
| 2026-11-08 | D22 | Modelo logístico principal: actor, edad, sexo, franja, fin de semana, cuarentena y año, con errores agrupados por radicado. La clase de incidente va solo como sensibilidad (casi coincide con el actor). | Cristopher |
| 2026-11-08 | D21 | La velocidad nocturna por corredor sale de `velocidad_simm` (solo 2020): p85 y % de mediciones sobre 50 km/h, ponderado por intensidad, sin velocidades 0 ni mayores de 150. | Johan |
| 2026-11-08 | D20 | La hora entra en los modelos como control, no como efecto de la velocidad: de noche el p85 solo sube ~4 % y la letalidad es 5,6 veces la del día. El riesgo nocturno se reporta aparte como hallazgo. | Cristopher |
| 2026-11-08 | D19 | La cuarentena (mar–ago 2020: +29 % de velocidad, letalidad de moto +31 % y de peatón +37 %, p = 0,12) es **evidencia consistente, no prueba**. Sirve para contrastar el exponente de la binomial negativa. Las comparaciones de letalidad se hacen **por actor**, no con el promedio. | Cristopher |
| 2026-11-08 | D18 | La reducción de velocidad se evalúa **solo en las vías rápidas** (Regional, Autopista Norte, Autopista Sur, Las Palmas y demás de flujo continuo) **a cualquier hora**: ~20 % de las mediciones supera 50 km/h todo el día. En las arterias con semáforos no se evalúa (casi nadie pasa de 50). | Johan, Cristopher |
| 2026-11-08 | D17 | Los muertos por corredor (línea base de las vidas salvadas) salen de las coordenadas de `mortalidad_distrito`, 2019–2024. | Josué, Cristopher |
| 2026-11-08 | D16 | La regresión logística ("¿qué hace que una víctima muera?") se hace sobre `victimas_medata` (2014 a sep-2021), cuya etiqueta coincide con la cifra oficial. No se hace sobre la base del ITM. | Cristopher |
| 2026-11-08 | D15 | **Cierra P2.** El riesgo de motos por corredor = % de víctimas graves que iban en moto (`victimas_medata`), asignado al corredor por coordenadas. Las categorías del SIMM no sirven (la categoría 1 parece "livianos"). | Johan |
| 2026-11-08 | D14 | `motos_medata` tiene una fila por vehículo: se usa **sin radicados repetidos**. No se une con la base del ITM (la `llave` del ITM es un consecutivo, no el radicado). Sirve para el peso de la moto (~85 % de los incidentes graves) y la letalidad por diseño de vía. | Josué |
| 2026-11-08 | D13 | **La base del ITM no se usa para contar muertos:** registra entre el 52 % y el 91 % de los muertos oficiales según el año. Las vidas salvadas se calculan con `mortalidad_distrito` (2019–2024) y `victimas_medata` (2014–2021). El ITM se queda para incidentes graves (D8). El "pico" de 2022 no es real. | Todos |
| 2026-11-08 | D12 | `victimas_medata` tiene 1.048.317 filas, pero solo **235.843 son reales** (el resto está vacío): se filtra `ano` no nulo. Cubre ene-2014 a sep-2021. Unificar "Acompañante de Motocicleta" con "Acompañante de motocicleta". No se une con el ITM. | Josué |
| 2026-11-08 | D11 | La hora del incidente entra a los modelos como variable de control: la letalidad de madrugada es hasta 5 veces la del día. | Cristopher |
| 2026-11-08 | D10 | Valores de relleno = faltantes: "CALLE 999 CON CARRERA 999", "N/D" y coordenadas fuera de Medellín. El 2,5 % de los graves (sin dirección ni coordenadas) no se asigna a corredor, pero no se elimina. Las direcciones del ITM usan el número de la vía ("Calle 44", "Carrera 80"): los `alias_direccion` del catálogo deben usar ese formato. | Josué, Johan |
| 2026-11-08 | D9 | 2025 solo trae enero–agosto. **No se compara como año completo**: en series anuales se excluye o se compara contra enero–agosto de los otros años. | Todos |
| 2026-11-08 | D8 | Desde 2023 casi no se registran choques de solo daños (cambio de registro). **Todo el análisis usa solo incidentes graves (HERIDO + MUERTO).** | Todos |
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
