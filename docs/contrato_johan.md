# Contrato de trabajo – Johan
## Hackathon de Datos 2026 · ITM · Equipo de Cristopher, Josué y Johan

> **Para la IA que use Johan:** este documento es el contexto completo de su parte del proyecto. Léelo entero antes de ayudar. Johan es responsable de los **datos de velocidad y tráfico, el costo en tiempo, el módulo de motos, los referentes internacionales y la comunicación** (guía de entrega y pitch). Lo que produzca lo usan Cristopher (líder, modelos estadísticos) y Josué (datos de seguridad), así que el **formato de salida de la sección 6 es obligatorio**. No cambies nombres de archivos, funciones, columnas, tipos ni unidades. Si algo del contrato no se puede cumplir con los datos reales, la respuesta correcta es avisar a Cristopher, no inventar un formato propio. La prioridad es la **velocidad**: entregar en cuanto cada parte esté lista y pase las pruebas, sin esperar a terminar todo.
>
> **Regla de oro:** en este proyecto **no se trabaja con archivos descargados a mano**. Todo dato se lee **directamente desde su URL de descarga** con código. Ver la sección 3.

---

## 1. Contexto del proyecto

**Nombre:** *Segundos contra vidas: lo que Medellín puede aprender de Bogotá y Malasia.*

**Concurso:** Hackathon de Datos 2026 de la Institución Universitaria ITM, modalidad **análisis de datos**: un notebook reproducible (Jupyter o Colab) con un hallazgo y una recomendación. Temática: **transporte y movilidad**. Es obligatorio usar datos abiertos de **MEData** (portal de la Alcaldía de Medellín).

**Pregunta:** ¿en qué corredores viales de Medellín bajar la velocidad o crear un carril exclusivo para motos salvaría más vidas, y cuánto tiempo le costaría eso a quien se moviliza?

**La idea en simple:** encontramos las vías donde más muere la gente, medimos qué tan rápido se anda en ellas, estimamos cuánto pesa la velocidad en las muertes y simulamos qué pasaría si Medellín hiciera lo que hicieron Bogotá (bajar el límite a 50 km/h) y Malasia (carriles exclusivos para motos). La balanza final es **vidas salvadas contra segundos perdidos por viaje**.

**Las 6 partes del proyecto:**
1. Dónde muere la gente (diagnóstico) → Josué
2. Cuánto mata la velocidad en Medellín (regresión binomial negativa) → Cristopher
3. Qué hace mortal un choque (regresión logística) → Cristopher
4. Dónde y cuándo será el próximo choque grave (modelo de predicción) → Cristopher
5. Qué pasaría si se aplica lo de Bogotá y Malasia (simulación) → Cristopher y **Johan** (costo en tiempo y motos)
6. Recomendación final → los tres

**Ventanas de tiempo del proyecto:**
- Los datos públicos de velocidad van de **2017 a 2020**. Los modelos se estiman con **2017–2019**, donde se cruzan velocidad y siniestros.
- **2020** es año de pandemia y se marca aparte.
- Johan entrega **todos los años disponibles**; Cristopher filtra.

**Cómo se evalúa:** el jurado ejecuta el notebook en otro computador **siguiendo solo `instrucciones.txt`**. Si no corre, el proyecto no se califica.

---

## 2. Rol de Johan

Johan es el dueño de la **velocidad real de las vías** (sensores del SIMM y Google Traffic) y del **lado humano del proyecto**: cuánto tiempo cuesta la medida, qué hicieron otras ciudades y cómo se cuenta la historia en la guía de entrega y el pitch. Además entrega **primero que nadie** el catálogo de corredores, porque Josué lo necesita para asignar los incidentes.

---

## 3. Regla de datos: todo desde la URL de descarga

