# Guion del notebook final · *Segundos contra vidas*

> Camino narrativo del notebook final. Cada paso responde la pregunta que deja el anterior.
> **Estado (9 nov 2026):** camino aprobado; apertura y Actos I a III desglosados; Acto IV con estructura definida, a la espera de los resultados del exponente, la predicción y el Monte Carlo.

## La idea central
En Medellín no hay una sola víctima, hay dos: **el peatón y el motociclista**. Y el mundo ya probó una solución para cada una:
**Bogotá bajó la velocidad** (protege a los más vulnerables) y **Malasia separó a las motos** (ataca el volumen).

**La historia en una frase:** cada año muere más gente en las vías de Medellín, casi siempre peatones y motociclistas. Bajar la velocidad en las vías rápidas y separar a las motos salvaría vidas, y le costaría a cada conductor unos segundos.

## Reglas de estilo
- Cada paso abre con **una frase en negrita: el mensaje**. Luego **una sola gráfica**, cuyo título es el mensaje, y 2 o 3 frases con cifras redondas.
- El código ocupa una línea por celda; lo pesado vive en `src/`.
- Lo técnico va en bloques plegables ("¿Cómo lo calculamos?") o en los anexos (notebooks 01 a 04).
- **Sin personajes ilustrativos:** los perfiles se describen tal como son en los datos.
- Cada cifra dice de dónde sale. Lo que sale de un modelo se marca como tal.

---

## Apertura
- **Título:** *Segundos contra vidas*.
- **Subtítulo:** *Lo que Medellín puede aprender de Bogotá y Malasia*.
- **La pregunta**, en una línea.
- **La respuesta corta:** tres cifras al inicio (cuántas vidas, en qué corredores, cuántos segundos). Se llena al final con la tabla del paso 12. El jurado lee primero la conclusión y después la historia que la sostiene.
- **Cómo correrlo:** en un bloque plegable.

---

## Acto I · El problema

### Paso 1 · Cada 28 horas muere alguien
- **Mensaje:** *En 2024 murieron 313 personas en las vías de Medellín, una cada 28 horas. Es la cifra más alta en al menos 11 años.*
- **Gráfica:** una línea de 2014 a 2024 con la serie oficial (víctimas de MEData hasta 2018 y el Distrito desde 2019). Anotaciones: el mínimo de 2018 (239), la pandemia de 2020 y el 313 de 2024.
- **Texto:**
  - Medellín estaba mejorando: entre 2014 y 2018 las muertes bajaron 18% (de 290 a 239).
  - Desde entonces la curva se devolvió: +31% hasta 2024, y +27% solo en los dos últimos años.
  - 2020 no cuenta como mejora: la ciudad estuvo encerrada.
  - **Los muertos son la punta del problema:** por cada persona que muere, otras 120 quedan heridas (233.894 heridos y 1.949 muertos entre 2014 y 2021; unas 30.000 víctimas al año, 80 por día).
  - Una línea sobre la fuente: *"Contamos los muertos con la cifra oficial del Distrito; la base de incidentes registra solo una parte."*
- **Nota técnica (plegable):** las dos fuentes coinciden en 2019 (247 y 251), así que se pueden unir.
- **Bloque plegable "¿De dónde salen estas cifras?":**
  - La tabla de las 7 fuentes y para qué se usa cada una.
  - Muertos registrados contra reales: la base del ITM registra entre el 52% y el 91%, según el año; solo 4 de cada 10 mueren en la vía.
  - Los problemas de calidad resueltos, con enlace al anexo 01.
  - Una línea: *"Al final proponemos cómo mejorar estos datos"* (paso 13).
  - Tono: la base del ITM es excelente para incidentes, pero no está hecha para contar muertos (D13).
- → *¿Las muertes caen al azar, o tienen un patrón?*

### Paso 2 · No es mala suerte: es un patrón
- **Mensaje:** *Las muertes no están repartidas al azar: se concentran en pocos lugares, a ciertas horas y en ciertas personas. Y lo que tiene patrón se puede prevenir.*
- **Gráfica:** el mapa de muertos 2019–2024 (Josué, `diagnostico.fig_mapa`). El 10% de las zonas con más muertes concentra el 39% de los fallecidos. **Por mejorar:** superponer los 12 corredores y agregar una referencia de ciudad.
- **Texto:** tres pistas, y cada una anuncia un acto:
  - **Dónde:** pocas zonas concentran gran parte de las muertes → Acto III.
  - **Quiénes:** 9 de cada 10 muertos son peatones o motociclistas → Acto II.
  - **Cuándo:** de madrugada, el mismo choque mata tres veces más → Cierre.
