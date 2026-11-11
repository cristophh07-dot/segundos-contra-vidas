# Guion del notebook final · *Segundos contra vidas*

> Camino narrativo del notebook final. Cada paso responde la pregunta que deja el anterior.
> **Estado (10 nov 2026):** construido en `notebooks/segundos_contra_vidas.ipynb`. Cambios frente a este guion al construirlo:
> - Sin emojis: las cajas se llaman "Cómo lo sabemos".
> - El **cierre es la propuesta**: tabla por vía, tarjetas de lo que se evita (vidas e incidentes graves), qué proponemos en concreto y limitaciones. La recomendación (antes paso 12) pasa al final; "medir" queda como paso 12 y la madrugada como paso 13.
> - Paso 5: se compara 2015 contra 2019 (los peatones bajan, los motociclistas casi no cambian); 2020 es pandemia y 2021 llega hasta septiembre.
> - Paso 6: "Lote o predio" sale de la gráfica porque no es un diseño de vía.
> - Paso 2: el mapa va sobre un fondo de calles de Medellín.

## La idea central
En Medellín no hay una sola víctima, hay dos: **el peatón y el motociclista**. Y el mundo ya probó una solución para cada una:
**Bogotá bajó la velocidad** (protege a los más vulnerables) y **Malasia separó a las motos** (ataca el volumen).

**La historia en una frase:** cada año muere más gente en las vías de Medellín, casi siempre peatones y motociclistas. En las 3 vías rápidas, separar a las motos y bajar la velocidad donde se pasa de 50 evitaría una de cada cuatro muertes, y a cada conductor le costaría segundos.

## Reglas de estilo
- Cada paso abre con **una frase en negrita: el mensaje**. Luego **una gráfica** (o dos, si el paso necesita mostrar dos cosas distintas), cuyo título es el mensaje, y 2 o 3 frases con cifras redondas.
- **Poco texto:** si una idea necesita más de 3 frases, va a un plegable. Ninguna caja pasa de 3 líneas.
- El código ocupa una línea por celda; lo pesado vive en `src/`.
- **Lo técnico se ve, explicado en simple.** Cada paso lleva una caja corta **"Cómo lo sabemos"** (2 o 3 líneas visibles): qué método usamos, dicho en palabras, y cómo comprobamos que funciona. El detalle (fórmulas, tablas completas) va en un bloque plegable y en los anexos (notebooks 01 a 06).
- La idea que guía todo: **cada resultado de la historia sale de un análisis concreto**, y el lector puede ver cuál.
- **Sin personajes ilustrativos:** los perfiles se describen tal como son en los datos.
- Cada cifra dice de dónde sale. Lo que sale de un modelo se marca como tal.

---

## Portada
- **Título:** *Segundos contra vidas*.
- **Subtítulo:** *Lo que Medellín puede aprender de Bogotá y Malasia*.
- **La pregunta**, en una línea: *¿en qué vías de Medellín salvaría más vidas bajar la velocidad o separar a las motos, y cuántos segundos le costaría a cada conductor?*
- Equipo, categoría y una línea de cómo correrlo (detalle en un plegable).

---

## Parte 0 · Con qué datos trabajamos
**Mensaje:** *Siete fuentes públicas que no se pueden unir entre sí. Para responder la pregunta, primero tuvimos que conectarlas.*

### 0.1 · Las siete fuentes y para qué usamos cada una
| Fuente | Quién la publica | Periodo | Qué trae | Para qué la usamos | Dónde aparece |
|---|---|---|---|---|---|
| **Base de incidentes del ITM** | Arango, Quiceno y Correa (2026), Mendeley Data | 2008 – ago 2025 | 702.540 incidentes, con hora, gravedad y coordenadas | **Incidentes graves** por corredor y hora: el exponente, la predicción y la base de incidentes del Monte Carlo (D3, D8) | Pasos 2, 8, 10, 11 |
| **Víctimas en incidentes viales** | MEData · Secretaría de Movilidad | 2014 – sep 2021 | 235.843 víctimas, con actor, edad, sexo y gravedad | **Quién muere:** el modelo logístico y el % de víctimas en moto por corredor (D12, D16) | Pasos 1, 3, 4, 5, 11 |
| **Mortalidad (Observatorio de Movilidad)** | Alcaldía de Medellín · Distrito | 2019 – 2024 | 1.541 fallecidos con coordenadas | **Cuántos mueren** y dónde: la cifra oficial y la base de las vidas salvadas (D13, D17) | Pasos 1, 2, 10, 11, 14 |
| **Incidentes viales con motos** | MEData | 2015 – 2021 | Una fila por vehículo | **El peso de la moto** y la letalidad según el diseño de la vía (D14) | Pasos 3, 6 |
| **Velocidad y tiempo de viaje (Google Traffic)** | MEData · SIMM | 2017 – 2020, de 6 a 20 h | Velocidad media de cada tramo, hora por hora | **Dónde se pasa de 50 de día** y cuántos segundos costaría el tope (D29) | Pasos 7, 8, 11 |
| **Velocidad e intensidad vehicular (SIMM)** | MEData · SIMM | jul – ago 2020, 24 horas | Velocidad y volumen por carril en 303 sensores | **La velocidad de noche** (D21, D34, D36) y el trazado de los corredores (D27) | Pasos 7, 11, 14 |
| **Incidentes viales** | MEData | 2014 – 2020 | Incidentes por clase y gravedad | **Respaldo y control:** comparar con la base del ITM (D3) | Anexo 01 |