1. **Prohibido** trabajar con archivos bajados a mano (desde el navegador, WhatsApp, Drive, etc.).
2. Cada dataset se lee **por código desde su URL directa de descarga**: `pd.read_csv(URL)` o una consulta a la API.
3. Todas las URLs viven en **un solo archivo compartido**: `src/fuentes.py`. Nadie escribe una URL suelta dentro de un notebook.
4. Como algunos archivos pesan mucho (el del SIMM pasa de 70 MB), se permite una **caché automática**: el código guarda la descarga en `data/cache/` y, si ya existe, la reutiliza. Esa carpeta **no se sube al repositorio** (va en `.gitignore`) y **nunca se edita a mano**. Si se borra, el código vuelve a descargar todo desde la URL.
5. Los archivos procesados de la sección 6 se **generan siempre con código** a partir de las URLs. Si se borran, se regeneran corriendo el script.

**Las URLs YA ESTÁN LISTAS.** Cristopher entrega tres archivos que van en la carpeta `src/` del repositorio (junto con un `__init__.py` vacío):
- `src/fuentes.py`: las 8 fuentes del proyecto con su URL directa verificada, diccionario de datos, licencia y años. **No se modifica sin acuerdo de Cristopher.**
- `src/descarga.py`: la función `leer("clave")`, que descarga desde la URL, guarda la caché en `data/cache/`, detecta separador y codificación de los CSV, abre el zip de Mendeley y pagina el servicio ArcGIS de mortalidad. También trae `citar("clave")` para las referencias.
- `src/verificar_fuentes.py`: prueba rápida de que todas las URLs responden (`python -m src.verificar_fuentes`).

Para cargar cualquier dato basta con:

```python
from src.descarga import leer
df = leer("victimas_medata")
```

---

## 4. Fuentes de Johan (ya cargadas en `src/fuentes.py`)

| Clave en `FUENTES` | Dataset | Fuente | Años | Origen (referencia) |
|---|---|---|---|---|
| `velocidad_gt` | Velocidad y tiempo de viaje GT | MEData | feb. 2017 – dic. 2020 | https://medata.app.medellin.gov.co/dataset/1-023-25-000287 |
| `velocidad_simm` | Velocidad e intensidad vehicular en Medellín | MEData | desde mar. 2017 | https://medata.app.medellin.gov.co/dataset/1-023-25-000296 |
| `conteo_simm` | Conteo Vehicular (Simmtrafficdata) | MEData | desde 2021 (**verificar año máximo: puede traer volumen posterior a 2020**) | https://medata.app.medellin.gov.co/dataset/1-023-25-000300 |

**Lo que se sabe de estos datos (verificar con los archivos reales):**
- Google Traffic tendría **22 tramos de 11 corredores**, datos **cada hora de 6:00 a 20:00**. **No hay datos de noche** en esta fuente.
- El SIMM mide velocidades puntuales al paso por las cámaras CCTV y de apoyo a la red semafórica. **Revisa si cubre las 24 horas**: es la única forma de medir la velocidad nocturna.
- Según el diccionario del SIMM, la "Categoría 4" son motos, pero solo en algunos dispositivos.

---

## 5. Qué tiene que hacer Johan (en este orden)

### Tarea 1 · Fuentes y lectura
- Las URLs ya están en `src/fuentes.py`. Correr `python -m src.verificar_fuentes` y avisar a Cristopher si alguna falla.
- Comprobar que `leer("velocidad_gt")`, `leer("velocidad_simm")` y `leer("conteo_simm")` funcionan.
- **Urgente:** confirmar años (sobre todo de `conteo_simm`), horas cubiertas (¿hay datos de noche?) y corredores de cada fuente. Envía el resumen a Cristopher apenas lo tengas.

### Tarea 2 · Catálogo de corredores (la primera entrega del equipo)
Josué lo necesita para trabajar, así que va antes que todo lo demás. Los corredores salen de los tramos de Google Traffic y de los corredores del SIMM. Para cada uno:
- Un `corredor_id` corto y estable, en mayúscula con guiones bajos (por ejemplo `AV_80`, `AV_REGIONAL`, `CL_10`).
- Los patrones de dirección con que aparece en los incidentes (columna `alias_direccion`, separados por `|`), para que Josué pueda buscarlo por texto.
- Su longitud en km. Es clave para el costo en tiempo. Si los datos no la traen, mídela con la geometría o un mapa y anota la fuente.
- Geometría (línea WKT) o al menos la ubicación de las cámaras, si se puede obtener.