- → *¿Quiénes son esos 313?*

---

## Acto II · Quién muere y por qué

### Paso 3 · Los 313 tienen dos caras
- **Mensaje:** *9 de cada 10 muertos son peatones o motociclistas, casi mitad y mitad. Pero no mueren por la misma razón.*
- **Gráfica:** la de Josué (`diagnostico.fig_actor`): *"el 76% de las víctimas iba en moto, pero el más letal es el peatón"*. A la izquierda, víctimas por actor; a la derecha, muertos por cada 100.
- **Texto:**
  - **La moto pesa por volumen:** 3 de cada 4 víctimas, y aparece en 8 de cada 10 incidentes graves (84–86%).
  - **El peatón pesa por gravedad:** de cada 100 peatones víctimas mueren 2,75; de cada 100 motociclistas, 0,5 (5,5 veces más).
  - Son dos problemas distintos mezclados en una misma cifra.
- → *¿Por qué el peatón muere tanto más?*

### Paso 4 · El mismo choque no pesa igual para todos
- **Mensaje:** *Un motociclista de 20 a 29 años que choca de día muere 1 de cada 331 veces. Un peatón de 60 años o más atropellado de madrugada muere 1 de cada 7.*
- **Gráfica:** barras horizontales con la etiqueta "1 de cada N": Moto · 20–29 · de día (331); Moto · 20–29 · madrugada (104); Ciclista · 30–44 · de día (91); Peatón · 30–44 · de día (75); Peatón · 60+ · de día (18); Peatón · 60+ · madrugada (7). Función: `modelos.probabilidad_perfiles()`.
- **Texto:**
  - Sin carrocería, el cuerpo recibe todo el impacto. A igual edad y hora, ser peatón multiplica por 3,4 el riesgo de morir; tener 60 años o más, por 5,7.
  - Los factores se suman: el riesgo cambia unas 50 veces según quién recibe el choque.
  - El modelo, en una frase: *"comparamos víctimas parecidas que solo se diferencian en una cosa"*.
- **Precisión:** el "1 de cada 7" es el dato real (33 de 236 peatones de 60+ de madrugada, hombres y mujeres juntos). El "1 de cada 331" sale del modelo y se marca así.
- **Nota técnica (plegable):** la regresión logística, la validación (AUC 0,76; predijo 353 muertos y hubo 357) y la tabla completa de OR.
- → *Si al peatón lo protegemos mejor, ¿qué pasa con la moto?*

### Paso 5 · Medellín aprendió a proteger al peatón; con la moto, no
- **Mensaje:** *Entre 2015 y 2019 los peatones muertos bajaron 25%. Los motociclistas muertos no bajaron, y desde 2016 son tantos o más que los peatones.*
- **Gráfica nueva:** muertos por año, peatón contra moto, 2014–2021 (dos líneas que se cruzan). 2021 marcado como incompleto (hasta septiembre).
- **Texto:**
  - Para el peatón algo funcionó: de 145 a 109 muertos.
  - Para la moto, nada cambió: entre 107 y 127 muertos todos los años.
  - Es la parte del problema que la ciudad no ha logrado mover.
- **Cuidado:** no sabemos por qué bajaron los peatones muertos; no se atribuye a ninguna política.

### Cierre del Acto II · Dos problemas, dos medidas
| Problema | Por qué muere | Medida | Quién lo probó | Resultado |
|---|---|---|---|---|
| **El peatón** (y el ciclista y los mayores) | Por gravedad: el impacto llega al cuerpo sin protección | **Bajar la velocidad** | Bogotá (2018) | Muertes entre −22% y −37% en las avenidas intervenidas |
| **La moto** | Por volumen: está en 8 de cada 10 incidentes graves | **Separarla del tráfico** | Malasia (carril en la F02) | Entre 25% y 34% menos accidentes de moto |

- **Frase de cierre:** *"Medellín no tiene que inventar nada: tiene que decidir dónde aplicar lo que ya funcionó."*
- **Fuentes:** `docs/referentes.md` (verificadas, D31). Bogotá: Secretaría de Movilidad y Global Road Safety Facility; Malasia: Radin Umar, Mackay y Hills (1995).
- → *Pero, ¿cuánto pesa la velocidad en Medellín, y dónde se va rápido?*

---

## Acto III · La velocidad actúa dos veces
**Hilo del acto:** *la velocidad hace que haya más choques, y hace que cada choque mate más.* El paso 8 mide lo primero; el paso 9, lo segundo; el Monte Carlo junta los dos.