- **Evidencia externa** (no son datos de Medellín, son el punto de comparación), todo verificado en la fuente (`docs/referentes.md`, D31): Bogotá (límite de 50 km/h, 2018), Malasia (carril de motos, 1995), Elvik (2009) y Nilsson (relación velocidad–siniestros), FHWA (límite variable).
- **Gráfica:** una línea de tiempo 2008–2025 con la barra de cada fuente (la misma idea del paso 13, aquí para presentar los datos).

### 0.2 · El problema: las fuentes no hablan entre sí
- Ninguna fuente comparte un identificador con otra, y los tramos de velocidad no traen coordenadas (algunos terminan en sitios como "Tugo" o "CTI").
- **Lo que hicimos:** construimos nuestra propia **geometría de los 12 corredores** con los sensores del SIMM, cortada a los tramos de Google Traffic, y asignamos cada incidente, víctima y muerto al corredor que queda a menos de 50 m (D27, D30). Así, por primera vez, la velocidad y los siniestros de un mismo corredor se pueden comparar.
- **Cómo sabemos que funciona:** 55.832 incidentes graves quedan en algún corredor; en 10 de los 11 corredores con número propio, entre el 64% y el 94% de esos incidentes nombran su vía en la dirección. El resultado casi no cambia con 30 o con 100 m.
- **Gráfica:** un diagrama: las 7 fuentes → limpieza → unión por corredor → los 6 análisis.

### 0.3 · Lo que encontramos al revisar los datos (y cómo lo resolvimos)
| Lo que encontramos | Qué habría pasado si no lo corregíamos | Qué hicimos |
|---|---|---|
| El archivo de víctimas tiene 1.048.317 filas, pero 812.474 están vacías | Contar 4 veces más víctimas | Filtrar las filas reales (D12) |
| La base del ITM registra entre el 52% y el 91% de los muertos oficiales, según el año | Un falso "pico" de muertes en 2022 | Contar los muertos con la cifra del Distrito (D13) |
| Desde 2023 casi no se registran los choques de solo daños | Una falsa caída de los incidentes | Usar solo incidentes graves (D8) |
| En 2024 los incidentes con coordenadas bajan de 94% a 86% | Una falsa caída de 22% en los corredores | Corregir por la cobertura de cada mes (D32) |
| La base de motos tiene una fila por vehículo | Contar dos veces el mismo choque | Quitar los radicados repetidos (D14) |
| Direcciones de relleno ("Calle 999", "N/D") | Incidentes ubicados en lugares falsos | Tratarlas como faltantes (D10) |

- **Reproducible:** el notebook descarga cada fuente desde su URL oficial y verifica el archivo; nadie tiene que bajar nada a mano.

### 0.4 · Por qué contamos incidentes graves (heridos y muertos)
- **Mensaje:** *Desde 2023 casi no se registran los choques de solo daños. Si los contáramos, parecería que Medellín mejoró, y no es así.*
- **Gráfica:** incidentes por año en la base del ITM, en dos colores: solo daños y graves (heridos y muertos). Los de solo daños se desploman en 2023; los graves siguen su curva.
- **Texto:**
  - La caída de los solo daños es un cambio en cómo se registran, no menos choques (D8).
  - Los graves se registran igual todos los años, y son los que importan: en ellos hay alguien herido o muerto.
  - Y son muchos más que los muertos (unos 120 por cada muerto), así que dan resultados firmes donde los muertos solos serían muy pocos.
- **Cómo lo sabemos:** de 702.540 incidentes del ITM, 403.135 son graves; comparamos su evolución año por año con la de los solo daños.
- → *Con los datos unidos y limpios, ¿qué preguntas respondimos?*

