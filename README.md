# Segundos contra vidas

Hackathon de Datos 2026 · ITM · Modalidad análisis de datos · Transporte y movilidad

**Pregunta:** ¿En qué corredores viales de Medellín una reducción de la velocidad o un carril
exclusivo para motos salvaría más vidas, y cuánto tiempo le costaría esa medida a quienes se movilizan?

Equipo: Cristopher Corrales (líder), Josué y Johan.

## Cómo empezar
```
pip install -r requirements.txt
python -m src.verificar_fuentes
```
Todos los datos se leen desde su URL con `from src.descarga import leer`.
Ver `instrucciones.txt` para ejecutar el proyecto completo.

## Estructura
- `src/` código compartido (fuentes, descarga y funciones de cada integrante)
- `notebooks/` notebooks de trabajo y el notebook final
- `docs/` contratos, diccionarios, referentes y uso de IA
- `figuras/` gráficas exportadas
- `data/` se llena sola al correr el código (no se sube)
