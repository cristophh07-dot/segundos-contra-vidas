# Diccionario de datos de seguridad vial

Todas las fuentes se leen con `leer("clave")` desde las URLs de `src/fuentes.py`.
Salidas procesadas (regenerables, no van al repositorio): `data/processed/`.

## 1. incidentes_itm (fuente principal de incidentes)
- **Nombre:** Dataset on Road Traffic Fatalities in Medellín, Colombia (2008–2025)
- **Autores:** Arango, Quiceno y Correa (2026). Mendeley Data, DOI 10.17632/r6g5dfnpgh.1
- **Página:** https://data.mendeley.com/datasets/r6g5dfnpgh/1
- **URL de descarga:** definida en `src/fuentes.py` (clave `incidentes_itm`)
- **Diccionario original:** `Data_Dictionary_Fatal_Road_Traffic.xlsx`, dentro del mismo zip
- **Años:** 2008 a agosto de 2025 (2025 es parcial, D9)
- **Filas:** 702.540 (hoja "BD" del archivo `Fatal_Road_Traffic.xlsx`)
- **Licencia:** CC BY 4.0
- **Uso:** incidentes graves (D8). No sirve para contar muertos: registra entre el 52 % y el 91 % de los fallecidos oficiales (D13).

| Columna original | Columna en `incidentes_limpios()` | Transformación |
|---|---|---|
| LLAVE | incidente_id | Texto. Es un consecutivo único, no el radicado. |
| (constante) | fuente | `itm` |
| FECHA_INCIDENTE | fecha | Formato YYYY-MM-DD |
| HORA_INCIDENTE | hora | Entero 0–23 |
| FECHA_INCIDENTE | anio, mes, dia_semana | Derivadas de la fecha (0 = lunes) |
| GRAVEDAD_INCIDENTE | gravedad | SOLO DAÑOS → `solo_danos`, HERIDO → `herido`, MUERTO → `muerto` |
| CLASE_INCIDENTE | clase | Choque, Atropello, Volcamiento, Caída Ocupante, Incendio; el resto → `otro` |
| (no disponible) | hay_moto | Vacío: el ITM no se une con víctimas ni motos (D12, D14) |
| CLASE_INCIDENTE | hay_peaton | 1 si la clase es atropello; vacío en las demás |
| Latitud, Longitud | lat, lon | Fuera de Medellín (lat 6,1–6,4; lon −75,75 a −75,45) o vacías → vacías |
| DIRECCION_INTERPOLADA | direccion_normalizada | Mayúsculas, sin tildes, CARRERA→CR, CALLE→CL, AVENIDA→AV, TRANSVERSAL→TV, DIAGONAL→DG. Relleno ("CALLE 999 CON CARRERA 999", N/D) → vacío (D10) |
| Comuna Planeacion | comuna | "N/D" → vacío |
| Barrio Planeacion | barrio | "Sin inf" → vacío |
| (pendiente) | corredor_id, metodo_asignacion | Vacío y `sin_asignar` hasta recibir el catálogo de corredores |

## 2. victimas_medata
- **Nombre:** MEData – Víctimas en Incidentes viales (Secretaría de Movilidad de Medellín)
- **Página:** https://medata.app.medellin.gov.co/dataset/1-023-25-000360
- **Diccionario original:** https://medata.app.medellin.gov.co/sites/default/files/distribution/1-023-25-000360/diccionario_mede_victimas_inci.json
- **Años:** 2014-01-01 a 2021-09-30
- **Filas:** 1.048.317 en el archivo; **235.843 reales** (233.894 heridos y 1.949 muertos). Las 812.474 restantes están completamente vacías (D12).
- **Licencia:** CC BY-SA 4.0
- **Uso:** letalidad y perfil de las víctimas (D16).

| Columna original | Columna en `victimas_limpias()` | Transformación |
|---|---|---|
| (no disponible) | incidente_id | Vacío: no se une con el ITM (D12) |
| Fecha_incidente | fecha | d/mm/aaaa → YYYY-MM-DD |
| Hora_incidente | hora | Entero 0–23 |
| Gravedad_victima | gravedad_victima | Heridos → `herido`, Muertos → `muerto` |
| Condicion | condicion | Motociclista → `conductor_moto`; Acompañante de motocicleta (ambas escrituras) → `parrillero`; Conductor → `conductor_carro`; Pasajero → `pasajero`; Peatón → `peaton`; Ciclista → `ciclista`; otro → `otro` |
| Edad | edad | Entero 0–110; fuera de rango → vacío |
| Sexo | sexo | M o F; "Sin Inf" / "Sin inf" → vacío |
| Comuna | comuna | Se quita el prefijo numérico ("04 - Aranjuez" → "Aranjuez") |
| Latitud, Longitud | lat, lon | Coma decimal → punto; fuera de Medellín → vacías (22.960 sin coordenadas) |
| (pendiente) | corredor_id | Vacío hasta recibir el catálogo |

Nota: la columna `Radicado` existe en el original pero no está en el formato del contrato (6.2).

## 3. motos_medata
- **Nombre:** MEData – Incidentes Viales con Motos (Secretaría de Movilidad de Medellín)
- **Página:** https://medata.app.medellin.gov.co/dataset/1-023-25-000277
- **Diccionario original:** no publicado en `src/fuentes.py`
- **Años:** 2015 a agosto de 2021
- **Filas:** 223.439 (una fila por vehículo, con radicados repetidos). Sin coordenadas.
- **Licencia:** CC BY-SA 4.0
- **Uso:** peso de la moto en los incidentes graves y letalidad por diseño de vía, sin radicados repetidos (D14). No genera una tabla procesada propia en `seguridad.py`.
- **Problemas conocidos:** codificación dañada en "SOLO DAÑOS"; 52.726 fechas no se leen con el formato d/mm/aaaa.

## 4. mortalidad_distrito
- **Nombre:** Alcaldía de Medellín – Secretaría de Movilidad – Observatorio de Movilidad, capa Mortalidad
- **Página:** https://www.medellin.gov.co/servidormapas/rest/services/transporte/VM_Mortalidad/MapServer/0
- **Diccionario original:** metadatos de la capa (misma página)
- **Años:** 2019-01-01 a 2024-12-31
- **Filas:** 1.541 (27 comparten `id` con otro fallecido; no son duplicados, D17)
- **Licencia:** uso para análisis y planificación (ver metadatos de la capa)
- **Uso:** línea base de muertos por corredor, por coordenadas (D17).

| Columna original | Columna en `mortalidad_distrito()` | Transformación |
|---|---|---|
| id | id | Texto. **No es único.** |
| fecha_ocurrencia | fecha | d/mm/aaaa → YYYY-MM-DD |
| hora_ocurrencia | hora | Entero 0–23 |
| clase | clase | Choque, Atropello, Caída Ocupante, Volcamiento, Incendio; Otros y Sumersión → `otro`; vacío se queda vacío |
| edad_fallecido | edad | Entero 0–110 |
| sexo_fallecido | sexo | M o F; "Sin Información" → vacío |
| nom_comuna | comuna | "La Calendaria" → "La Candelaria"; "0" → vacío |
| lat_wgs84, lon_wgs84 | lat, lon | Coordenadas WGS84 (4 vacías) |
| (pendiente) | corredor_id | Vacío hasta recibir el catálogo |

## No usadas
- `incidentes_medata`: respaldo si no se aprobaba la base del ITM. Cubre hasta ago. 2020. No se procesa.