---

## El camino del análisis
**Mensaje:** *Seis análisis, cada uno responde una pregunta y le pasa su resultado al siguiente.*

| # | Pregunta | Qué hicimos (en palabras) | Resultado que pasa a la historia | Anexo |
|---|---|---|---|---|
| 1 | ¿Qué dicen y qué no dicen los datos? | Revisamos, limpiamos y unimos las 7 fuentes por corredor | 294 de 1.541 muertos en 12 corredores; 3 de ellos concentran la mitad | 01 |
| 2 | ¿Quién muere y por qué? | Comparamos víctimas parecidas que solo se diferencian en una cosa (regresión logística, validada) | Ser peatón multiplica el riesgo por 3,4; tener 60+, por 5,7 | 02 |
| 3 | ¿Cuánto pesa la velocidad en Medellín? | Comparamos el mismo corredor en horas más rápidas y más lentas (binomial negativa, bootstrap) | La evidencia directa es débil: simulamos con un rango | 03 |
| 4 | ¿Lo confirma un experimento real? | Usamos la cuarentena, cuando la ciudad fue 30% más rápida, y la comparamos con 5 años normales | Va en la dirección esperada, pero no es prueba | 04 |
| 5 | ¿Qué pasa si no hacemos nada? | Predijimos 2023–2025 sin mostrarle esos años al modelo, y comparamos 4 modelos | Unos 10 incidentes graves al día en 12 vías | 05 |
| 6 | ¿Cuántas vidas, a qué costo? | Repetimos el cálculo 10.000 veces con todo lo que no sabemos con exactitud (Monte Carlo) | 5,7 vidas al año con las dos medidas; 57 s por viaje en la Regional | 06 |

- **Gráfica:** el mismo camino como un diagrama de seis cajas, con la flecha de lo que cada una le pasa a la siguiente.
- **Frase de cierre:** *"Lo que sigue es la historia que cuentan estos seis análisis juntos."*

---

## Apertura · La respuesta corta
- **La respuesta corta** (de la tabla del paso 12; el jurado lee primero la conclusión y después la historia que la sostiene):
  - **3 vías** (Regional, Autopista Sur y Autopista Norte) concentran casi la mitad de los muertos de los 12 corredores principales.
  - **5,7 vidas al año** (entre 4,4 y 7,1) y **372 incidentes graves** menos si se aplican las dos medidas: una de cada cuatro muertes de esas vías.
  - **57 segundos por viaje** es lo que cuesta el tope de 50 km/h en la Regional, la vía donde más rinde. El carril de motos no cuesta segundos.

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
- **Cómo lo sabemos:** unimos dos fuentes oficiales: las víctimas de MEData hasta 2018 y el Distrito desde 2019. En 2019, el año en que se cruzan, coinciden (247 y 251), así que la serie se puede leer como una sola.
- **Una línea:** *"Contamos los muertos con la cifra oficial; las fuentes y lo que corregimos están en la Parte 0. Al final proponemos cómo mejorar estos datos (paso 13)."*
- → *¿Las muertes caen al azar, o tienen un patrón?*

### Paso 2 · No es mala suerte: es un patrón
- **Mensaje:** *Las muertes no están repartidas al azar: se concentran en pocos lugares, a ciertas horas y en ciertas personas. Y lo que tiene patrón se puede prevenir.*
- **Cómo lo sabemos:** cada muerto del Distrito tiene coordenadas; lo asignamos al corredor que queda a menos de 50 m de nuestra geometría (Parte 0.2).
- **Gráfica:** el mapa de muertos 2019–2024 con los 12 corredores superpuestos (Josué, `figuras/08_mapa_12_corredores.png`). El 10% de las zonas con más muertes concentra el 39% de los fallecidos, y **294 de los 1.541 muertos (19%) ocurren en solo 12 corredores**; tres de ellos concentran casi la mitad (D30).
- **Texto:** tres pistas, y cada una anuncia un acto:
  - **Dónde:** pocas zonas y pocos corredores concentran gran parte de las muertes → Acto III.
  - **Quiénes:** 9 de cada 10 muertos son peatones o motociclistas → Acto II.
  - **Cuándo:** en los corredores, la mitad de los muertos es de noche, aunque de noche ocurre solo uno de cada cuatro incidentes graves → Cierre.
- → *¿Quiénes son esos 313?*

---

## Acto II · Quién muere y por qué