### Tarea 3 · Velocidad y volumen por corredor y hora (`src/velocidad.py`)
- Limpiar los datos del SIMM: quitar lecturas inválidas (los datos traen un indicador de validez cuando el sensor registra menos del 80 % del tiempo).
- Agregar por **corredor + fecha + hora**: velocidad media, vehículos por hora y motos por hora.
- Hacer lo mismo con Google Traffic: velocidad y tiempo de viaje (si un corredor tiene varios tramos, ponderar por longitud).
- Gráfica: velocidad media por hora del día en los corredores principales. Lo que buscamos ver es si de noche se anda mucho más rápido, si hay datos para medirlo.

### Tarea 4 · Referentes
Archivo `docs/referentes.md`. Usa **solo cifras de fuentes que hayas abierto y leído**, con enlace:
- **Bogotá:** en octubre de 2018 bajó el límite de 60 a 50 km/h en 5 corredores (Boyacá, Las Américas, Carrera 68, Ciudad de Cali, Calle 80), y las muertes en ellos bajaron alrededor de 32 %. Fuente: bogota.gov.co.
- **Malasia:** en el carril exclusivo de motos de la autopista Federal F02 se observó una reducción de 25 % en accidentes de moto (34 % sin contar la calzada principal). Otros estudios reportan 39 %. Fuente: Radin Umar et al., IATSS Research, 1995.
- **Power Model de Nilsson:** las muertes cambian aproximadamente con la cuarta potencia de la velocidad media (los heridos graves, con la tercera). En vías urbanas el efecto es más incierto: SWOV reporta un exponente de 3,0 para muertes en vías urbanas, con intervalo de -0,5 a 6,5. Fuentes: swov.nl; Cameron y Elvik, 2010.
- **Antecedente local:** Arango, Quiceno y Correa (2026), base de incidentes de Medellín 2008–2025, revista *Data* (MDPI) y Mendeley Data.
- Escribe para cada referente: qué se hizo, el resultado, la fuente y **por qué aplica o no a Medellín**.

### Tarea 5 · Costo en tiempo
Cuando Cristopher entregue el **exponente estimado para Medellín** y los corredores prioritarios, calcula para cada corredor, franja horaria y escenario cuántos **segundos extra por viaje** costaría la medida. Puedes dejar el código listo desde antes con los datos de velocidad.

La regla clave: un límite de velocidad solo cuesta tiempo donde hoy se anda **por encima** de ese límite. En hora pico, con trancón, el costo suele ser casi cero.

```text
v_escenario = min(v_actual, limite_del_escenario)
segundos_extra = (longitud_km / v_escenario - longitud_km / v_actual) * 3600
```

Franjas: `pico_am` (6–9 h), `valle` (9–17 h), `pico_pm` (17–20 h), `noche` (20–6 h, solo si el SIMM tiene datos nocturnos; si no, se omite y se declara como limitación).
Escenarios: `limite_50` (50 km/h todo el día), `limite_40` (40 km/h todo el día) y `nocturno_40` (40 km/h solo de 20 a 6 h).

### Tarea 6 · Módulo de motos
Con `incidentes_limpios()` de Josué (columna `hay_moto`) y los volúmenes de motos:
- **Riesgo por exposición:** incidentes graves con moto por cada millón de motos que pasan por el corredor. El corredor con más choques no es necesariamente el más riesgoso.
- Ranking de corredores candidatos a carril exclusivo.
- Estimación de incidentes evitables con el rango de Malasia (25 % a 39 %).
- Si los sensores no cuentan motos en suficientes corredores, avisa a Cristopher y usa el volumen total como aproximación, declarándolo como limitación.

### Tarea 7 · Comunicación
- Redactar la **`guia_entrega.pdf`** (ficha de hallazgos) con los resultados de los tres, incluyendo al menos una propuesta de mejora.
- Ayudar a redactar `instrucciones.txt` con la plantilla de las bases. Debe explicar que los datos **se descargan solos desde las URLs** al correr el notebook.
- **Diapositivas del pitch:** poco texto, sobre todo gráficas, cifras y mensajes clave.
- Estructura del pitch de 5 minutos: Problema 45 s (Josué), Datos 75 s (Johan), Demostración 120 s (Cristopher), Aporte 60 s (Cristopher).
- Si somos finalistas: `resumen_pitch.pdf` de una página.

