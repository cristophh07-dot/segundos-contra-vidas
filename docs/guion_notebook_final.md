# Guion del notebook final · *Segundos contra vidas*

> Camino narrativo del notebook final. Cada paso responde la pregunta que deja el anterior.
> Estado: **camino aprobado** (8 nov 2026). Falta desglosar cada paso: texto, gráfica y cifra.

## La idea central
En Medellín no hay una sola víctima, hay dos: **el peatón y el motociclista**. Y el mundo ya probó una solución para cada una:
**Bogotá bajó la velocidad** (protege a los más vulnerables) y **Malasia separó a las motos** (ataca el volumen).

**La historia en una frase:** cada año muere más gente en las vías de Medellín, casi siempre peatones y motociclistas. Bajar la velocidad en las vías rápidas y separar a las motos salvaría vidas, y le costaría a cada conductor unos segundos.

---

## Acto I · El problema que no se ve

### 1. Cada vez muere más gente
- 247 muertos en 2022, 277 en 2023, **313 en 2024**: casi uno por día, +27% en dos años.
- Fuente: mortalidad del Distrito (exploración 4.4).
- → *¿Por qué nadie habla de eso?*

### 2. Porque la base más usada no lo muestra
- La base del ITM registra entre el 52% y el 91% de los muertos, según el año; en 2023–2024 aparece plana (160 y 164).
- Solo 4 de cada 10 mueren en la vía; los demás mueren en el hospital y se pierden del registro.
- **Decisión que justifica:** los muertos se cuentan con la cifra oficial y se cruzan 7 fuentes, cada una para lo que sirve (D13).
- Muestra al jurado que conocemos los datos a fondo. La limpieza se menciona en una línea; el detalle va al anexo.

## Acto II · Quién muere y por qué

### 3. Dos víctimas
- **9 de cada 10 muertos son peatones (46%) o motociclistas (45%).**
- **El peatón muere por gravedad:** 3,4 veces más letal que la moto; con 60 años o más, 5,7 veces (logística, D22).
- **El mismo choque no pesa igual para todos:** un motociclista joven de día muere 1 de cada 331 veces; un peatón de 60+ de madrugada, 1 de cada 7 (dato real: 33 de 236).
- **La moto muere por volumen:** está en 8 de cada 10 incidentes graves (84–86%).
- **Es la muerte que Medellín no ha logrado bajar:** los peatones muertos bajaron 25% entre 2015 y 2019; los de moto, no.
- **Decisión que justifica:** dos problemas, dos medidas. **Velocidad para el peatón (Bogotá) y carril para la moto (Malasia)** (D23). El título del proyecto sale de los datos.
- Pendiente de definir: si se usan dos personajes ilustrativos (por ejemplo, un motociclista joven y una peatona mayor) con sus probabilidades reales.

## Acto III · La velocidad: cuánto pesa y dónde

### 4. Donde se va más rápido, el choque mata más
- Letalidad por diseño de vía: paso elevado 1,27%, puente 1,15%, tramo 0,64%, intersección 0,48% (base de motos, D14).
- Es evidencia independiente: esa base no tiene ningún dato de velocidad.
- → *¿Entonces hay que bajar la velocidad en toda la ciudad?*

### 5. No: Medellín tiene dos velocidades
- Las arterias ya van a 14–35 km/h por la congestión.
- Solo 4 vías rápidas (Regional, Autopista Norte, Autopista Sur, Las Palmas) pasan de 50, y lo hacen a cualquier hora (~20% de las mediciones).
- Pendiente: velocidad nocturna por corredor (Johan) y los corredores que concentran las muertes (Josué).
- **Decisión que justifica:** la medida de Bogotá se evalúa solo en esas 4 vías (D18). Una propuesta focalizada es más creíble que una general.

### 6. ¿Cuánto pesa la velocidad en Medellín?
- El exponente de Medellín frente al de Nilsson (notebook 03).
- ⏳ Espera la asignación a corredores (Josué) y el corte de la geometría (Johan).

### 7. La ciudad hizo el experimento por nosotros
- En la cuarentena Medellín fue un 31% más rápida.
- Corregido por quiénes fueron las víctimas, murió algo más gente (+19%), pero sin distinguirse de un año normal (placebos 2015–2019: 0,89 a 1,20) y menos de lo que predice Nilsson (notebook 04).
- **Decisión que justifica:** no se copia el número de la literatura; se usan rangos y se simula con incertidumbre (D26).
- Es el momento en que el jurado ve que pusimos a prueba nuestra propia hipótesis y contamos lo que salió.

## Acto IV · Lo que proponemos

### 8. Si no hacemos nada
- Proyección por corredor de incidentes graves y muertes.
- ⏳ Predicción (corredor × mes).

### 9. Segundos contra vidas
- Por corredor: vidas salvadas por año, con su intervalo, con el tope de Bogotá y con el carril de Malasia, frente a lo que cuesta cada medida.
- El tope de 50 cuesta entre 9 y 62 segundos por viaje (estimación preliminar; la oficial es la de Johan).
- **Es la gráfica central del proyecto.**
- ⏳ Monte Carlo.

### 10. La recomendación
- Qué corredor va primero, con qué medida, cuántas vidas y cuántos segundos.
- El orden lo dicen los datos: primero donde hay más peatones y mayores (velocidad) y donde más pesa la moto (carril). El 10% de las víctimas de mayor riesgo concentra el 43% de los muertos.
- ⏳ Depende de 6, 8 y 9.

## Cierre · Lo que la velocidad no resuelve

### 11. La madrugada
- La madrugada triplica el riesgo de morir (×3,2, ajustado), pero allí la velocidad apenas sube 4%.
- Ese riesgo pide otras medidas: control de alcohol, iluminación, respuesta médica (D20).
- Reconocerlo hace la propuesta más honesta.
- Después: limitaciones, fuentes y uso de IA.

---

## Lo que queda fuera de la historia (va a los anexos)
- El pico de 2022 de la base del ITM: era un artefacto del registro.
- La clase de incidente: casi repite al actor.
- La tabla completa de odds ratios: en la historia van los perfiles.
- Las tablas de limpieza de datos.
- Las cifras brutas de la cuarentena (+31% moto, +37% peatón): exageraban el efecto.

## Cambios frente al plan original
- El backtest pasa del final al Acto III (paso 7): la cuarentena es un experimento sobre la velocidad.
- "Quién muere" va antes que "dónde" y que la velocidad: es lo que justifica las dos medidas.
- El riesgo nocturno sale de las limitaciones y se convierte en el cierre.

## Estado por paso
| Paso | Listo con lo que hay | Depende de |
|---|---|---|
| 1, 2, 3, 4, 7, 11 | ✅ | — |
| 5 | En parte | Johan (noche), Josué (concentración y mapas) |
| 6 | ⏳ | Notebook 03 (Josué y Johan) |
| 8, 9, 10 | ⏳ | Predicción, Monte Carlo |