### Paso 3 · Los 313 tienen dos caras
- **Mensaje:** *9 de cada 10 muertos son peatones o motociclistas, casi mitad y mitad. Pero no mueren por la misma razón.*
- **Gráfica 1 · quiénes mueren:** los muertos por actor como una sola barra dividida: peatones y motociclistas suman 9 de cada 10.
- **Gráfica 2 · por qué mueren:** la de Josué (`diagnostico.fig_actor`): *"el 76% de las víctimas iba en moto, pero el más letal es el peatón"*. A la izquierda, víctimas por actor; a la derecha, muertos por cada 100.
- **Texto:**
  - **La moto pesa por volumen:** 3 de cada 4 víctimas, y aparece en 8 de cada 10 incidentes graves (84–86%).
  - **El peatón pesa por gravedad:** de cada 100 peatones víctimas mueren 2,75; de cada 100 motociclistas, 0,5 (5,5 veces más).
  - Son dos problemas distintos mezclados en una misma cifra.
- **Cómo lo sabemos:** cada una de las 235.843 víctimas trae su condición (peatón, motociclista, parrillero, ciclista, conductor o pasajero de carro). La presencia de la moto en los incidentes graves sale de una fuente distinta, la base de motos, contando cada choque una sola vez (D14).
- → *¿Por qué el peatón muere tanto más?*

### Paso 4 · El mismo choque no pesa igual para todos
- **Mensaje:** *Un motociclista de 20 a 29 años que choca de día muere 1 de cada 331 veces. Un peatón de 60 años o más atropellado de madrugada muere 1 de cada 7.*
- **Gráfica:** barras horizontales con la etiqueta "1 de cada N": Moto · 20–29 · de día (331); Moto · 20–29 · madrugada (104); Ciclista · 30–44 · de día (91); Peatón · 30–44 · de día (75); Peatón · 60+ · de día (18); Peatón · 60+ · madrugada (7). Función: `modelos.probabilidad_perfiles()`.
- **Texto:**
  - Sin carrocería, el cuerpo recibe todo el impacto. A igual edad y hora, ser peatón multiplica por 3,4 el riesgo de morir; tener 60 años o más, por 5,7.
  - Los factores se suman: el riesgo cambia unas 50 veces según quién recibe el choque.
  - El modelo, en una frase: *"comparamos víctimas parecidas que solo se diferencian en una cosa"*.
- **Precisión:** el "1 de cada 7" es el dato real (33 de 236 peatones de 60+ de madrugada, hombres y mujeres juntos). El "1 de cada 331" sale del modelo y se marca así.
- **Cómo lo sabemos:** una regresión logística con actor, edad, sexo, hora, día y año, entrenada hasta 2019. **La probamos con 2020–2021, años que no vio:** predijo 353 muertos y hubo 357 (AUC 0,76).
- **Nota técnica (plegable):** la tabla completa de odds ratios, la calibración y los errores agrupados por incidente (D22).
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
  - **Cómo lo sabemos:** la base de motos trae el diseño de la vía de cada choque; contamos cada choque una sola vez (D14). Es evidencia independiente: esa base no tiene ningún dato de velocidad.
- → *¿Entonces hay que bajar la velocidad en toda la ciudad?*

### Paso 7 · Medellín tiene dos velocidades
- **Mensaje:** *En 9 de los 12 corredores principales la congestión ya obliga a ir despacio. Solo en 3 vías rápidas se pasa de 50 km/h, y no solo de día.*
- **Gráfica:** la del notebook 03, sección 5.2: % de los registros sobre 50 km/h hora por hora en las 3 vías, y los segundos que costaría el tope en cada una.
- **Texto:**
  - De día, la Regional pasa de 50 en el 68% de los registros, la Autopista Sur en el 37% y la Autopista Norte en el 21% (Google Traffic 2017–2019). En las otras 9 vías, incluida Las Palmas, casi nadie pasa de 50.
  - **De noche el exceso no se apaga:** entre las 0 y las 4 a. m. sigue pasando de 50 entre el 15% y el 28% del tráfico de esas vías (SIMM). La velocidad de noche es la misma que de día (D34).
  - Un tope como el de Bogotá solo cambia algo donde de verdad se va rápido. En la congestión no cuesta nada: un tope fijo ya se comporta como uno que cambia con la hora.
- **Cómo lo sabemos:** aplicamos el tope registro por registro a 39.584 mediciones de Google Traffic (no al promedio, que esconde las horas rápidas). La noche sale del SIMM, usando solo cuánto cambia frente al día, porque las dos fuentes miden distinto (D36).
- **Decisión (recuadro):** el tope se evalúa en la Regional, la Autopista Sur y la Autopista Norte, a cualquier hora (D29, D35).
- → *¿Y cuánto más choque hay cuando se va más rápido?*

