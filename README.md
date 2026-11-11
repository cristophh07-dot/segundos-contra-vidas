# Segundos contra vidas

**Equipo The Outliers** · Cristopher Corrales Boada (líder), Josué Tamayo Uribe y Johan Hernando López Londoño
Hackathon de Datos 2026 · ITM · Categoría interna · Análisis de datos · Transporte y movilidad

**Pregunta:** ¿en qué vías de Medellín salvaría más vidas bajar la velocidad (como Bogotá) o separar a las motos (como Malasia), y cuántos segundos le costaría a cada conductor?

**Respuesta corta:** en solo 3 vías (Regional, Autopista Sur y Autopista Norte), un tope de 50 km/h con control permanente y un carril exclusivo de motos salvarían unas **5,7 vidas al año** y evitarían unos **372 incidentes graves al año**, 1 de cada 4 en esas vías, a cambio de **57 segundos por viaje** en la Regional y entre 4 y 16 s en las autopistas.

## Verlo sin instalar nada
El notebook principal ya está ejecutado: [notebooks/segundos_contra_vidas.ipynb](notebooks/segundos_contra_vidas.ipynb)

## Ejecutarlo
Paso a paso en [`instrucciones.txt`](instrucciones.txt). En resumen, con Python 3.13 (con o sin Anaconda):
```
python -m pip install -r requirements.txt
python -m src.correr_todo
```
El segundo comando corre los 4 notebooks necesarios en orden. Los datos se descargan solos desde sus fuentes oficiales (unos 370 MB la primera vez). Para ver el resultado: `python -m notebook` y abrir `notebooks/segundos_contra_vidas.ipynb`.

## Estructura
- `notebooks/` el notebook principal (`segundos_contra_vidas.ipynb`) y los anexos 01 a 06
- `src/` el código: fuentes y descarga, limpieza, corredores, modelos y gráficas
- `docs/` decisiones del análisis (`DECISIONES.md`), referentes verificados (`referentes.md`) y uso de IA (`uso_ia_general.md`)
- `figuras/` gráficas exportadas
- `data/` se llena sola al correr el código (no se sube)
