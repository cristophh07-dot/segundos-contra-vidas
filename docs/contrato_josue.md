# Contrato de trabajo – Josué
## Hackathon de Datos 2026 · ITM · Equipo de Cristopher, Josué y Johan

> **Para la IA que use Josué:** este documento es el contexto completo de su parte del proyecto. Léelo entero antes de ayudar. Josué es responsable de los **datos de seguridad vial y la visualización**. Lo que produzca lo usa Cristopher (líder) para los modelos estadísticos, así que el **formato de salida de la sección 6 es obligatorio**. No cambies nombres de archivos, funciones, columnas, tipos ni unidades. Si algo del contrato no se puede cumplir con los datos reales, la respuesta correcta es avisar a Cristopher, no inventar un formato propio. La prioridad es la **velocidad**: entregar en cuanto cada parte esté lista y pase las pruebas, sin esperar a terminar todo.
>
> **Regla de oro:** en este proyecto **no se trabaja con archivos descargados a mano**. Todo dato se lee **directamente desde su URL de descarga** con código. Ver la sección 3.

---

## 1. Contexto del proyecto

**Nombre:** *Segundos contra vidas: lo que Medellín puede aprender de Bogotá y Malasia.*

**Concurso:** Hackathon de Datos 2026 de la Institución Universitaria ITM, modalidad **análisis de datos**: un notebook reproducible (Jupyter o Colab) con un hallazgo y una recomendación. Temática: **transporte y movilidad**. Es obligatorio usar datos abiertos de **MEData** (portal de la Alcaldía de Medellín).

**Pregunta:** ¿en qué corredores viales de Medellín bajar la velocidad o crear un carril exclusivo para motos salvaría más vidas, y cuánto tiempo le costaría eso a quien se moviliza?

**Las 6 partes del proyecto:**
1. **Dónde muere la gente** (diagnóstico) → **Josué**
2. Cuánto mata la velocidad en Medellín (regresión binomial negativa) → Cristopher
3. Qué hace mortal un choque (regresión logística) → Cristopher
4. Dónde y cuándo será el próximo choque grave (modelo de predicción) → Cristopher
5. Qué pasaría si se aplica lo de Bogotá y Malasia (simulación) → Cristopher y Johan
6. Recomendación final → los tres

**Ventanas de tiempo del proyecto:**
- **2017–2019:** años donde se cruzan siniestros y velocidad. Ahí se estiman los modelos.
- **2020:** año de pandemia, se marca aparte.
- **2021–2025:** se usan para el diagnóstico reciente y para validar (backtest) los modelos.
- Josué entrega **todos los años disponibles (2008–2025)**; Cristopher filtra.

**Cómo se evalúa:** el jurado ejecuta el notebook en otro computador **siguiendo solo `instrucciones.txt`**. Si no corre, el proyecto no se califica.

---

## 2. Rol de Josué

Josué es el dueño de los **datos de seguridad vial** (incidentes, víctimas, motos y mortalidad) y de **las gráficas y mapas** del proyecto. Su trabajo es la base de todo: si los incidentes no están limpios y bien asignados a corredor, los modelos no sirven.

---

## 3. Regla de datos: todo desde la URL de descarga

1. **Prohibido** trabajar con archivos bajados a mano (desde el navegador, WhatsApp, Drive, etc.).
2. Cada dataset se lee **por código desde su URL directa de descarga**: `pd.read_csv(URL)`, `pd.read_excel(URL)` o una consulta a la API.
3. Todas las URLs viven en **un solo archivo compartido**: `src/fuentes.py`. Nadie escribe una URL suelta dentro de un notebook.
4. Como algunos archivos pesan mucho, se permite una **caché automática**: el código guarda la descarga en `data/cache/` y, si ya existe, la reutiliza. Esa carpeta **no se sube al repositorio** (va en `.gitignore`) y **nunca se edita a mano**. Si se borra, el código vuelve a descargar todo desde la URL.
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

## 4. Fuentes de Josué (ya cargadas en `src/fuentes.py`)

| Clave en `FUENTES` | Dataset | Fuente | Años | Origen (referencia) |
|---|---|---|---|---|
| `incidentes_itm` | Incidentes viales de Medellín (base de los profesores del ITM) — **principal** | Mendeley Data, DOI `10.17632/r6g5dfnpgh.1` | 2008 – ago. 2025 | https://data.mendeley.com/datasets/r6g5dfnpgh/1 (zip de 63 MB) |
| `victimas_medata` | Víctimas en incidentes viales | MEData | desde 2014 | https://medata.app.medellin.gov.co/dataset/1-023-25-000360 |
| `motos_medata` | Incidentes viales con motos | MEData | desde 2015 | https://medata.app.medellin.gov.co/dataset/1-023-25-000277 |
| `incidentes_medata` | Incidentes viales — **respaldo** si no aprueban la base del ITM | MEData | 2014 – ago. 2020 | https://medata.app.medellin.gov.co/dataset/1-023-25-000094 |
| `mortalidad_distrito` | Mortalidad en vías (1.541 fallecidos) | Observatorio de Movilidad (Distrito) | 2019 – 2024 | Servicio ArcGIS de la Alcaldía; `leer()` pagina solo |

