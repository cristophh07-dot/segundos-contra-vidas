"""
src/fuentes.py — ÚNICA fuente de verdad de las URLs del proyecto.
Hackathon de Datos 2026 · ITM · "Segundos contra vidas"

Reglas:
- Nadie escribe URLs sueltas en notebooks: todo se lee con src.descarga.leer("<clave>").
- Las URLs se verificaron el 4 de noviembre de 2026 (respondían 200).
- "tamano_mb" es aproximado, para saber cuánto tarda la primera descarga.
"""

FUENTES = {
    # =====================================================================
    # SINIESTROS (responsable: Josué)
    # =====================================================================
    "incidentes_itm": {
        # Base de los profesores del ITM. El .zip trae 4 archivos; los datos están en
        # Fatal_Road_Traffic.xlsx (63 MB, hoja "BD"). También trae diccionario, README y script R.
        "url": "https://data.mendeley.com/public-files/datasets/r6g5dfnpgh/files/e992c888-5819-40c6-9538-41980ea1d429/file_downloaded",
        "formato": "zip",
        "archivo": "Medellin_Road_Traffic_Fatalities_Dataset_2008_2025/Fatal_Road_Traffic.xlsx",
        "diccionario_en_zip": "Medellin_Road_Traffic_Fatalities_Dataset_2008_2025/Data_Dictionary_Fatal_Road_Traffic.xlsx",
        "tamano_mb": 63,
        "sha256": "7c5dbdc6aa81942d605dfc5235d8c03b412c5b97a31f646cb6d4352976eae706",
        "fuente": "Arango, Quiceno y Correa (2026). Dataset on Road Traffic Fatalities in Medellín, Colombia (2008–2025). Mendeley Data, DOI 10.17632/r6g5dfnpgh.1",
        "pagina": "https://data.mendeley.com/datasets/r6g5dfnpgh/1",
        "licencia": "CC BY 4.0",
        "anios": "2008 – ago. 2025",
    },
    "victimas_medata": {
        # Ojo: coordenadas con coma decimal entre comillas ("6,2669").
        # Trae "radicado", que puede servir para unir víctimas con incidentes.
        "url": "https://medata.app.medellin.gov.co/sites/default/files/distribution/1-023-25-000360/Mede_Victimas_inci.csv",
        "diccionario": "https://medata.app.medellin.gov.co/sites/default/files/distribution/1-023-25-000360/diccionario_mede_victimas_inci.json",
        "formato": "csv",
        "tamano_mb": 54,
        "fuente": "MEData – Víctimas en Incidentes viales (Secretaría de Movilidad de Medellín)",
        "pagina": "https://medata.app.medellin.gov.co/dataset/1-023-25-000360",
        "licencia": "CC BY-SA 4.0",
        "anios": "desde 2014 (modificado 02-03-2025; verificar año máximo)",
    },
    "motos_medata": {
        "url": "https://medata.app.medellin.gov.co/sites/default/files/resources/fb3c5c2c57fafad330a038f9fb02d6ab_1743010268/incidentes_viales_motos.csv",
        "formato": "csv",
        "tamano_mb": 22,
        "fuente": "MEData – Incidentes Viales con Motos (Secretaría de Movilidad de Medellín)",
        "pagina": "https://medata.app.medellin.gov.co/dataset/1-023-25-000277",
        "licencia": "CC BY-SA 4.0",
        "anios": "desde 2015 (modificado 01-02-2023)",
    },
    "incidentes_medata": {
        # Respaldo si la organización no aprueba la base del ITM.
        "url": "https://medata.app.medellin.gov.co/sites/default/files/resources/98400bfb4bb49fab4c30a729b68deb5a_1743010252/incidentes_viales.csv",
        "formato": "csv",
        "tamano_mb": 62,
        "fuente": "MEData – Incidentes viales (Secretaría de Movilidad de Medellín)",
        "pagina": "https://medata.app.medellin.gov.co/dataset/1-023-25-000094",
        "licencia": "CC BY-SA 4.0",
        "anios": "2014 – ago. 2020 (aprox.)",
    },
    "mortalidad_distrito": {
        # Servicio ArcGIS: máximo 2.000 registros por consulta; leer() pagina solo.
        # 1.541 fallecidos al 4-nov-2026.
        "url": "https://www.medellin.gov.co/servidormapas/rest/services/transporte/VM_Mortalidad/MapServer/0/query",
        "formato": "arcgis",
        "tamano_mb": 1,
        "fuente": "Alcaldía de Medellín – Secretaría de Movilidad – Observatorio de Movilidad, capa Mortalidad",
        "pagina": "https://www.medellin.gov.co/servidormapas/rest/services/transporte/VM_Mortalidad/MapServer/0",
        "licencia": "Uso para análisis y planificación (ver metadatos de la capa)",
        "anios": "2019 – 2024",
    },

    # =====================================================================
    # VELOCIDAD Y TRÁFICO (responsable: Johan)
    # =====================================================================
    "velocidad_gt": {
        "url": "https://medata.app.medellin.gov.co/sites/default/files/distribution/1-023-25-000287/Velocidad_y_tiempo_de_viaje_GT.csv",
        "formato": "csv",
        "tamano_mb": 90,
        "fuente": "MEData – Velocidad y tiempo de viaje GT (SIMM, Secretaría de Movilidad de Medellín)",
        "pagina": "https://medata.app.medellin.gov.co/dataset/1-023-25-000287",
        "licencia": "CC BY-SA 4.0",
        "anios": "feb. 2017 – dic. 2020 (aprox.), horas 6:00–20:00; trae LONGITUD_KM, INICIO y FIN de cada tramo",
    },
    "velocidad_simm": {
        # Trae las 24 horas (sí hay datos de noche) y carril, corredor, sentido, intensidad y categorías.
        # Coordenadas en metros (MAGNA-SIRGAS Medellín) y con coma decimal, no en grados.
        "url": "https://medata.app.medellin.gov.co/sites/default/files/resources/1c0b79d0227e7153bef3cb9c6fe3a63d_1743010237/velocidad_e_intensidad_vehicular_en_medellin.csv",
        "formato": "csv",
        "tamano_mb": 79,
        "fuente": "MEData – Velocidad e intensidad vehicular en Medellín (SIMM, Secretaría de Movilidad de Medellín)",
        "pagina": "https://medata.app.medellin.gov.co/dataset/1-023-25-000296",
        "licencia": "CC BY-SA 4.0",
        "anios": "desde mar. 2017 (modificado 10-08-2021)",
    },
    "conteo_simm": {
        # Conteos de las cámaras ARS, CCTV y de fotodetección del SIMM, con VELOCIDAD e INTENSIDAD por dispositivo.
        # Datos desde enero de 2021: es la única fuente de velocidad posterior a 2020.
        # ¡PESA 856 MB! Leer por partes: leer("conteo_simm", usecols=[...], chunksize=500_000).
        "url": "https://medata.app.medellin.gov.co/sites/default/files/resources/c55e39ca070041d812721588475a0a90_1743010250/simmtrafficdata.csv",
        "diccionario": "https://medata.app.medellin.gov.co/sites/default/files/distribution/1-023-25-000300/simmtraffic.json",
        "formato": "csv",
        "tamano_mb": 856,
        "fuente": "MEData – Conteo Vehicular (Simmtrafficdata) (SIMM, Secretaría de Movilidad de Medellín)",
        "pagina": "https://medata.app.medellin.gov.co/dataset/1-023-25-000300",
        "licencia": "CC BY-SA 4.0 según los metadatos (la página del dataset muestra CC BY 4.0)",
        "anios": "desde ene. 2021 (verificar año máximo)",
    },
}