### Paso 6 · Donde se va más rápido, el choque mata más
- **Mensaje:** *Un choque en un paso elevado mata 2,6 veces más que uno en una intersección.*
- **Gráfica:** letalidad por diseño de vía: paso elevado 1,27%, puente 1,15%, tramo 0,64%, intersección 0,48%, glorieta 0,43% (base de motos, D14).
- **Texto:**
  - En un paso elevado nadie frena; en una intersección, todos. El diseño de la vía es un reflejo de la velocidad.
  - Es evidencia independiente: esa base no tiene ningún dato de velocidad.
- → *¿Entonces hay que bajar la velocidad en toda la ciudad?*

### Paso 7 · Medellín tiene dos velocidades
- **Mensaje:** *En 8 de los 12 corredores principales la congestión ya obliga a ir despacio. Solo en 4 vías rápidas se pasa de 50 km/h, y a cualquier hora.*
- **Gráfica:** velocidad media de los 12 corredores, de mayor a menor, con una línea en 50 km/h. Arriba: Regional (54), Autopistas Norte y Sur (44–48), Las Palmas (40–42). Abajo: las 8 arterias (14–35).
- **Texto:**
  - En las vías rápidas, cerca de 1 de cada 5 mediciones pasa de 50, de día y de noche.
  - En las arterias casi nadie pasa de 50.
  - Un tope como el de Bogotá solo cambia algo donde de verdad se va rápido.
- **Decisión (recuadro):** la reducción de velocidad se evalúa solo en las 4 vías rápidas (D18).
- **Pendiente:** velocidad de noche por corredor (Johan, `velocidad_nocturna_corredor()`).
- → *¿Y cuánto más choque hay cuando se va más rápido?*

### Paso 8 · Primera vez: más velocidad, más choques
- **Mensaje:** *Si la velocidad de un corredor sube 10%, los incidentes graves suben X%.* (notebook 03)
- **Gráfica:** el exponente de Medellín con su intervalo, junto al de la literatura (Elvik 2009 para vías urbanas y Nilsson clásico).
- **Texto:** sin la palabra "exponente" hasta el final: *"comparamos el mismo corredor en horas más rápidas y más lentas, con el mismo tráfico"*. Referencia: según Nilsson, +10% de velocidad trae +21% de incidentes con heridos.
- **Dos versiones del texto, según el resultado:**
  - Si sale parecido a Nilsson: *"Medellín se comporta como dice la literatura."*
  - Si sale bajo o muy incierto: *"En Medellín la evidencia directa es débil, y por eso no apostamos a un solo número: simulamos con un rango."*
- **Nota técnica (plegable):** binomial negativa, exposición, bootstrap y prueba quitando un corredor a la vez.
- ⏳ Espera la asignación a corredores (Josué) y la geometría (Johan).
- → *¿Y cada choque, mata más cuando se va más rápido?*

### Paso 9 · Segunda vez: la ciudad hizo el experimento
- **Mensaje:** *En la cuarentena Medellín fue un 31% más rápida. La proporción de víctimas que murió subió 19%, menos de lo que predice la literatura y sin distinguirse de un año normal. Solo en los peatones el efecto se parece al de la literatura.*
- **Gráfica:** la del notebook 04: placebos 2015–2019 en gris, cuarentena en rojo, línea en 1.
- **Texto:**
  - Con calles vacías, las vías rápidas pasaron de unos 45 a 58 km/h.
  - Comparando con víctimas del mismo perfil, murieron 70 donde se esperaban 59. Pero en años normales ya se vio una diferencia así (2015).
  - La literatura predecía +70%. Solo en los peatones el resultado es compatible con ella: la velocidad pesa más sobre los más vulnerables (Acto II).
  - **El total de muertos cayó 40% porque hubo menos viajes:** cuánta gente está expuesta pesa tanto como la velocidad. Es el puente hacia el carril de motos.
- **Por qué da credibilidad:** pusimos a prueba nuestra propia hipótesis y la contamos tal como salió.
- **Decisión (recuadro):** no se copia el número de la literatura; las vidas salvadas se calculan con un rango entre nuestros datos y la literatura para vías urbanas (Elvik 2009), con Nilsson como sensibilidad (D26, D28, D31).
- → *Con todo esto, ¿cuántas vidas se salvarían, y a qué costo?*

---

## Acto IV · Lo que proponemos
⏳ **Estructura definida; se llena cuando lleguen los resultados.**

