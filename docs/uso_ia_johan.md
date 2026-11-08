# Uso de IA — Johan

**Herramienta:** Claude (Anthropic), en la interfaz de chat.

## Para qué se usó
- Preparar y depurar los scripts de exploración de las fuentes (`src/explorar_johan.py`) y de validación de alias (`src/validar_alias.py`).
- Escribir la primera versión de `src/velocidad.py` (`catalogo_corredores()`).
- Interpretar los reportes de exploración (años, horas, corredores, longitudes) y redactar mensajes de resumen para el equipo.
- Apoyo con la configuración del entorno (Python 3.11, entorno virtual, Git).

## Cómo se verificó
- Todos los scripts se ejecutaron en mi computador con los datos reales descargados desde las URLs de `src/fuentes.py`; nada se leyó desde archivos bajados a mano.
- Las cifras de los reportes (filas, años, horas, corredores, longitudes) salen de esas ejecuciones, no de la IA.
- Los códigos de dirección de los corredores (por ejemplo `CR 80`, `CL 44`) fueron propuestos por la IA a partir de la nomenclatura de Medellín y luego se contrastaron con datos reales: con las direcciones de `victimas_medata` (`docs/validacion_alias.txt`), con `direccion_interpolada` de la base del ITM (`docs/validacion_alias_itm.txt`) y, para identificar qué número corresponde a cada vía, cruzando los sensores del SIMM con las coordenadas de `victimas_medata` (`docs/validacion_alias_coord.txt`). Esa comprobación corrigió una propuesta inicial errónea de la IA (Autopista Sur es la Carrera 50, no la 48) y mostró que la Avenida Regional y Las Palmas no tienen un número de vía propio.
- El significado de las columnas de clasificación del SIMM se tomó del diccionario publicado por MEData (`simmtraffic.json`).

## Lo que la IA no hizo
- No se generaron datos sintéticos ni cifras de otras ciudades sin fuente.
- No se modificó `src/fuentes.py` ni las URLs.
- No se hicieron modelos estadísticos.