### Paso 8 · Primera vez: más velocidad, más choques
- **Mensaje:** *En Medellín, la evidencia directa es débil: según cómo se mida, el efecto de la velocidad va de nada a la mitad de lo que dice la literatura. Por eso no apostamos a un solo número: simulamos con un rango.*
- **Gráfica:** el exponente de Medellín con su intervalo (bootstrap por corredor), junto al de la literatura: Elvik 2009 para vías urbanas (1,5 para incidentes graves) y Nilsson clásico (2).
- **Texto:** sin la palabra "exponente" hasta el final: *"comparamos el mismo corredor en horas más rápidas y más lentas"*.
  - Sin tener en cuenta la hora, +10% de velocidad trae unos +5% de incidentes graves (0,52; entre 0,09 y 0,99). Según Nilsson serían +21%.
  - Teniendo en cuenta la hora, el efecto desaparece (−0,27; entre −0,63 y 0,25): dentro de un corredor, la velocidad cambia sobre todo por la congestión, y estos datos no pueden separar las dos cosas.
  - El resultado no depende del radio de asignación ni de ningún corredor.
- **Cómo lo sabemos:** un modelo de conteo (binomial negativa) sobre 8.791 incidentes graves, con el volumen de tráfico como exposición. Lo pusimos a prueba de tres formas: repitiéndolo 500 veces con corredores sorteados (bootstrap), quitando un corredor a la vez y cambiando el radio de 30 a 100 m.
- **Nota técnica (plegable):** los cinco modelos (A a E) y por qué el resultado cambia al controlar la hora (notebook 03).
- → *¿Y cada choque, mata más cuando se va más rápido?*

### Paso 9 · Segunda vez: la ciudad hizo el experimento
- **Mensaje:** *En la cuarentena Medellín fue un 30% más rápida. La proporción de víctimas que murió subió 19%, menos de lo que predice la literatura y sin distinguirse de un año normal. Solo en los peatones el efecto se parece al de la literatura.*
- **Gráfica:** la del notebook 04: placebos 2015–2019 en gris, cuarentena en rojo, línea en 1.
- **Texto:**
  - Con calles vacías, las vías rápidas pasaron de unos 45 a 58 km/h.
  - Comparando con víctimas del mismo perfil, murieron 70 donde se esperaban 59. Pero en años normales ya se vio una diferencia así (2015).
  - La literatura predecía +70%. Solo en los peatones el resultado es compatible con ella: la velocidad pesa más sobre los más vulnerables (Acto II).
  - **El total de muertos cayó 40% porque hubo menos viajes:** cuánta gente está expuesta pesa tanto como la velocidad. Es el puente hacia el carril de motos.
- **Cómo lo sabemos:** con el modelo logístico calculamos cuántos muertos se esperaban en la cuarentena según el perfil de las víctimas, y los comparamos con los que hubo. Hicimos la misma prueba en 5 años normales ("placebos") para ver si la diferencia era rara.
- **Por qué da credibilidad:** pusimos a prueba nuestra propia hipótesis y la contamos tal como salió.
  - El efecto implícito de la velocidad sobre la letalidad (0,64) es compatible con el de la literatura urbana (≈ 1,1).
- **Decisión (recuadro):** no se copia el número de la literatura. Las vidas salvadas se calculan con un rango que va desde nuestros datos hasta la literatura para vías urbanas (Elvik 2009), con Nilsson como techo (D26, D31, D37).
- → *Con todo esto, ¿cuántas vidas se salvarían, y a qué costo?*

---

## Acto IV · Lo que proponemos

### Paso 10 · No actuar también es una decisión
- **Mensaje:** *Si nada cambia, los 12 corredores principales seguirán teniendo unos 10 incidentes graves al día. Los corredores peligrosos lo siguen siendo año tras año.*
- **Gráfica:** la del notebook 05, sección 4.3: incidentes graves por mes en las 3 vías rápidas, observado contra predicho, con el tramo 2023–2025 que el modelo no vio.
- **Texto:**
  - Entre septiembre de 2025 y agosto de 2026 habría entre **3.455 y 3.732 incidentes graves** en los 12 corredores (D33). La Autopista Norte, con 700 a 835 al año, duplica a cualquier otro.
  - En las 3 vías rápidas mueren unas **24 personas al año** y hay unos **1.419 incidentes graves** (Distrito e ITM, 2019–2024). Esa es la línea base de las vidas salvadas.
  - *"Probamos el modelo con 2023–2025 sin mostrarle esos años."* Ganó el modelo más simple: la binomial negativa superó a XGBoost (desviación 2,36 frente a 4,33), aunque solo por poco a "repetir el año pasado" (2,48).
  - El modelo sobrestimó 2023–2025 en un 10%, sobre todo en las autopistas. Parte de la explicación es el registro: en 2024 se perdieron coordenadas sin aviso (paso 13).
