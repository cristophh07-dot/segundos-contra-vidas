# Uso de IA — Johan

**Herramienta:** Claude (Anthropic), en la interfaz de chat.

## Para qué se usó
- Preparar y depurar los scripts de exploración de las fuentes (`src/explorar_johan.py`) y de validación de alias (`src/validar_alias.py`, `src/validar_alias_itm.py` y `src/validar_alias_coord.py`).
- Escribir la primera versión de `src/velocidad.py` (`catalogo_corredores()` y `tiempo_viaje_gt()`, incluido el promedio en dos pasos ponderado por longitud mediana).
- Interpretar los reportes de exploración (años, horas, corredores, longitudes) y redactar mensajes de resumen para el equipo.
- Leer `DECISIONES.md` y el contrato de trabajo, ordenar los pendientes y redactar los mensajes para Cristopher.
- Apoyo con la configuración del entorno (Python 3.11, entorno virtual, Git).
- Más adelante: apoyo en la redacción de `docs/referentes.md`, la guía de entrega y el pitch (se actualizará este archivo cuando se haga).

## Cómo se verificó
- La IA no ejecutó código con los datos. Todos los scripts los ejecuté yo en mi computador con los datos reales descargados desde las URLs de `src/fuentes.py`, y pegué las salidas en la conversación; nada se leyó desde archivos bajados a mano.
- Las cifras de los reportes (filas, años, horas, corredores, longitudes) salen de esas ejecuciones, no de la IA. Lo mismo aplica a las velocidades medias por corredor de `tiempo_viaje_gt()`; `python -m src.velocidad` pasa las pruebas de aceptación.
- Los códigos de dirección de los corredores (por ejemplo `CR 80`, `CL 44`) fueron propuestos por la IA a partir de la nomenclatura de Medellín y luego se contrastaron con datos reales: con las direcciones de `victimas_medata` (`docs/validacion_alias.txt`), con `direccion_interpolada` de la base del ITM (`docs/validacion_alias_itm.txt`) y, para identificar qué número corresponde a cada vía, cruzando los sensores del SIMM con las coordenadas de `victimas_medata` (`docs/validacion_alias_coord.txt`). Esa comprobación corrigió una propuesta inicial errónea de la IA (Autopista Sur es la Carrera 50, no la 48) y mostró que la Avenida Regional y Las Palmas no tienen un número de vía propio.
- Los alias de `AV_REGIONAL` son de baja confianza (el número más frecuente cerca de sus sensores, CR 62, llega solo al 32 %); ese corredor debe ubicarse por coordenadas.

## Lo que la IA no hizo
- No se generaron datos sintéticos ni cifras de otras ciudades sin fuente.
- No se incluyó ninguna cifra de referentes sin que yo hubiera abierto y leído la fuente.
- No se modificó `src/fuentes.py` ni las URLs.
- No se hicieron modelos estadísticos.
- No tomó decisiones del proyecto: las decisiones de `DECISIONES.md` son de Cristopher.