**Notas sobre los datos:**
- La base del ITM es la **principal** (está pendiente que la organización confirme que se admite; si no se aprueba, se reemplaza por "Incidentes viales" de MEData, que llega hasta agosto de 2020, y se avisa a Cristopher).
- La capa de mortalidad la entrega `leer()` ya en WGS84 (columnas `lat_wgs84` y `lon_wgs84`, además de `latitud` y `longitud`).
- **Víctimas trae 1.048.317 filas**, muy cerca del límite de Excel (1.048.576): puede estar recortado. Revisar el año máximo apenas se cargue y avisar a Cristopher.
- En víctimas, las coordenadas vienen con **coma decimal** (`6,2669`) y algunas tildes salen dañadas: corregir en la limpieza.
- Víctimas trae el campo **`radicado`**: probar si sirve para unir víctimas con incidentes.
- Los enlaces a los diccionarios de datos están en `src/fuentes.py` (campo `diccionario`); resúmelos en `docs/diccionario_seguridad.md`.

---

## 5. Qué tiene que hacer Josué (en este orden)

### Tarea 1 · Fuentes y lectura
- Las URLs ya están en `src/fuentes.py`. Correr `python -m src.verificar_fuentes` y avisar a Cristopher si alguna falla.
- Comprobar que `leer("incidentes_itm")`, `leer("victimas_medata")`, `leer("motos_medata")` y `leer("mortalidad_distrito")` funcionan.
- **Revisar y documentar las columnas reales** de cada dataset y los años que cubren. Envía ese resumen a Cristopher apenas lo tengas.

### Tarea 2 · Limpieza (`src/seguridad.py`)
- Normalizar fechas y horas. Crear `anio`, `mes`, `dia_semana`.
- Unificar la gravedad en tres valores exactos: `solo_danos`, `herido`, `muerto`.
- Limpiar coordenadas: si están fuera de Medellín o vacías, dejarlas vacías (no eliminar el registro).
- Normalizar direcciones para poder buscar el corredor: mayúsculas, sin tildes, abreviaturas uniformes (`CARRERA` → `CR`, `CALLE` → `CL`, `AVENIDA` → `AV`, `TRANSVERSAL` → `TV`, `DIAGONAL` → `DG`).
- Marcar si en el incidente hubo moto o peatón, cruzando con víctimas y con incidentes con motos cuando sea posible. Si no se puede determinar para un incidente, dejar el valor vacío (no poner 0).
- **Documentar cuántos registros se eliminaron y por qué** en `docs/limpieza_seguridad.md`.

### Tarea 3 · Asignar cada incidente a un corredor
Johan entrega primero `catalogo_corredores.csv`, con un `corredor_id` por cada vía principal que tiene datos de velocidad. Mientras llega, avanza en la limpieza.

Reglas de asignación, en este orden:
1. **Por coordenadas:** si el incidente tiene coordenadas y el catálogo trae geometría, se asigna al corredor si está a **50 m o menos** de la vía.
2. **Por dirección:** si no, se busca en `direccion_normalizada` alguno de los patrones de la columna `alias_direccion` del catálogo (por ejemplo `CR 80|AV 80`).
3. Si ninguna regla aplica, `corredor_id` queda vacío y `metodo_asignacion = "sin_asignar"`. Esos incidentes **no se borran**: sirven para el diagnóstico de ciudad.

Reporta el porcentaje de incidentes asignados por cada método.

### Tarea 4 · Diagnóstico: dónde muere la gente
En `notebooks/01_datos_seguridad.ipynb`:
- **Red de alta lesividad:** ordenar los corredores por muertos y heridos, y calcular qué porcentaje de corredores concentra qué porcentaje de las muertes. La frase objetivo es "el X % de los corredores concentra el Y % de las muertes".
- Perfil por **hora del día** y **día de la semana**: incidentes y proporción de muertos (¿la noche es más letal?).
- Perfil por **actor vial**: moto, peatón, carro, ciclista.
- Tendencia anual de muertos 2008–2025.
- Comparar los muertos de la base del ITM con la capa de mortalidad del Distrito (2019–2024): si las cifras coinciden, eso valida la base.