### Paso 10 · No actuar también es una decisión
- **Mensaje:** *Si nada cambia, en las 4 vías rápidas habrá unos X incidentes graves y Y muertos por año.*
- **Gráfica:** incidentes graves por mes en cada vía rápida, observado contra predicho; resaltado el tramo 2023–2025, que el modelo no vio.
- **Texto:**
  - *"Probamos el modelo con 2023–2025 sin mostrarle esos años, y acertó con un error de Z%."*
  - Esta proyección es la línea base de las vidas salvadas.
- **Nota técnica (plegable):** XGBoost contra binomial negativa; se queda el más simple que funcione.
- ⏳ Predicción (corredor × mes), que espera la asignación a corredores.
- → *¿Cuánto cambiaría eso con las medidas de Bogotá y Malasia?*

### Paso 11 · Segundos contra vidas *(la gráfica central del proyecto)*
- **Mensaje:** *Bajar a 50 km/h en la [vía] salvaría entre A y B vidas por año, y a cada conductor le costaría C segundos por viaje.*
- **Gráfica:** cada punto es una vía con una medida. Eje horizontal: segundos por viaje; eje vertical: vidas salvadas por año, con su intervalo. Arriba a la izquierda (muchas vidas por pocos segundos) es lo que va primero.
- **Texto:**
  - El método, en una frase: *"repetimos el cálculo 10.000 veces con todos los valores posibles de lo que no sabemos con exactitud, y nos quedamos con el rango"*.
  - De las vidas salvadas, cuántas serían peatones y cuántas motociclistas (modelo logístico, D24).
  - **Prueba de sensatez:** comparar la reducción simulada con el −22% a −37% de Bogotá.
- **El carril de motos no cuesta segundos:** su costo es de espacio e infraestructura, que no se puede medir con estos datos. Sus puntos van marcados aparte, sin costo en tiempo.
- **Nota técnica (plegable):** entradas del Monte Carlo (exponente del paso 8, rango 0–2 del paso 9, velocidad registro por registro, muertos del Distrito por corredor, rangos de Bogotá y Malasia) y sensibilidad con tope de 40 km/h.
- ⏳ Monte Carlo. Necesita el exponente, `costo_tiempo_escenarios()` y `riesgo_motos_corredor()` (Johan), los muertos por corredor (Josué) y los referentes verificados.
- **Decisión pendiente:** en qué vías se evalúa el carril de motos: las 4 vías rápidas (como Malasia, en una autopista) o los corredores con más peso de la moto (pueden incluir arterias).
- → *Entonces, ¿por dónde empezar?*

### Paso 12 · La recomendación
- **Mensaje:** *Tres decisiones, en orden.*
- **Tabla** (la misma que alimenta la "respuesta corta" del inicio):

| Orden | Dónde | Medida | Vidas por año (rango) | Costo |
|---|---|---|---|---|
| 1 | La vía con más vidas por segundo | Tope de 50 km/h | A – B | C s por viaje |
| 2 | La vía donde más pesa la moto | Carril exclusivo | … | Espacio vial |
| 3 | … | … | … | … |

- **Texto:**
  - El orden lo deciden los datos: vidas salvadas por cada segundo de costo, y dónde hay más peatones, mayores y motos. El 10% de las víctimas de mayor riesgo concentra el 43% de los muertos: focalizar rinde.
  - **Lo que no recomendamos:** un tope de 50 en las arterias, porque allí la congestión ya hace el trabajo.
- ⏳ Depende de los pasos 10 y 11.

### Paso 13 · Para saber si funciona, hay que poder medirlo
- **Mensaje:** *Bogotá supo que su medida salvó vidas porque midió antes y después. Con los datos abiertos de hoy, Medellín no podría hacerlo.*
- **Gráfica nueva:** línea de tiempo 2014–2025 con los años que cubre cada base de MEData (víctimas 2014 – sep 2021; motos 2015–2021; Google Traffic 2017–2020, solo 6–20 h; SIMM solo jul–ago 2020; conteo solo ene 2021). Sombreado 2022–2024, cuando más suben las muertes: justo cuando el problema crece, los datos se acaban.
- **Cuatro mejoras:**

| Mejora | Qué encontramos | Qué permitiría |
|---|---|---|
| **Series de velocidad y volumen continuas, las 24 horas** | La velocidad se publica en pedazos: 2017–2020 solo de día, y la de 24 horas son dos meses de pandemia | Medir la velocidad antes y después de un tope de 50 |
| **Contar las motos aparte** | En el SIMM, carros y motos vienen juntos en la misma categoría | Saber cuántas motos usan cada corredor, que es lo que justifica un carril |
| **Mantener actualizado el archivo de víctimas** | Termina en septiembre de 2021, justo antes de que las muertes suban | Saber quién muere hoy |
| **Un identificador común y la ubicación de cada tramo** | Las bases no se pueden unir entre sí; los tramos de Google Traffic no traen coordenadas (algunos terminan en sitios como "Tugo" o "CTI") | Seguir un mismo corredor en todas las fuentes |