---

## 6. Lo que Johan entrega (formato obligatorio)

La entrega **no es un archivo suelto**, sino **funciones en `src/velocidad.py`** que leen desde las URLs y devuelven las tablas con el formato exacto de abajo. Cada función también guarda su resultado en `data/processed/` (carpeta regenerable, fuera del repositorio). Se entregan **en cuanto estén listas y pasen las pruebas**, en este orden.

```python
# src/velocidad.py
def catalogo_corredores() -> pd.DataFrame: ...         # data/processed/catalogo_corredores.csv  (primera entrega)
def velocidad_corredor_hora() -> pd.DataFrame: ...     # data/processed/velocidad_corredor_hora.csv
def tiempo_viaje_gt() -> pd.DataFrame: ...             # data/processed/tiempo_viaje_gt.csv
def costo_tiempo_escenarios() -> pd.DataFrame: ...     # data/processed/costo_tiempo_escenarios.csv
def riesgo_motos_corredor() -> pd.DataFrame: ...       # data/processed/riesgo_motos_corredor.csv
```

### 6.1 `catalogo_corredores()` → para Josué y Cristopher (primera entrega)

| Columna | Tipo | Descripción |
|---|---|---|
| `corredor_id` | texto | Identificador único, por ejemplo `AV_80` |
| `nombre` | texto | Nombre legible, por ejemplo "Avenida 80" |
| `alias_direccion` | texto | Patrones de dirección separados por `\|`, en mayúscula y sin tildes, por ejemplo `CR 80\|AV 80` |
| `longitud_km` | decimal | Longitud del tramo analizado |
| `fuente_longitud` | texto | De dónde salió la longitud |
| `geometria_wkt` | texto | Línea del corredor en formato WKT (vacía si no se tiene) |
| `tiene_simm` | 0/1 | Tiene datos de sensores SIMM |
| `tiene_gt` | 0/1 | Tiene datos de Google Traffic |

### 6.2 `velocidad_corredor_hora()` → para Cristopher
Una fila por corredor, fecha y hora.

| Columna | Tipo | Descripción |
|---|---|---|
| `corredor_id` | texto | Debe existir en el catálogo |
| `fecha` | fecha `YYYY-MM-DD` | Fecha |
| `hora` | entero 0–23 | Hora |
| `velocidad_media_kmh` | decimal | Velocidad media de los sensores válidos |
| `intensidad_veh_h` | decimal | Vehículos por hora (todas las categorías) |
| `motos_veh_h` | decimal | Motos por hora (vacío si el sensor no las cuenta) |
| `n_sensores` | entero | Cuántos sensores aportaron a esa hora |
| `pct_valido` | decimal 0–100 | Porcentaje de lecturas válidas |

### 6.3 `tiempo_viaje_gt()` → para Cristopher y el costo en tiempo

| Columna | Tipo | Descripción |
|---|---|---|
| `corredor_id` | texto | Debe existir en el catálogo |
| `fecha` | fecha | Fecha |
| `hora` | entero 0–23 | Hora |
| `velocidad_gt_kmh` | decimal | Velocidad de Google Traffic |
| `tiempo_viaje_min` | decimal | Tiempo de viaje del corredor |

### 6.4 `costo_tiempo_escenarios()`

| Columna | Tipo | Descripción |
|---|---|---|
| `corredor_id` | texto | Corredor |
| `franja` | texto | `pico_am`, `valle`, `pico_pm` o `noche` |
| `escenario` | texto | `limite_50`, `limite_40` o `nocturno_40` |
| `v_actual_kmh` | decimal | Velocidad media actual en la franja |
| `v_escenario_kmh` | decimal | Velocidad con la medida |
| `segundos_extra_viaje` | decimal | Segundos que se pierden por viaje |

### 6.5 `riesgo_motos_corredor()`