### Tarea 5 · Mapas y gráficas
- Mapa de incidentes graves y de la red de alta lesividad.
- Gráficas de los resultados de los modelos de Cristopher (él te pasa las tablas).
- **Estilo uniforme** para todo el proyecto:
  - Títulos y ejes en español, con unidades.
  - Paleta: muertos `#C0392B`, heridos `#E67E22`, solo daños `#95A5A6`, color principal `#2C3E50`.
  - Exportar PNG de 1600×900 px en `figuras/`, con nombres `NN_descripcion.png` (por ejemplo `01_red_alta_lesividad.png`).
  - Cada figura con un mensaje en el título (por ejemplo "De noche, 1 de cada X choques es mortal"), no solo "Incidentes por hora".

### Tarea 6 · Prueba de reproducibilidad
Cuando el notebook final esté integrado: clonar el repositorio en **otro computador**, **borrar `data/cache/`**, seguir **solo** `instrucciones.txt` y anotar todo lo que falle.

### Tarea 7 · Pitch
Josué presenta la parte de **Problema** (45 segundos): la cifra de muertos y la concentración en pocos corredores.

---

## 6. Lo que Josué le entrega a Cristopher (formato obligatorio)

La entrega **no es un archivo suelto**, sino **funciones en `src/seguridad.py`** que leen desde las URLs y devuelven las tablas con el formato exacto de abajo. Cada función también guarda su resultado en `data/processed/` (carpeta regenerable, fuera del repositorio).

```python
# src/seguridad.py
def incidentes_limpios() -> pd.DataFrame: ...   # escribe data/processed/incidentes_limpios.csv
def victimas_limpias() -> pd.DataFrame: ...     # escribe data/processed/victimas_limpias.csv
def mortalidad_distrito() -> pd.DataFrame: ...  # escribe data/processed/mortalidad_distrito.csv
```

Se entregan **en cuanto estén listas y pasen las pruebas de aceptación**, en este orden.

### 6.1 `incidentes_limpios()` (una fila por incidente)

| Columna | Tipo | Descripción |
|---|---|---|
| `incidente_id` | texto | Identificador del incidente en la fuente |
| `fuente` | texto | `itm` o `medata` |
| `fecha` | fecha `YYYY-MM-DD` | Fecha del incidente |
| `hora` | entero 0–23 | Hora del incidente (vacía si no hay) |
| `anio` | entero | Año |
| `mes` | entero 1–12 | Mes |
| `dia_semana` | entero 0–6 | 0 = lunes … 6 = domingo |
| `gravedad` | texto | Exactamente `solo_danos`, `herido` o `muerto` |
| `clase` | texto | `choque`, `atropello`, `volcamiento`, `caida_ocupante`, `incendio` u `otro` |
| `hay_moto` | 0/1 o vacío | 1 si hubo al menos una moto; vacío si no se puede saber |
| `hay_peaton` | 0/1 o vacío | 1 si hubo al menos un peatón víctima; vacío si no se puede saber |
| `lat` | decimal | Latitud WGS84 (vacía si no hay) |
| `lon` | decimal | Longitud WGS84 (vacía si no hay) |
| `direccion_normalizada` | texto | Dirección normalizada |
| `comuna` | texto | Nombre de la comuna |
| `barrio` | texto | Nombre del barrio (vacío si no hay) |
| `corredor_id` | texto | Debe existir en `catalogo_corredores.csv`; vacío si no se asignó |
| `metodo_asignacion` | texto | `coordenadas`, `direccion` o `sin_asignar` |

### 6.2 `victimas_limpias()` (una fila por víctima, fuente MEData)

| Columna | Tipo | Descripción |
|---|---|---|
| `incidente_id` | texto | Si se puede unir con los incidentes; si no, vacío (y avisar a Cristopher) |
| `fecha` | fecha | Fecha |
| `hora` | entero 0–23 | Hora |
| `gravedad_victima` | texto | `herido` o `muerto` |
| `condicion` | texto | `conductor_moto`, `parrillero`, `conductor_carro`, `pasajero`, `peaton`, `ciclista` u `otro` |
| `edad` | entero | Vacía si no hay |
| `sexo` | texto | `F`, `M` o vacío |
| `comuna` | texto | Comuna |
| `lat` | decimal | Vacía si no hay |
| `lon` | decimal | Vacía si no hay |
| `corredor_id` | texto | Igual que en incidentes |