- **Cómo lo sabemos:** pusimos a competir 4 modelos (dos que repiten el pasado, una binomial negativa y XGBoost), entrenados hasta 2022 y probados en 2023–2025. La regla para elegir se fijó antes de ver los resultados.
- **Nota técnica (plegable):** variables, desviación de Poisson y corrección por cobertura (D32).
- → *¿Cuánto cambiaría eso con las medidas de Bogotá y Malasia?*

### Paso 11 · Segundos contra vidas *(la gráfica central del proyecto)*
- **Mensaje:** *Un carril de motos en las 3 vías rápidas salvaría unas 4 vidas al año sin costar segundos. Un tope de 50 km/h en la Regional salvaría 1 vida al año por 57 segundos por viaje. Juntas, las dos medidas evitarían una de cada cuatro muertes.*
- **Gráfica:** la del notebook 06, sección 5: por cada vía, lo que evita cada medida al año (punto = mediana, línea = intervalo de 90%), en muertes y en incidentes graves, con los segundos por viaje en la etiqueta de cada vía.
- **Texto:**
  - **Cómo lo sabemos:** repetimos el cálculo 10.000 veces. En cada vuelta sorteamos lo que no sabemos con exactitud (cuánto pesa la velocidad, cuántos cumplen el tope, cuánto reduce el carril, cuántos muertos hay en un año), y nos quedamos con el rango.
  - **Tope de 50 con control permanente:** 1,6 vidas al año en las 3 vías (entre 0,6 y 2,6) y 37 incidentes graves. Casi todo en la Regional (1 vida, el 16% de sus muertes, por 57 s de día y 48 s de noche). En la Autopista Norte casi no cambia nada (0,2 vidas, 4 s): allí poca gente pasa de 50.
  - **Carril de motos:** 4,4 vidas al año (entre 3,5 y 5,5) y 344 incidentes graves. Donde más rinde es la Autopista Norte (1,8 vidas y 197 incidentes graves), justo donde el tope no sirve.
  - **Las dos juntas:** 5,7 vidas al año (entre 4,4 y 7,1) y 372 incidentes graves.
  - **El orden no depende del supuesto más dudoso:** el carril salva más que el tope incluso en el mejor caso para el tope (Nilsson: 3,3 vidas al año).
  - **Prueba de sensatez:** en la Regional, el −22% a −37% de Bogotá cae en la parte alta de nuestro rango (6% a 25%; 33% con Nilsson).
- **Cuidado (recuadro):** el intervalo del carril es estrecho porque el rango de Malasia lo es, no porque el resultado sea seguro. Descansa en un solo estudio de 1995, sin grupo de control.
- **El carril no cuesta segundos:** su costo es de espacio e infraestructura, que no se puede medir con estos datos.
- **Nota técnica (plegable):** entradas del Monte Carlo (D35–D38): exponente entre el piso de Medellín y Elvik urbano, letalidad entre 0 y 2, velocidad registro por registro, factor de noche del SIMM, cumplimiento del 85% al 100%, muertos del Distrito y graves del ITM por vía, % en moto con su incertidumbre, y Malasia entre 25% y 34%.
- → *Entonces, ¿por dónde empezar?*

### Paso 12 · La recomendación
- **Mensaje:** *Dos problemas, dos medidas: la Regional tiene un problema de velocidad; las autopistas, un problema de motos.*
- **Tabla** (la misma que alimenta la "respuesta corta" del inicio):

| Orden | Dónde | Medida principal | Las dos medidas: vidas por año (rango 90%) | Incidentes graves por año | Costo en tiempo |
|---|---|---|---|---|---|
| 1 | Regional | Tope de 50 km/h con control permanente (problema de velocidad) | 2,3 (1,5 – 3,2) | 84 | 57 s por viaje |
| 2 | Autopista Norte | Carril exclusivo de motos (problema de motos) | 2,0 (1,5 – 2,7) | 203 | 4 s por viaje |
| 3 | Autopista Sur | Carril exclusivo de motos | 1,3 (0,9 – 1,9) | 86 | 16 s por viaje |
| | **Las 3 vías** | **Tope + carril** | **5,7 (4,4 – 7,1)** | **372** | |