| Columna | Tipo | Descripción |
|---|---|---|
| `corredor_id` | texto | Corredor |
| `incidentes_graves_moto` | entero | Incidentes con heridos o muertos y al menos una moto |
| `motos_por_dia` | decimal | Promedio de motos diarias |
| `riesgo_por_millon_motos` | decimal | Incidentes graves por cada millón de motos |
| `ranking` | entero | 1 = mayor riesgo |
| `evitables_min` | decimal | Incidentes evitables por año con 25 % de reducción |
| `evitables_max` | decimal | Incidentes evitables por año con 39 % de reducción |

### 6.6 Pruebas de aceptación
Ninguna función se entrega sin pasar estas pruebas:

```python
from src.velocidad import catalogo_corredores, velocidad_corredor_hora
from src.fuentes import FUENTES

for clave in ["velocidad_gt", "velocidad_simm", "conteo_simm"]:
    assert FUENTES[clave]["url"].startswith("http"), f"Falta la URL de {clave}"

cat = catalogo_corredores()
vel = velocidad_corredor_hora()

assert cat["corredor_id"].is_unique
assert cat["corredor_id"].str.fullmatch(r"[A-Z0-9_]+").all()
assert cat["alias_direccion"].notna().all()
assert (cat["longitud_km"] > 0).all()

assert vel["corredor_id"].isin(cat["corredor_id"]).all()
assert not vel.duplicated(["corredor_id", "fecha", "hora"]).any()
assert vel["hora"].between(0, 23).all()
assert vel["velocidad_media_kmh"].dropna().between(1, 120).all()
assert vel["pct_valido"].between(0, 100).all()
print("Contrato cumplido ✔")
```

---

## 7. Lo que Johan recibe

| Qué | De | Momento |
|---|---|---|
| `incidentes_limpios()` | Josué | Apenas Josué la tenga lista |
| Exponente estimado (con IC) y corredores prioritarios | Cristopher | Cuando estén los modelos |
| Resultados y gráficas finales | Los tres | Al cierre del análisis |

## 8. Lo que la IA NO debe hacer
- No leer datos desde archivos bajados a mano, no escribir URLs fuera de `src/fuentes.py` y no cambiar las URLs que ya están ahí.
- No buscar fuentes nuevas por su cuenta: si falta algo, avisar a Cristopher.
- No cambiar el formato de la sección 6.
- No poner 0 donde un sensor no midió.
- No inventar cifras de referentes: cada número de otra ciudad necesita una fuente abierta y citada.
- No hacer los modelos estadísticos (eso es de Cristopher).

## 9. Reglas generales del equipo
1. **Formato de archivos:** CSV en UTF-8, separador coma `,`, punto decimal `.`, con encabezado.
2. **Nombres de columnas:** `snake_case`, en minúscula, sin tildes ni ñ, sin espacios.
3. **Fechas en los datos:** `YYYY-MM-DD`. **Horas:** entero de 0 a 23, hora local de Medellín.
4. **Unidades:** velocidad en km/h, volumen en vehículos por hora, distancia en km, tiempo en segundos o minutos (indicado en el nombre de la columna).
5. **Coordenadas:** WGS84 en grados decimales.
6. **Valores faltantes:** celda vacía (NaN). Nunca `"N/A"`, `0` ni `-1` para representar un faltante.
7. **Solo datos reales:** prohibido generar datos sintéticos. Los parámetros de otras ciudades se usan como **supuestos citados**, no como datos.
8. **Cambios al contrato:** solo con acuerdo de Cristopher. Si una columna pedida no existe, se avisa **de inmediato**.
9. **Entregas parciales:** cada función se entrega apenas esté lista y pase sus pruebas.
10. **Git:** rama `johan`, integración con pull request. Cristopher revisa el trabajo de Johan antes de unirlo a `main`. `data/cache/` y `data/processed/` van en `.gitignore`.
11. **Uso de IA:** se permite, pero hay que declararlo en `docs/uso_ia_johan.md`.

**Entorno:** Python 3.11, `pandas`, `numpy`, `geopandas`, `shapely`, `matplotlib`, `requests`. Si necesitas otra librería, avisa para agregarla a `requirements.txt` con versión exacta.
