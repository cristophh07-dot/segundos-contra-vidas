# Limpieza de datos de seguridad vial

## incidentes_limpios (fuente: base del ITM, Mendeley)
- Filas leídas: 702.540
- Filas eliminadas: 0 (todas tienen fecha y gravedad válidas)
- Filas finales: 702.540 (2008 a ago. 2025)
- Dejadas vacías, no eliminadas: 44.785 sin coordenadas, 15.365 sin dirección
  (incluye direcciones de relleno "CALLE 999 CON CARRERA 999", según D10)
- "N/D" en comuna y "Sin inf" en barrio pasan a vacío
- hay_moto: vacío en todas las filas (el ITM no se une con víctimas ni motos, D12 y D14)
- hay_peaton: 1 si la clase es atropello; vacío en las demás
- corredor_id: vacío y metodo_asignacion = sin_asignar hasta recibir el catálogo de Johan

## victimas_limpias (fuente: MEData)
- Filas leídas: 1.048.317
- Filas eliminadas: 812.474, porque están completamente vacías (D12)
- Sin fecha o gravedad eliminadas: 0
- Filas finales: 235.843 (233.894 heridos y 1.949 muertos), 2014-01-01 a 2021-09-30
- Dejadas vacías: 22.960 sin coordenadas
- Coordenadas con coma decimal convertidas a punto
- "Acompañante de Motocicleta" y "Acompañante de motocicleta" unificados en parrillero
- "Sin Inf" en sexo pasa a vacío
- incidente_id: vacío (no se une con el ITM, D12)

## mortalidad_distrito (fuente: Observatorio de Movilidad)
- Filas leídas: 1.541
- Filas eliminadas: 0 (27 comparten id pero son fallecidos distintos)
- Sin fecha válida: 0
- Dejadas vacías: 4 sin coordenadas, 3 sin hora, 9 sin clase
- Comuna "La Calendaria" corregida a "La Candelaria"; comuna "0" pasa a vacío