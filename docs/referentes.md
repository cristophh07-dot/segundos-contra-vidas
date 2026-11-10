# Referentes verificados

*Verificado el 9 nov 2026 contra la fuente primaria o la fuente oficial citada. Si una cifra no está aquí, no va en el notebook.*

## 1. Bogotá: límite de 50 km/h en avenidas arteriales

| Qué | Cifra | Periodo y comparación | Fuente |
|---|---|---|---|
| Muertes en los 5 primeros corredores (Av. Boyacá, Av. Carrera 68, Av. Ciudad de Cali, Av. Calle 80, Av. de las Américas) | **−37%** (de 46 a 29) | Oct 2018 – ene 2019, frente al promedio del mismo periodo de 2015–2017 | Secretaría Distrital de Movilidad, citada por [CESVI Colombia, Revista Autocrash](https://www.revistaautocrash.com/limite-de-velocidad-a-50-km-h-ha-disminuido-las-muertes-en-un-37-en-bogota/) e [Infobae (2021)](https://www.infobae.com/america/soluciones/2021/12/24/con-el-limite-de-velocidad-de-50-kmh-bogota-redujo-en-mas-del-30-las-muertes-por-accidentes-de-transito/) |
| Muertes en 10 avenidas arteriales (60 → 50 km/h) | **−22%** | No se especifica | [Global Road Safety Facility (Banco Mundial)](https://roadsafetyfacility.org/success-stories/improving-road-safety-through-speed-management-bogota) |
| Vidas salvadas en 10 corredores | **46** | Oct 2018 – dic 2019 | Secretaría de Movilidad (2020), presentado por WRI en el [ITF/OCDE](https://www.itf-oecd.org/sites/default/files/repositories/segundo_lopez_-_wri.pdf) |

- **Corrección:** la cifra "−32%" que usábamos no aparece en ninguna fuente. Se reemplaza por el **rango −22% a −37%**.
- **Cuidado al citarlo:** el −37% compara solo 4 meses y no tiene grupo de control, así que puede incluir regresión a la media. El −22% cubre más vías. Existe un estudio con grupos de control (López et al., 2019, *Effects of reducing and enforcing speed limits in selected arterial roads in Bogota*), pero sus resultados se reportan por kilómetro y para motociclistas, y no se pudo acceder al texto completo.
- **Cómo se hizo cumplir (corregido):** en 2018 no fue con cámaras. Se cambiaron las señales de 60 a 50 km/h en octubre de 2018, hubo puestos de control visibles de la Policía de Tránsito (759 entre enero y noviembre de 2018, frente a 356 en 2017), un periodo pedagógico hasta el 13 de diciembre y **multas desde el 15 de diciembre de 2018** ([Alcaldía de Bogotá](https://bogota.gov.co/mi-ciudad/movilidad/multas-para-quienes-superen-50-km/h-en-5-corredores-de-bogota)). No fue solo un cambio de señales.
- **Cámaras de fotodetección (después):** en las zonas con cámaras, los siniestros con fallecidos bajaron 19% en 2022 y el primer semestre de 2023; la fuente no dice frente a qué periodo. La Secretaría atribuye al límite de 50 km/h en los corredores principales 202 vidas salvadas desde 2018 frente al promedio anterior ([Alcaldía de Bogotá, 2023](https://bogota.gov.co/mi-ciudad/movilidad/camaras-de-fotodeteccion-redujeron-siniestros-viales-con-fatalidad)). Sirve como apoyo, no como cifra del Monte Carlo: no tiene periodo de comparación claro.

## 2. Malasia: carril exclusivo de motos en la Federal Highway F02

| Qué | Cifra | Detalle | Fuente |
|---|---|---|---|
| Accidentes de moto en los 14 km del corredor | **−25%** (de 122 a 92) | χ² = 5,19; p < 0,05 | Radin Umar, R.S., Mackay, G.M. y Hills, B.L. (1995). *Preliminary analysis of exclusive motorcycle lanes along the Federal Highway F02, Shah Alam, Malaysia.* IATSS Research, 19(2). [Ficha](https://www.gov.uk/research-for-development-outputs/preliminary-analysis-of-exclusive-motorcycle-lanes-along-the-federal-highway-f02-shah-alam-malaysia) · [PDF](https://assets.publishing.service.gov.uk/media/5cdc05f5ed915d5c4e406448/1_567_PA3136_1996.pdf) |
| Sin contar los de la calzada principal | **−34%** (de 122 a 81) | χ² = 9,51; p < 0,005 | Misma fuente |

- **Corrección:** el rango "25–39%" que usábamos no corresponde a la fuente. Es **25–34%**.
- El estudio mide accidentes de moto, no muertes, y es un análisis antes y después sin grupo de control.

## 3. Relación entre velocidad y siniestros

**Nilsson (modelo potencia clásico):** si la velocidad media cambia en una proporción *r*, los siniestros cambian en *r* elevado a:
- **2** para siniestros con heridos;
- **3** para siniestros con heridos graves;
- **4** para siniestros mortales.

Fuente: Nilsson (1982, 2004), según [FHWA](https://www.fhwa.dot.gov/publications/research/safety/17098/003.cfm).

**Elvik (2009), la actualización que distingue vías urbanas y rurales.** Valores tomados de la [ficha de SWOV (2012), "The relation between speed and crashes"](https://www.littlerock.gov/media/2484/the-relation-between-speed-and-crashes.pdf), tabla 1; la fuente original es Elvik, R. (2009), TØI Report 1034/2009:

| Severidad | **Vías urbanas** (IC 95%) | Rurales, incluidas autopistas (IC 95%) |
|---|---|---|
| Siniestros mortales | **2,6** (0,3 – 4,9) | 4,1 (2,9 – 5,3) |
| Víctimas fatales | **3,0** (−0,5 – 6,5) | 4,6 (4,0 – 5,2) |
| Siniestros con heridos graves | **1,5** (0,9 – 2,1) | 2,6 (−2,7 – 7,9) |
| Víctimas con heridas graves | **2,0** (0,8 – 3,2) | 3,5 (0,5 – 5,5) |
| Siniestros con heridos leves | **1,0** (0,6 – 1,4) | 1,1 (0,0 – 2,2) |

- **Corrección:** el "3,0 (−0,5 a 6,5)" del SWOV que usábamos corresponde a **víctimas fatales** en vía urbana, no a siniestros mortales (que es 2,6).
- **Por qué importa:** para vías urbanas como las de Medellín, la literatura actualizada da exponentes **más bajos que Nilsson clásico**: alrededor de 1,5 para los siniestros con heridos graves y 2,6 para los mortales, frente a 2 y 4.
- **Coherencia con nuestros datos:** con Elvik urbano, el exponente implícito de la letalidad es ≈ 2,6 − 1,5 ≈ 1,1. En la cuarentena estimamos 0,64 (IC −0,29 a 1,52, notebook 04): **es compatible**.

## 4. Límite de velocidad variable (solo como paso siguiente en la recomendación)

| Dónde | Cambio en choques | Fuente |
|---|---|---|
| Wyoming (autopista) | **−34,4%** | [FHWA, *Safety Evaluation of Variable Speed Limits*](https://www.fhwa.dot.gov/publications/research/safety/21053/index.cfm) |
| Georgia (autopista, con grupo de comparación) | **−29,2%** | Misma fuente |
| Virginia (clima adverso) | Sin evidencia de cambio | Misma fuente |