- **Bloque plegable:** la lista completa de problemas encontrados y su propuesta: 812 mil filas vacías de la exportación a Excel; codificación dañada; una fila por vehículo en la base de motos sin documentar; direcciones de relleno ("999", "N/D"); los solo daños que desaparecen desde 2023 sin explicación. Propuestas como CSV en UTF-8 y un diccionario de datos.
- **Tono:** propuesta constructiva para la Secretaría de Movilidad: *"MEData hizo posible este análisis; con estos cambios, haría posible evaluarlo."*

---

## Cierre · Lo que la velocidad no resuelve

### Paso 14 · La madrugada
- La madrugada triplica el riesgo de morir (×3,2, ajustado), pero allí la velocidad apenas sube 4%.
- Ese riesgo pide otras medidas: control de alcohol, iluminación, respuesta médica (D20).
- Reconocerlo hace la propuesta más honesta.
- ⏳ Por desglosar.

### Después
- Limitaciones, fuentes y uso de IA.

---

## Lo que queda fuera de la historia (va a los anexos)
- El pico de 2022 de la base del ITM: era un artefacto del registro.
- La clase de incidente: casi repite al actor.
- La tabla completa de odds ratios: en la historia van los perfiles.
- Las tablas de limpieza de datos (resumidas en el plegable del paso 1 y en el paso 13).
- Las cifras brutas de la cuarentena (+31% moto, +37% peatón): exageraban el efecto.

## Gráficas por hacer
| Paso | Gráfica | Fuente | Estado |
|---|---|---|---|
| 1 | Muertes 2014–2024, serie oficial con anotaciones | `seguridad.victimas_limpias()` + `seguridad.mortalidad_distrito()` | Por hacer |
| 1 (plegable) | Muertos reales contra registrados, barras 2019–2024 con % de cobertura | `seguridad.mortalidad_distrito()` + `seguridad.limpiar_itm()` | Por hacer |
| 2 | Mapa con los corredores superpuestos | `diagnostico.fig_mapa` + geometría de Johan | Mejorar |
| 3 | Víctimas y letalidad por actor | `diagnostico.fig_actor` | ✅ Existe |
| 4 | Perfiles "1 de cada N" | `modelos.probabilidad_perfiles()` | Por pasar a `src/` (existe en el notebook 02) |
| 5 | Muertos por año, peatón contra moto | `seguridad.victimas_limpias()` | Por hacer |
| 6 | Letalidad por diseño de vía | base de motos | Por pasar a `src/` (existe en el notebook 01) |
| 7 | Velocidad media de los 12 corredores con línea en 50 | `velocidad.tiempo_viaje_gt()` | Por hacer |
| 8 | Exponente frente a la literatura | notebook 03 | ⏳ |
| 9 | O/E de la cuarentena y placebos | `modelos.backtest()` | Por pasar a `src/` (existe en el notebook 04) |
| 10 | Observado contra predicho por vía rápida | predicción | ⏳ |
| 11 | Segundos contra vidas | Monte Carlo | ⏳ |
| 13 | Línea de tiempo de cobertura de MEData | `src/fuentes.py` | Por hacer |

## Cambios frente al plan original
- El backtest pasa del final al Acto III (paso 9): la cuarentena es un experimento sobre la velocidad.
- "Quién muere" va antes que "dónde" y que la velocidad: es lo que justifica las dos medidas.
- La comparación entre fuentes sale de la historia y pasa a un bloque plegable; el paso 2 cuenta el patrón de las muertes.
- El Acto II se abre en tres pasos (dos caras, el mismo choque no pesa igual, la moto no baja).
- El Acto III se ordena con la idea de que la velocidad actúa dos veces.
- Se agrega el paso 13 (mejoras a MEData), ligado a la evaluación de la medida.
- El riesgo nocturno sale de las limitaciones y se convierte en el cierre.

## Estado por paso
| Paso | Estado | Depende de |
|---|---|---|
| Apertura, 1–7, 9, 13 | ✅ Desglosados | Gráficas por hacer |
| 2 | ✅ | Mejora con la geometría de Johan |
| 8 | Estructura lista | Notebook 03 (Josué y Johan) |
| 10, 11, 12 | Estructura lista | Predicción y Monte Carlo |
| 14 | Por desglosar | — |