### 6.3 `mortalidad_distrito()` (una fila por fallecido, 2019–2024)

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | texto | Identificador de la capa |
| `fecha` | fecha | Fecha de ocurrencia |
| `hora` | entero 0–23 | Hora de ocurrencia |
| `clase` | texto | Mismos valores que en incidentes |
| `edad` | entero | Edad del fallecido |
| `sexo` | texto | `F`, `M` o vacío |
| `comuna` | texto | Comuna |
| `lat` | decimal | WGS84 |
| `lon` | decimal | WGS84 |
| `corredor_id` | texto | Igual que en incidentes |

### 6.4 Documentación
`docs/diccionario_seguridad.md`: para cada fuente, nombre, URL, enlace al diccionario original, años cubiertos, número de filas, cómo se transformó cada columna y licencia.

### 6.5 Pruebas de aceptación
Ninguna función se entrega si no pasa estas pruebas. Inclúyelas al final del notebook:

```python
import pandas as pd
from src.seguridad import incidentes_limpios
from src.fuentes import FUENTES

for clave in ["incidentes_itm", "victimas_medata", "motos_medata", "mortalidad_distrito"]:
    assert FUENTES[clave]["url"].startswith("http"), f"Falta la URL de {clave}"

inc = incidentes_limpios()
cat = pd.read_csv("data/processed/catalogo_corredores.csv")

cols = ["incidente_id","fuente","fecha","hora","anio","mes","dia_semana","gravedad","clase",
        "hay_moto","hay_peaton","lat","lon","direccion_normalizada","comuna","barrio",
        "corredor_id","metodo_asignacion"]
assert list(inc.columns) == cols
assert inc["incidente_id"].is_unique
assert inc["hora"].dropna().between(0, 23).all()
assert inc["dia_semana"].between(0, 6).all()
assert set(inc["gravedad"].unique()) <= {"solo_danos", "herido", "muerto"}
assert set(inc["metodo_asignacion"].unique()) <= {"coordenadas", "direccion", "sin_asignar"}
assert inc["hay_moto"].dropna().isin([0, 1]).all() and inc["hay_peaton"].dropna().isin([0, 1]).all()
assert (inc["lat"].isna() | inc["lat"].between(6.1, 6.4)).all()
assert inc["corredor_id"].dropna().isin(cat["corredor_id"]).all()
print("Contrato cumplido ✔")
```

---

## 7. Lo que Josué recibe

| Qué | De | Momento |
|---|---|---|
| `catalogo_corredores.csv` | Johan | Es la primera entrega del equipo |
| Tablas de resultados de los modelos para graficar | Cristopher | Cuando estén los modelos |

## 8. Lo que la IA NO debe hacer
- No leer datos desde archivos bajados a mano, no escribir URLs fuera de `src/fuentes.py` y no cambiar las URLs que ya están ahí.
- No buscar fuentes nuevas por su cuenta: si falta algo, avisar a Cristopher.
- No cambiar el formato de la sección 6.
- No crear datos sintéticos ni rellenar coordenadas inventadas.
- No hacer los modelos estadísticos (eso es de Cristopher).
- No borrar incidentes sin corredor: se marcan como `sin_asignar`.

## 9. Reglas generales del equipo
1. **Formato de archivos:** CSV en UTF-8, separador coma `,`, punto decimal `.`, con encabezado.
2. **Nombres de columnas:** `snake_case`, en minúscula, sin tildes ni ñ, sin espacios.
3. **Fechas en los datos:** `YYYY-MM-DD`. **Horas:** entero de 0 a 23, hora local de Medellín.
4. **Coordenadas:** WGS84 en grados decimales.
5. **Valores faltantes:** celda vacía (NaN). Nunca `"N/A"`, `"sin dato"`, `0` ni `-1` para representar un faltante.
6. **Sin datos personales:** nada que identifique a una persona. Edad y sexo sí se pueden usar.
7. **Solo datos reales:** prohibido generar datos sintéticos (las bases del concurso lo descalifican).
8. **Cambios al contrato:** solo con acuerdo de Cristopher. Si una columna pedida no existe, se avisa **de inmediato**.
9. **Entregas parciales:** cada función se entrega apenas esté lista y pase sus pruebas.
10. **Git:** rama `josue`, integración con pull request. Johan revisa el trabajo de Josué antes de unirlo a `main`. `data/cache/` y `data/processed/` van en `.gitignore`.
11. **Uso de IA:** se permite, pero hay que declararlo en `docs/uso_ia_josue.md`.

**Entorno:** Python 3.11, `pandas`, `numpy`, `geopandas`, `shapely`, `matplotlib`, `requests`, `openpyxl`. Si necesitas otra librería, avisa para agregarla a `requirements.txt` con versión exacta.