- En cada vía se aplican las dos medidas; la "medida principal" es la que más pesa allí. El carril, además, cuesta espacio vial (no se mide en segundos).
- **Texto:**
  - **El tope va con control permanente** (cámaras o puestos de control con multas, como en Bogotá en 2018). Sin control, el efecto sería mucho menor (D38).
  - **A quién protege cada medida:** el tope protege sobre todo a los más vulnerables (peatón ×3,4, ciclista ×2,8, 60+ ×5,7; D23). El carril protege por volumen: en las 3 vías, más del 80% de las víctimas va en moto.
  - **Lo que no recomendamos:** un tope de 50 en las arterias, porque allí la congestión ya hace el trabajo. En la Autopista Norte el tope suma poco (0,2 vidas al año), aunque cuesta solo 4 s: lo que cambia esa vía es el carril.
  - **Paso siguiente:** un límite variable con avisos, que en autopistas de Estados Unidos redujo los choques entre 29% y 34% (FHWA).
- **Límites, en una línea cada uno:** cumplimiento supuesto del 85% al 100%; el carril descansa en un solo estudio; los segundos son por viaje, no horas totales de la ciudad; los periodos de las fuentes no coinciden.

### Paso 13 · Para saber si funciona, hay que poder medirlo
- **Mensaje:** *Bogotá supo que su medida salvó vidas porque midió antes y después. Con los datos abiertos de hoy, Medellín no podría hacerlo.*
- **Gráfica nueva:** línea de tiempo 2014–2025 con los años que cubre cada base de MEData (víctimas 2014 – sep 2021; motos 2015–2021; Google Traffic 2017–2020, solo 6–20 h; SIMM solo jul–ago 2020; conteo solo ene 2021). Sombreado 2022–2024, cuando más suben las muertes: justo cuando el problema crece, los datos se acaban.
- **Cinco mejoras:**

| Mejora | Qué encontramos | Qué permitiría |
|---|---|---|
| **Series de velocidad y volumen continuas, las 24 horas** | La velocidad se publica en pedazos: 2017–2020 solo de día, y la de 24 horas son dos meses de pandemia | Medir la velocidad antes y después de un tope de 50 |
| **Contar las motos aparte** | En el SIMM, carros y motos vienen juntos en la misma categoría | Saber cuántas motos usan cada corredor, que es lo que justifica un carril |
| **Mantener actualizado el archivo de víctimas** | Termina en septiembre de 2021, justo antes de que las muertes suban | Saber quién muere hoy |
| **Un identificador común y la ubicación de cada tramo** | Las bases no se pueden unir entre sí; los tramos de Google Traffic no traen coordenadas (algunos terminan en sitios como "Tugo" o "CTI") | Seguir un mismo corredor en todas las fuentes |
| **Avisar cuando cambia el registro** | En 2024 los incidentes con coordenadas bajaron de 94% a 86% sin aviso, y eso fabricaba una caída de 22% en los corredores (D32) | Que una caída en los datos no se confunda con una mejora en las vías |

- **Bloque plegable:** la lista completa de problemas encontrados y su propuesta: 812 mil filas vacías de la exportación a Excel; codificación dañada; una fila por vehículo en la base de motos sin documentar; direcciones de relleno ("999", "N/D"); los solo daños que desaparecen desde 2023 sin explicación. Propuestas como CSV en UTF-8 y un diccionario de datos.
- **Tono:** propuesta constructiva para la Secretaría de Movilidad: *"MEData hizo posible este análisis; con estos cambios, haría posible evaluarlo."*

---

## Cierre · Lo que la velocidad no resuelve

### Paso 14 · La madrugada
- **Mensaje:** *De noche no se va más rápido, pero cada choque mata entre 2 y 4,5 veces más.*
- **Gráfica:** en los 12 corredores, % de los incidentes graves contra % de los muertos, de día y de noche (notebook 06, 1.1 y 1.3).
- **Texto:**
  - De noche ocurre el 24% de los incidentes graves de los corredores, pero el 49% de los muertos.
  - La velocidad no explica la diferencia: de noche es la misma que de día (p85 noche/día de 0,98; D34). La madrugada triplica el riesgo de morir aun comparando víctimas del mismo perfil (×3,2, modelo logístico).
  - El tope sí ayuda de noche, porque el exceso sobre 50 no se apaga. Pero la mayor parte de ese riesgo pide otras medidas: control de alcohol, iluminación y respuesta médica (D20).
  - Reconocerlo hace la propuesta más honesta.

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
| 0.1 | Línea de tiempo de las 7 fuentes | `src/fuentes.py` | Por hacer |
| 0.2 | Diagrama: fuentes → limpieza → unión por corredor → análisis | — | Por hacer |
| 0.4 | Incidentes por año: solo daños contra graves | `seguridad.incidentes_limpios()` | Por hacer |
| Camino | Diagrama de los 6 análisis | — | Por hacer |
| 1 | Muertes 2014–2024, serie oficial con anotaciones | `seguridad.victimas_limpias()` + `seguridad.mortalidad_distrito()` | Por hacer |
| 1 (plegable) | Muertos reales contra registrados, barras 2019–2024 con % de cobertura | `seguridad.mortalidad_distrito()` + `seguridad.limpiar_itm()` | Por hacer |
| 2 | Mapa con los 12 corredores | `figuras/08_mapa_12_corredores.png` (Josué) | ✅ Existe |
| 3 (1) | Muertos por actor: peatones y motociclistas, 9 de cada 10 | `seguridad.victimas_limpias()` | Por hacer |
| 3 (2) | Víctimas y letalidad por actor | `diagnostico.fig_actor` | ✅ Existe |
| 4 | Perfiles "1 de cada N" | `modelos.probabilidad_perfiles()` | Por pasar a `src/` (existe en el notebook 02) |
| 5 | Muertos por año, peatón contra moto | `seguridad.victimas_limpias()` | Por hacer |
| 6 | Letalidad por diseño de vía | base de motos | Por pasar a `src/` (existe en el notebook 01) |
| 7 | Dos velocidades: % sobre 50 por hora y segundos | notebook 03, sección 5.2 | Por pasar a `src/` |
| 8 | Exponente de Medellín frente a la literatura | notebook 03 | Por hacer |
| 9 | O/E de la cuarentena y placebos | `modelos.backtest()` | Por pasar a `src/` (existe en el notebook 04) |
| 10 | Observado contra predicho, 3 vías rápidas | notebook 05, sección 4.3 | Por pasar a `src/` |
| 11 | Segundos contra vidas | notebook 06, sección 5 | Por pasar a `src/` |
| 13 | Línea de tiempo de cobertura de MEData | `src/fuentes.py` | Por hacer |
| 14 | Incidentes graves contra muertos, día y noche | notebook 06, 1.1 y 1.3 | Por hacer |

## Cambios frente al plan original
- El backtest pasa del final al Acto III (paso 9): la cuarentena es un experimento sobre la velocidad.
- "Quién muere" va antes que "dónde" y que la velocidad: es lo que justifica las dos medidas.
- La comparación entre fuentes sale de la historia y pasa a un bloque plegable; el paso 2 cuenta el patrón de las muertes.
- El Acto II se abre en tres pasos (dos caras, el mismo choque no pesa igual, la moto no baja).
- El Acto III se ordena con la idea de que la velocidad actúa dos veces.
- Se agrega el paso 13 (mejoras a MEData), ligado a la evaluación de la medida.
- El riesgo nocturno sale de las limitaciones y se convierte en el cierre.
- **Parte 0 y "el camino del análisis" van antes de la apertura:** las fuentes, cómo se unieron y qué se corrigió, porque la rúbrica pesa mucho los datos; y un mapa de los 6 análisis, para que cada resultado de la historia tenga visible de dónde sale. El bloque plegable de fuentes del paso 1 pasa a la Parte 0.
- **Cada paso lleva una caja "Cómo lo sabemos"** visible, con el método en palabras y cómo se comprobó.
- **Un paso puede tener dos gráficas** si necesita mostrar dos cosas. Se agregan la 0.4 (por qué contamos incidentes graves) y la gráfica de muertos por actor del paso 3.
- **Con los resultados (notebooks 03 a 06):** el tope se evalúa en 3 vías, no en 4 (Las Palmas no pasa de 50 de día); el paso 8 usa la versión "evidencia débil"; el paso 12 queda como "dos problemas, dos medidas"; el paso 13 suma la pérdida de coordenadas de 2024; el paso 14 ya no dice que de noche se va más rápido; sale la sensibilidad con tope de 40 km/h (D39); se suma el paso siguiente del límite variable.

## Estado por paso
| Paso | Estado | Depende de |
|---|---|---|
| Portada, Parte 0, camino del análisis | ✅ Desglosados | Línea de tiempo y diagramas por hacer |
| Apertura y 1 a 14 | ✅ Desglosados, con cifras finales | Gráficas por hacer o por pasar a `src/` |
