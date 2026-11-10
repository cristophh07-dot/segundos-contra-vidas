"""
src/graficas.py — gráficas del notebook final (Segundos contra vidas).

Reglas (docs/guion_notebook_final.md):
- El título de cada gráfica es su mensaje.
- Paleta fija del proyecto: el mismo color siempre significa lo mismo.
- Etiquetas directas en vez de leyendas cuando hay pocas series; ejes y grilla discretos.
Cada función recibe las tablas ya listas (src/historia.py) y devuelve la figura.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch

# --- Paleta del proyecto (validada; la misma de los notebooks 03 a 06) ---
AZUL, NARANJA, VERDE, AMARILLO = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
ROSA, VERDE_OSC, MORADO, ROJO = "#e87ba4", "#008300", "#6250d6", "#e34948"
TINTA, TINTA_2, GRILLA, GRIS, FONDO = "#0b0b0b", "#52514e", "#e6e5e1", "#c3c2b7", "#ffffff"

plt.rcParams.update({
    "figure.facecolor": FONDO, "axes.facecolor": FONDO, "savefig.facecolor": FONDO,
    "font.size": 11, "axes.titlesize": 14, "axes.labelcolor": TINTA_2,
    "xtick.color": TINTA_2, "ytick.color": TINTA_2, "axes.edgecolor": GRILLA,
})


def _estilo(ax, eje: str = "y"):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRILLA)
    if eje:
        ax.grid(axis=eje, color=GRILLA, lw=0.8)
    ax.set_axisbelow(True)


def _titulo(fig, texto: str, sub: str | None = None):
    alto = fig.get_figheight()
    fig.suptitle(texto, x=0.01, y=1 - 0.08 / alto, ha="left", va="top", fontsize=15, weight="bold", color=TINTA)
    if sub:
        fig.text(0.01, 1 - 0.42 / alto, sub, ha="left", va="top", fontsize=10.5, color=TINTA_2)


def _caja(ax, x, y, w, h, texto, color, sub=None, tinta=TINTA):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.02",
                                fc=color, ec="none", alpha=0.16))
    ax.add_patch(FancyBboxPatch((x, y), 0.008, h, boxstyle="square,pad=0", fc=color, ec="none"))
    cy = y + h / 2 + (0.022 if sub else 0)
    ax.text(x + 0.02, cy, texto, ha="left", va="center", fontsize=10.5, weight="bold", color=tinta)
    if sub:
        ax.text(x + 0.02, y + h / 2 - 0.03, sub, ha="left", va="center", fontsize=9, color=TINTA_2)


def _flecha(ax, x0, y0, x1, y1):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", color=TINTA_2, lw=1.3, shrinkA=0, shrinkB=0))


# =====================================================================================
# Parte 0 · Los datos
# =====================================================================================
# Periodos que de verdad trae cada archivo (no el que dice su ficha); ver docs/DECISIONES.md.
PERIODOS = [
    ("Incidentes del ITM (Mendeley)",          "2008-01", "2025-08", "siniestros", "D3, D9"),
    ("Incidentes viales (MEData)",             "2014-01", "2020-08", "siniestros", "respaldo"),
    ("Víctimas (MEData)",                      "2014-01", "2021-09", "siniestros", "D12"),
    ("Incidentes con motos (MEData)",          "2015-01", "2021-12", "siniestros", "D14"),
    ("Mortalidad del Distrito",                "2019-01", "2024-12", "siniestros", "D13, D17"),
    ("Velocidad · Google Traffic (6–20 h)",    "2017-02", "2020-12", "velocidad", "D29"),
    ("Velocidad e intensidad · SIMM (24 h)",   "2020-07", "2020-08", "velocidad", "D21"),
]


def linea_tiempo_fuentes():
    fig, ax = plt.subplots(figsize=(12, 4.6))
    for i, (nombre, ini, fin, tipo, dec) in enumerate(PERIODOS[::-1]):
        a, b = pd.Timestamp(ini), pd.Timestamp(fin) + pd.offsets.MonthEnd(0)
        color = AZUL if tipo == "siniestros" else NARANJA
        ancho = max((b - a).days, 25)
        ax.barh(i, ancho, left=a, height=0.55, color=color, zorder=2)
        ax.text(a - pd.Timedelta(days=60), i, nombre, ha="right", va="center", fontsize=10, color=TINTA)
        meses = "ene feb mar abr may jun jul ago sep oct nov dic".split()
        etiqueta = f"{a:%Y}–{b:%Y}" if a.year != b.year else f"{meses[a.month - 1]} – {meses[b.month - 1]} {b:%Y}"
        ax.text(a + pd.Timedelta(days=ancho + 50), i, etiqueta, va="center", fontsize=9, color=TINTA_2)
    ax.axvspan(pd.Timestamp("2022-01-01"), pd.Timestamp("2024-12-31"), color=GRILLA, alpha=0.7, lw=0, zorder=0)
    ax.text(pd.Timestamp("2023-07-01"), -0.95, "2022–2024:\nsuben las muertes",
            ha="center", va="bottom", fontsize=9, color=TINTA_2)
    ax.set_yticks([]); ax.set_xlim(pd.Timestamp("2007-01-01"), pd.Timestamp("2027-06-01"))
    ax.set_ylim(-1.0, len(PERIODOS) - 0.4)
    _estilo(ax, eje="x")
    ax.spines["left"].set_visible(False)
    _titulo(fig, "Siete fuentes, siete periodos distintos: casi ninguna llega a los años en que más suben las muertes")
    fig.text(0.01, 0.9, "■ siniestros", color=AZUL, fontsize=10, va="top")
    fig.text(0.1, 0.9, "■ velocidad y tráfico", color=NARANJA, fontsize=10, va="top")
    fig.subplots_adjust(left=0.27, right=0.97, top=0.83, bottom=0.1)
    return fig


def diagrama_datos():
    fig, ax = plt.subplots(figsize=(12, 4.8))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    sin = ["Incidentes del ITM", "Víctimas (MEData)", "Mortalidad del Distrito", "Incidentes con motos"]
    vel = ["Google Traffic", "SIMM"]
    ys = np.linspace(0.84, 0.16, len(sin) + len(vel))
    for y, n in zip(ys[:4], sin):
        _caja(ax, 0.01, y - 0.045, 0.22, 0.09, n, AZUL)
    for y, n in zip(ys[4:], vel):
        _caja(ax, 0.01, y - 0.045, 0.22, 0.09, n, NARANJA)
    _caja(ax, 0.32, 0.56, 0.2, 0.2, "Limpieza", MORADO, sub="filas vacías, relleno,\nduplicados, cobertura")
    _caja(ax, 0.32, 0.24, 0.2, 0.2, "12 corredores", VERDE, sub="geometría propia con\nlos sensores del SIMM")
    for y in ys:
        _flecha(ax, 0.235, y, 0.315, 0.66 if y > 0.5 else 0.34)
    _flecha(ax, 0.42, 0.555, 0.42, 0.445)
    _caja(ax, 0.62, 0.34, 0.36, 0.32, "Cada incidente, víctima, muerto\ny medición de velocidad\nqueda en su corredor", VERDE,
          sub=None)
    _flecha(ax, 0.525, 0.34, 0.615, 0.5)
    ax.text(0.8, 0.22, "a menos de 50 m (D27, D30)", ha="center", fontsize=9.5, color=TINTA_2)
    _titulo(fig, "Las fuentes no comparten un identificador: las unimos por el lugar, con un mapa propio de los corredores")
    fig.subplots_adjust(left=0.01, right=0.99, top=0.88, bottom=0.02)
    return fig


def graves_contra_danos(tabla: pd.DataFrame):
    """tabla = historia.graves_y_danos(): índice año, columnas 'graves' y 'solo daños'."""
    fig, ax = plt.subplots(figsize=(11, 4.6))
    x = tabla.index.to_numpy()
    for col, color in [("solo daños", GRIS), ("graves", AZUL)]:
        ax.plot(x, tabla[col] / 1000, color=color, lw=2.4, marker="o", ms=4)
        ax.text(x[-1] + 0.3, tabla[col].iloc[-1] / 1000,
                {"graves": "Graves (heridos y muertos)", "solo daños": "Solo daños"}[col],
                va="center", fontsize=10, color=TINTA)
    ax.axvspan(2022.5, x[-1] + 0.5, color=GRILLA, alpha=0.6, lw=0)
    ax.text(2023.5, ax.get_ylim()[1] * 0.97, "cambia el\nregistro", ha="center", va="top", fontsize=9, color=TINTA_2)
    ax.set_xlim(x[0] - 0.5, x[-1] + 4.2); ax.set_ylim(bottom=0)
    ax.set_xticks(range(int(x[0]), int(x[-1]) + 1, 2))
    ax.set_ylabel("Miles de incidentes por año")
    _estilo(ax)
    _titulo(fig, "Desde 2023 casi no se registran los choques de solo daños; los graves siguen su curva",
            "Base de incidentes del ITM, 2008–2024. Por eso todo el análisis cuenta solo incidentes graves (D8).")
    fig.subplots_adjust(left=0.07, right=0.98, top=0.82, bottom=0.1)
    return fig


ANALISIS = [
    ("01", "¿Qué dicen los datos?", "limpieza y unión\npor corredor", MORADO),
    ("02", "¿Quién muere?", "regresión logística\nvalidada", AZUL),
    ("03", "¿Cuánto pesa\nla velocidad?", "binomial negativa\n+ bootstrap", NARANJA),
    ("04", "¿Lo confirma\nla cuarentena?", "esperados contra\nobservados + placebos", NARANJA),
    ("05", "¿Y si no\nhacemos nada?", "4 modelos, prueba\n2023–2025", VERDE),
    ("06", "¿Cuántas vidas,\na qué costo?", "Monte Carlo,\n10.000 simulaciones", ROJO),
]


def camino_analisis():
    fig, ax = plt.subplots(figsize=(13, 3.4))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    w, gap = 0.148, 0.018
    for i, (nb, preg, metodo, color) in enumerate(ANALISIS):
        x = 0.01 + i * (w + gap)
        ax.add_patch(FancyBboxPatch((x, 0.12), w, 0.72, boxstyle="round,pad=0.008,rounding_size=0.02",
                                    fc=color, ec="none", alpha=0.14))
        ax.text(x + 0.012, 0.76, f"notebook {nb}", fontsize=8.5, color=TINTA_2, va="top")
        ax.text(x + 0.012, 0.6, preg, fontsize=10.5, weight="bold", color=TINTA, va="center")
        ax.text(x + 0.012, 0.3, metodo, fontsize=9, color=TINTA_2, va="center")
        if i < len(ANALISIS) - 1:
            _flecha(ax, x + w + 0.002, 0.48, x + w + gap - 0.002, 0.48)
    _titulo(fig, "Seis análisis: cada uno responde una pregunta y le pasa su resultado al siguiente")
    fig.subplots_adjust(left=0.005, right=0.995, top=0.8, bottom=0.02)
    return fig


# =====================================================================================
# Acto I · El problema
# =====================================================================================
def muertes_por_anio(serie: pd.DataFrame):
    """serie = historia.muertes_por_anio(): índice año, columna 'muertos'."""
    s = serie["muertos"]
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.plot(s.index, s.values, color=ROJO, lw=2.6, marker="o", ms=5)
    ax.axvspan(2019.5, 2020.5, color=GRILLA, alpha=0.7, lw=0)
    ax.text(2020, s.min() * 0.93, "pandemia", ha="center", fontsize=9, color=TINTA_2)
    minimo = s.loc[2015:2019].idxmin()
    ultimo = s.index.max()
    for anio, va, dy in [(s.index.min(), "bottom", 8), (minimo, "top", -10), (ultimo, "bottom", 8)]:
        ax.annotate(f"{s[anio]:.0f}", (anio, s[anio]), xytext=(0, dy), textcoords="offset points",
                    ha="center", va=va, fontsize=11, weight="bold", color=TINTA)
    ax.axvline(2018.5, color=GRIS, lw=1, ls="--")
    ax.text(2018.4, s.max() * 1.07, "MEData · víctimas", ha="right", fontsize=9, color=TINTA_2)
    ax.text(2018.6, s.max() * 1.07, "Distrito · mortalidad", ha="left", fontsize=9, color=TINTA_2)
    ax.set_ylim(s.min() * 0.85, s.max() * 1.12)
    ax.set_xticks(s.index)
    ax.set_ylabel("Muertos por año")
    _estilo(ax)
    horas = 365 * 24 / s[ultimo]
    _titulo(fig, f"En {ultimo} murieron {s[ultimo]:.0f} personas en las vías de Medellín: una cada {horas:.0f} horas",
            f"Bajaba hasta {minimo} ({s[minimo]:.0f}); desde entonces subió {(s[ultimo] / s[minimo] - 1) * 100:.0f}%.")
    fig.subplots_adjust(left=0.07, right=0.98, top=0.82, bottom=0.1)
    return fig


def mapa_corredores(mor_c: pd.DataFrame, cat: pd.DataFrame, nombres: dict, destacados=(), fondo: bool = True):
    """Muertos 2019–2024 sobre el mapa de Medellín, con los 12 corredores.
    mor_c = historia.mortalidad_corredor(); cat = historia.catalogo(); nombres = {corredor_id: nombre}.
    El mapa de fondo (calles de OpenStreetMap, estilo CARTO) necesita `contextily` e internet; si no hay,
    la gráfica sale igual, sin el fondo."""
    import shapely
    import matplotlib.patheffects as pe
    from matplotlib.lines import Line2D
    from pyproj import Transformer
    a_merc = Transformer.from_crs(4326, 3857, always_xy=True)

    lineas = {}
    for cid, w in zip(cat["corredor_id"], cat["geometria_wkt"]):
        p = np.array([(g.x, g.y) for g in shapely.from_wkt(w).geoms])
        lineas[cid] = np.column_stack(a_merc.transform(p[:, 0], p[:, 1]))
    todos = np.vstack(list(lineas.values()))
    x0, y0 = todos.min(axis=0) - 2500
    x1, y1 = todos.max(axis=0) + 2500

    d = mor_c.dropna(subset=["lat", "lon"]).copy()
    d["x"], d["y"] = a_merc.transform(d["lon"].to_numpy(), d["lat"].to_numpy())
    d = d[d["x"].between(x0, x1) & d["y"].between(y0, y1)]
    en = d[d["corredor_id"].notna()]

    fig, ax = plt.subplots(figsize=(10, 11))
    ax.scatter(d["x"], d["y"], s=9, color=TINTA_2, alpha=0.35, lw=0, zorder=3)
    ax.scatter(en["x"], en["y"], s=18, color=ROJO, lw=0, zorder=5)
    halo = [pe.Stroke(linewidth=6, foreground="white"), pe.Normal()]
    colores = dict(zip(destacados, [AZUL, NARANJA, VERDE]))
    for cid, p in lineas.items():
        if cid in colores:
            ax.plot(p[:, 0], p[:, 1], color=colores[cid], lw=4, zorder=4, path_effects=halo, solid_capstyle="round")
        else:
            ax.plot(p[:, 0], p[:, 1], color=TINTA, lw=1.8, alpha=0.75, zorder=4, solid_capstyle="round")
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for s_ in ax.spines.values():
        s_.set_visible(False)

    if fondo:
        try:
            import contextily as cx
            # Esri World Gray Canvas: mapa gris claro, sin clave de acceso (CARTO ahora pide una)
            cx.add_basemap(ax, crs="EPSG:3857", source=cx.providers.Esri.WorldGrayCanvas,
                           attribution="Mapa base: Esri, HERE, Garmin, OpenStreetMap", attribution_size=6, zorder=0)
        except ImportError:
            print("(Mapa sin fondo: falta la librería. Para verlo: pip install contextily==1.6.2)")
        except Exception as e:                                   # sin internet o el servidor no respondió
            print(f"(Mapa sin fondo: no se pudo descargar el mapa de calles ({type(e).__name__}). Revisa la conexión.)")

    total, n_en = len(mor_c), int(mor_c["corredor_id"].notna().sum())
    por = mor_c.dropna(subset=["corredor_id"]).groupby("corredor_id").size()
    marcas = [Line2D([], [], color=colores[c], lw=4, label=f"{nombres.get(c, c)} · {por.get(c, 0)} muertos")
              for c in destacados]
    marcas += [Line2D([], [], color=TINTA, lw=1.8, alpha=0.75, label=f"Otras {len(lineas) - len(destacados)} vías principales"),
               Line2D([], [], marker="o", ls="", color=ROJO, ms=5, label="Muerto a menos de 50 m de un corredor"),
               Line2D([], [], marker="o", ls="", color=TINTA_2, alpha=0.5, ms=5, label="Muerto en el resto de la ciudad")]
    top = int(por.reindex(list(destacados)).fillna(0).sum())
    leg = ax.legend(handles=marcas, loc="upper left", frameon=True, fontsize=9.5, borderpad=0.8)
    leg.get_frame().set(facecolor="white", edgecolor=GRILLA, alpha=0.92)
    _titulo(fig, f"{n_en} de los {total:,} muertos (2019–2024) cayeron sobre {len(lineas)} vías; "
                 f"{len(destacados)} de ellas suman el {top / n_en * 100:.0f}%".replace(",", "."),
            f"Muertos del Distrito con coordenadas, zona urbana de Medellín. Las 3 vías de color: {top} muertos "
            f"({top / n_en * 100:.0f}% de los que cayeron en corredores).")
    fig.subplots_adjust(left=0.01, right=0.99, top=0.91, bottom=0.01)
    return fig


# =====================================================================================
# Acto II · Quién muere y por qué
# =====================================================================================
COLOR_ACTOR = {"Peatón": AZUL, "Moto": NARANJA, "Ciclista": VERDE, "Carro (conductor o pasajero)": GRIS}


def muertos_por_actor(t: pd.DataFrame):
    """t = historia.por_actor(m)."""
    pct = t["muertos"] / t["muertos"].sum() * 100
    fig, ax = plt.subplots(figsize=(11, 2.6))
    izq = 0
    for actor, v in pct.items():
        ax.barh(0, v, left=izq, color=COLOR_ACTOR.get(actor, GRIS), height=0.6, edgecolor=FONDO, lw=2)
        if v >= 6:
            ax.text(izq + v / 2, 0, f"{actor}\n{v:.0f}%", ha="center", va="center", fontsize=10.5,
                    color="white" if actor in ("Peatón", "Moto") else TINTA, weight="bold")
        izq += v
    resto = pct[pct < 6]
    if len(resto):
        ax.text(100, -0.4, " · ".join(f"{a.lower()} {v:.0f}%" for a, v in resto.items()),
                ha="right", va="top", fontsize=9, color=TINTA_2)
    ax.set_xlim(0, 100); ax.set_ylim(-0.8, 0.4); ax.axis("off")
    pm = pct.get("Peatón", 0) + pct.get("Moto", 0)
    _titulo(fig, f"{pm:.0f} de cada 100 muertos eran peatones o motociclistas",
            f"Víctimas fallecidas, 2014 – sep 2021 (MEData), n = {int(t['muertos'].sum()):,}".replace(",", "."))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.66, bottom=0.05)
    return fig


def volumen_y_letalidad(t: pd.DataFrame):
    """t = historia.por_actor(m): a la izquierda cuántas víctimas, a la derecha cuántas mueren de cada 100."""
    orden = t.sort_values("victimas", ascending=True)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 3.8), sharey=True)
    colores = [COLOR_ACTOR.get(a, GRIS) for a in orden.index]
    a1.barh(orden.index, orden["victimas"] / 1000, color=colores, height=0.6)
    a2.barh(orden.index, orden["por_100"], color=colores, height=0.6)
    for y, (v, p) in enumerate(zip(orden["victimas"], orden["por_100"])):
        a1.text(v / 1000, y, f" {v / orden['victimas'].sum() * 100:.0f}%", va="center", fontsize=10, color=TINTA)
        a2.text(p, y, f" {p:.2f}", va="center", fontsize=10, color=TINTA)
    a1.set_title("Cuántas víctimas (miles)", loc="left", fontsize=11.5, color=TINTA)
    a2.set_title("Cuántas mueren de cada 100", loc="left", fontsize=11.5, color=TINTA)
    a1.set_xlim(0, orden["victimas"].max() / 1000 * 1.15); a2.set_xlim(0, orden["por_100"].max() * 1.25)
    for a in (a1, a2):
        _estilo(a, eje="x")
    moto = t.loc["Moto", "victimas"] / t["victimas"].sum() * 100
    veces = t.loc["Peatón", "por_100"] / t.loc["Moto", "por_100"]
    _titulo(fig, f"La moto pesa por volumen ({moto:.0f}% de las víctimas); el peatón, por gravedad ({veces:.1f} veces más letal)".replace(".", ","))
    fig.subplots_adjust(left=0.2, right=0.97, top=0.8, bottom=0.08, wspace=0.08)
    return fig


def perfiles(t: pd.DataFrame):
    """t = modelos.probabilidad_perfiles(modelo): columnas perfil, actor, 1_de_cada."""
    t = t.sort_values("1_de_cada", ascending=True)
    fig, ax = plt.subplots(figsize=(11, 4))
    riesgo = 100 / t["1_de_cada"]
    ax.barh(t["perfil"], riesgo, color=[COLOR_ACTOR.get(a, GRIS) for a in t["actor"]], height=0.6)
    for y, (r, n) in enumerate(zip(riesgo, t["1_de_cada"])):
        ax.text(r, y, f"  1 de cada {n}", va="center", fontsize=10.5, color=TINTA, weight="bold")
    ax.invert_yaxis(); ax.set_xlim(0, riesgo.max() * 1.3)
    ax.set_xlabel("Probabilidad de morir si es víctima de un incidente (%)")
    _estilo(ax, eje="x")
    a, b = t.iloc[-1], t.iloc[0]
    _titulo(fig, f"El mismo choque no pesa igual: de 1 de cada {a['1_de_cada']} a 1 de cada {b['1_de_cada']}",
            "Según el modelo logístico (hombres, entre semana): comparamos víctimas que solo se diferencian en una cosa.")
    fig.subplots_adjust(left=0.24, right=0.97, top=0.8, bottom=0.14)
    return fig


def peaton_contra_moto(t: pd.DataFrame):
    """t = historia.muertos_peaton_moto(m): índice año, columnas Peatón y Moto."""
    fig, ax = plt.subplots(figsize=(11, 4.4))
    for actor in ("Peatón", "Moto"):
        s = t[actor]
        ax.plot(s.index[:-1], s.values[:-1], color=COLOR_ACTOR[actor], lw=2.6, marker="o", ms=5)
        ax.plot(s.index[-2:], s.values[-2:], color=COLOR_ACTOR[actor], lw=2, ls=":", marker="o", ms=5)
        ax.text(s.index[-1] + 0.15, s.values[-1], "Peatones" if actor == "Peatón" else "Motociclistas",
                va="center", fontsize=10.5, color=TINTA)
    ax.set_xlim(t.index[0] - 0.4, t.index[-1] + 1.4); ax.set_xticks(t.index)
    ax.set_ylabel("Muertos por año")
    _estilo(ax)
    ax.axvspan(2019.5, 2020.5, color=GRILLA, alpha=0.7, lw=0, zorder=0)
    ax.text(2020, ax.get_ylim()[1], "pandemia", ha="center", va="top", fontsize=9, color=TINTA_2)
    cambio = {a_: (t[a_].loc[2019] / t[a_].loc[2015] - 1) * 100 for a_ in ("Peatón", "Moto")}
    verbo = lambda v: f"bajaron {abs(v):.0f}%" if v < -2 else (f"subieron {v:.0f}%" if v > 2 else "casi no cambiaron")
    _titulo(fig, f"Antes de la pandemia, los peatones muertos {verbo(cambio['Peatón'])}; los motociclistas {verbo(cambio['Moto'])}",
            "Víctimas fallecidas por año (MEData), 2015 contra 2019. La caída de 2020 es la pandemia; 2021 (punteado) llega solo hasta septiembre.")
    fig.subplots_adjust(left=0.08, right=0.97, top=0.82, bottom=0.1)
    return fig


# =====================================================================================
# Acto III · La velocidad actúa dos veces
# =====================================================================================
def letalidad_diseno(t: pd.DataFrame):
    """t = historia.letalidad_diseno(): índice diseño de vía, columnas graves y letalidad_%."""
    t = t.sort_values("letalidad_%")
    fig, ax = plt.subplots(figsize=(11, 4))
    colores = [NARANJA if v > 1 else GRIS for v in t["letalidad_%"]]
    ax.barh(t.index, t["letalidad_%"], color=colores, height=0.6)
    for y, (v, n) in enumerate(zip(t["letalidad_%"], t["graves"])):
        ax.text(v, y, f"  {v:.2f}%   ({int(n):,} incidentes)".replace(",", "."), va="center", fontsize=9.5, color=TINTA)
    ax.set_xlim(0, t["letalidad_%"].max() * 1.45)
    ax.set_xlabel("De cada 100 incidentes graves con moto, cuántos son mortales")
    _estilo(ax, eje="x")
    alto, bajo = t["letalidad_%"].idxmax(), t["letalidad_%"].idxmin()
    _titulo(fig, f"Donde nadie frena, el choque mata más: {alto.lower()} {t.loc[alto, 'letalidad_%'] / t.loc[bajo, 'letalidad_%']:.1f} veces más que {bajo.lower()}".replace(".", ","),
            "Base de incidentes con motos (MEData, 2015–2021), un registro por incidente.")
    fig.subplots_adjust(left=0.17, right=0.97, top=0.8, bottom=0.14)
    return fig


def dos_velocidades(tv: pd.DataFrame, nombres: dict, rapidas: list):
    """tv = historia.dos_velocidades(): % de los registros sobre 50 por hora, y segundos que cuesta el tope."""
    pct = tv.groupby("corredor_id")["sobre_50"].mean() * 100
    otras = pct.drop(rapidas, errors="ignore")
    colores = dict(zip(rapidas, [AZUL, NARANJA, VERDE]))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.6), gridspec_kw={"width_ratios": [1.6, 1]})
    por_hora = tv[tv["corredor_id"].isin(rapidas)].pivot_table(index="hora", columns="corredor_id",
                                                               values="sobre_50", aggfunc="mean") * 100
    for c in rapidas:
        a1.plot(por_hora.index, por_hora[c], color=colores[c], lw=2.4, marker="o", ms=4)
        a1.text(19.3, por_hora[c].iloc[-1], f"{nombres[c]} · {pct[c]:.0f}%", va="center", fontsize=9.5, color=TINTA)
    a1.set_xlim(5.6, 23.8); a1.set_ylim(0, 100); a1.set_xticks(range(6, 20, 2), [f"{h}:00" for h in range(6, 20, 2)])
    a1.set_ylabel("% de los registros sobre 50 km/h")
    a1.text(6, 3, f"En las otras {len(otras)} vías: menos del {max(otras.max(), 1):.0f}% de los registros", fontsize=9.5, color=TINTA_2)
    a1.set_title("Cuántas veces se pasa de 50, hora por hora", loc="left", fontsize=11.5, color=TINTA)
    seg = tv[tv["corredor_id"].isin(rapidas)].groupby("corredor_id")["seg_extra"].agg(
        media="mean", p90=lambda s: s.quantile(0.9)).loc[rapidas[::-1]]
    y = np.arange(len(seg))
    a2.barh(y, seg["media"], color=[colores[c] for c in seg.index], height=0.55)
    a2.scatter(seg["p90"], y, marker="|", s=380, color=TINTA, lw=2)
    for yi, (m, p) in enumerate(zip(seg["media"], seg["p90"])):
        a2.text(m + 2, yi + 0.33, f"{m:.0f} s", fontsize=10.5, color=TINTA, weight="bold")
        a2.text(p + 3, yi, f"peor 10%: {p:.0f} s", va="center", fontsize=9, color=TINTA_2)
    a2.set_yticks(y, [nombres[c] for c in seg.index]); a2.set_xlim(0, seg["p90"].max() * 1.55)
    a2.set_title("Segundos que cuesta el tope, por viaje", loc="left", fontsize=11.5, color=TINTA)
    _estilo(a1); _estilo(a2, eje="x")
    _titulo(fig, f"Medellín tiene dos velocidades: solo en {len(rapidas)} vías se pasa de 50 km/h",
            "Google Traffic 2017–2019, de 6:00 a 20:00. El tope se aplica registro por registro.")
    fig.subplots_adjust(left=0.06, right=0.97, top=0.8, bottom=0.1, wspace=0.42)
    return fig


def exponente(betas_A: np.ndarray, betas_C: np.ndarray):
    filas = [
        ("Medellín · sin tener en cuenta la hora", np.median(betas_A), *np.percentile(betas_A, [2.5, 97.5]), AZUL),
        ("Medellín · teniendo en cuenta la hora", np.median(betas_C), *np.percentile(betas_C, [2.5, 97.5]), AZUL),
        ("Literatura urbana · Elvik (2009)", 1.5, 0.9, 2.1, GRIS),
        ("Literatura clásica · Nilsson", 2.0, np.nan, np.nan, GRIS),
    ]
    fig, ax = plt.subplots(figsize=(11, 3.8))
    for y, (nombre, c, lo, hi, color) in enumerate(filas[::-1]):
        if not np.isnan(lo):
            ax.hlines(y, lo, hi, color=color, lw=3, alpha=0.5)
        ax.scatter(c, y, s=70, color=color, zorder=3)
        ax.text(c, y + 0.22, f"{c:.2f}".replace(".", ","), ha="center", fontsize=10, color=TINTA, weight="bold")
    ax.axvline(0, color=TINTA_2, lw=1)
    ax.text(0.03, len(filas) - 0.55, "0 = la velocidad no cambia los incidentes", fontsize=9, color=TINTA_2)
    ax.set_yticks(range(len(filas)), [f[0] for f in filas[::-1]])
    ax.set_xlabel("Cuánto suben los incidentes graves cuando sube la velocidad (exponente)")
    ax.set_ylim(-0.6, len(filas) - 0.3)
    _estilo(ax, eje="x")
    _titulo(fig, "En Medellín la evidencia directa es débil: el efecto va de nada a la mitad de la literatura",
            "Punto = estimación; línea = intervalo de 95% (bootstrap por corredor, 500 repeticiones).")
    fig.subplots_adjust(left=0.3, right=0.97, top=0.8, bottom=0.15)
    return fig


def cuarentena(bt: dict):
    """bt = modelos.backtest(): muertos observados / esperados en la cuarentena y en 5 años normales."""
    pla = bt["placebos"][["O/E", "IC95_inf", "IC95_sup"]].copy()
    pla.index = [i.replace("Placebo ", "") for i in pla.index]
    cua = bt["oe"].loc[[i for i in bt["oe"].index if i.startswith("Cuarentena")], ["O/E", "IC95_inf", "IC95_sup"]]
    cua.index = ["2020 · cuarentena"]
    t = pd.concat([pla, cua])
    fig, ax = plt.subplots(figsize=(11, 4))
    for y, (nombre, f) in enumerate(t.iterrows()):
        color = ROJO if "cuarentena" in nombre else GRIS
        ax.vlines(y, f["IC95_inf"], f["IC95_sup"], color=color, lw=3, alpha=0.5)
        ax.scatter(y, f["O/E"], s=80, color=color, zorder=3)
        ax.text(y + 0.12, f["O/E"], f"{f['O/E']:.2f}".replace(".", ","), va="center", fontsize=10, color=TINTA)
    ax.axhline(1, color=TINTA_2, lw=1, ls="--")
    ax.text(len(t) - 0.6, 0.99, "1 = murieron los que se esperaban", fontsize=9, color=TINTA_2, va="top", ha="right")
    ax.set_xticks(range(len(t)), t.index)
    ax.set_ylabel("Muertos observados / esperados")
    _estilo(ax)
    r = bt["razon"].get("vías rápidas", np.nan) if isinstance(bt.get("razon"), dict) else np.nan
    sub = f"La velocidad en las vías rápidas subió {(r - 1) * 100:.0f}%. " if not np.isnan(r) else ""
    _titulo(fig, f"En la cuarentena murió más gente de la esperada (×{cua['O/E'].iloc[0]:.2f}), pero en años normales ya pasó algo parecido".replace(".", ","),
            sub + "Esperados según el perfil de las víctimas (modelo logístico); 20 mar – 31 ago de cada año.")
    fig.subplots_adjust(left=0.08, right=0.97, top=0.8, bottom=0.1)
    return fig


# =====================================================================================
# Acto IV · Lo que proponemos
# =====================================================================================
def no_actuar(p: pd.DataFrame, nombres: dict):
    """p = historia.proyeccion() (notebook 05)."""
    col_u, col_p = "últimos 12 meses (sep 2024 – ago 2025)", "proyección (sep 2025 – ago 2026)"
    p = p.sort_values(col_p)
    fig, ax = plt.subplots(figsize=(11, 5.2))
    y = np.arange(len(p))
    ax.hlines(y, p["IC 90% inferior"], p["IC 90% superior"], color=AZUL, lw=5, alpha=0.3)
    ax.scatter(p[col_p], y, color=AZUL, s=45, zorder=3, label="Proyección del modelo (con su intervalo)")
    ax.scatter(p[col_u], y, color=TINTA, marker="|", s=250, lw=2, zorder=4, label="Últimos 12 meses")
    ax.set_yticks(y, [nombres.get(c, c) for c in p.index])
    ax.set_xlabel("Incidentes graves por año")
    ax.legend(frameon=False, loc="lower right", fontsize=9.5)
    _estilo(ax, eje="x")
    lo, hi = p[col_u].sum(), p[col_p].sum()
    _titulo(fig, f"Si nada cambia: entre {lo:,.0f} y {hi:,.0f} incidentes graves al año en {len(p)} vías, unos {lo / 365:.0f} al día".replace(",", "."),
            "Notebook 05: binomial negativa probada en 2023–2025. En las autopistas el modelo tiende a sobrestimar (D33).")
    fig.subplots_adjust(left=0.18, right=0.97, top=0.84, bottom=0.1)
    return fig


def segundos_contra_vidas(comp: pd.DataFrame):
    """comp = historia.comparacion() (notebook 06): índice (corredor, medida)."""
    vias = [v for v in comp.index.get_level_values(0).unique() if v != "Total 3 vías"] + ["Total 3 vías"]
    medidas = [("Tope de 50", AZUL), ("Carril de motos", NARANJA), ("Las dos juntas", VERDE)]
    seg = comp.xs("Tope de 50", level="medida")["segundos por viaje (día)"]
    etiquetas = [f"{v}\n{seg[v]:.0f} s por viaje con el tope" if v != "Total 3 vías" else "Total 3 vías" for v in vias]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 5.6), sharey=True)
    for ax, var, tit in [(a1, "muertes", "Vidas salvadas por año"), (a2, "graves", "Incidentes graves evitados por año")]:
        col = "muertes evitadas/año" if var == "muertes" else "graves evitados/año"
        for j, (m, color) in enumerate(medidas):
            x = comp.xs(m, level="medida").reindex(vias)
            y = np.arange(len(vias))[::-1] + (1 - j) * 0.25
            ax.hlines(y, x[f"{var} p5"], x[f"{var} p95"], color=color, lw=2.6, alpha=0.45)
            ax.scatter(x[col], y, color=color, s=48, zorder=3, label=m if ax is a1 else None)
            for yi, v in zip(y, x[col]):
                ax.text(v, yi + 0.09, (f"{v:.1f}" if var == "muertes" else f"{v:.0f}").replace(".", ","),
                        ha="center", va="bottom", fontsize=8.5, color=TINTA)
        ax.set_title(tit, loc="left", fontsize=11.5, color=TINTA); ax.set_xlim(left=0)
        _estilo(ax, eje="x")
    a1.set_yticks(np.arange(len(vias))[::-1], etiquetas)
    a1.legend(frameon=False, loc="upper right", fontsize=9.5)
    tot = comp.loc[("Total 3 vías", "Las dos juntas")]
    _titulo(fig, f"Segundos contra vidas: las dos medidas salvarían {tot['muertes evitadas/año']:.1f} vidas al año en 3 vías".replace(".", ","),
            "Monte Carlo, 10.000 simulaciones (notebook 06). Punto = mediana; línea = intervalo de 90%. El carril no cuesta segundos.")
    fig.subplots_adjust(left=0.17, right=0.98, top=0.84, bottom=0.07, wspace=0.08)
    return fig


def cobertura(serie: pd.Series):
    """serie = historia.cobertura_coordenadas(inc)."""
    fig, ax = plt.subplots(figsize=(11, 3.8))
    ax.plot(serie.index, serie.values, color=AZUL, lw=2.6, marker="o", ms=5)
    for a, v in serie.items():
        ax.text(a, v + 0.6, f"{v:.0f}%", ha="center", fontsize=9, color=TINTA)
    ax.set_ylim(min(80, serie.min() - 3), 100); ax.set_xticks(serie.index)
    ax.set_ylabel("% de los incidentes graves con coordenadas")
    _estilo(ax)
    _titulo(fig, "En 2024 el registro perdió coordenadas sin aviso, y eso fabricaba una caída de 22% en los corredores",
            "Base de incidentes del ITM. Lo corregimos mes a mes (D32); sin el aviso, se habría leído como una mejora.")
    fig.subplots_adjust(left=0.08, right=0.97, top=0.8, bottom=0.1)
    return fig


# =====================================================================================
# Cierre · La madrugada
# =====================================================================================
def dia_noche(t: pd.DataFrame):
    """t = historia.dia_noche_corredores(): filas 'incidentes graves' y 'muertos', columnas día y noche."""
    pct = t.div(t.sum(axis=1), axis=0) * 100
    fig, ax = plt.subplots(figsize=(11, 3))
    for y, fila in enumerate(["incidentes graves", "muertos"][::-1]):
        d, n = pct.loc[fila, "día"], pct.loc[fila, "noche"]
        ax.barh(y, d, color=GRIS, height=0.55, edgecolor=FONDO, lw=2)
        ax.barh(y, n, left=d, color=MORADO, height=0.55, edgecolor=FONDO, lw=2)
        ax.text(d / 2, y, f"día {d:.0f}%", ha="center", va="center", fontsize=10.5, color=TINTA)
        ax.text(d + n / 2, y, f"noche {n:.0f}%", ha="center", va="center", fontsize=10.5, color="white", weight="bold")
    ax.set_yticks([0, 1], ["Muertos", "Incidentes graves"]); ax.set_xlim(0, 100); ax.set_xticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    _titulo(fig, f"De noche ocurre el {pct.loc['incidentes graves', 'noche']:.0f}% de los incidentes graves, "
                 f"pero el {pct.loc['muertos', 'noche']:.0f}% de los muertos",
            "12 corredores, 2019–2024. Noche = 20:00 a 5:59 (notebook 06).")
    fig.subplots_adjust(left=0.15, right=0.98, top=0.74, bottom=0.05)
    return fig


def lo_que_se_evita(t: pd.DataFrame):
    """t = historia.lo_que_se_evita(): % de muertes e incidentes graves evitados en 3 escalas."""
    escalas = ["Las 3 vías", "Los 12 corredores", "Toda la ciudad"]
    fig, axs = plt.subplots(1, 2, figsize=(12, 3.9), sharey=True)
    for ax, (var, color) in zip(axs, [("incidentes graves", AZUL), ("muertes", ROJO)]):
        d = t[t["qué"] == var].set_index("escala").reindex(escalas)
        y = np.arange(len(escalas))[::-1]
        ax.barh(y, d["%"], color=color, height=0.55, alpha=0.9)
        ax.hlines(y, d["% p5"], d["% p95"], color=TINTA, lw=1.4)
        for yi, (v, b, e) in zip(y, zip(d["%"], d["por año"], d["evitados"])):
            ax.text(d["% p95"].max() * 1.04, yi, f"{v:.0f}%  ·  {e:,.0f} de {b:,.0f} al año".replace(",", ".")
                    if var == "incidentes graves" else f"{v:.0f}%  ·  {e:.1f} de {b:.0f} al año".replace(".", ","),
                    va="center", fontsize=9.5, color=TINTA)
        ax.set_xlim(0, d["% p95"].max() * 1.75); ax.set_yticks(y, escalas)
        ax.set_title(f"{var.capitalize()} que se evitan", loc="left", fontsize=11.5, color=TINTA)
        ax.set_xlabel("% del total de cada escala")
        _estilo(ax, eje="x")
    g3 = t[(t["qué"] == "incidentes graves") & (t["escala"] == "Las 3 vías")]["%"].iloc[0]
    _titulo(fig, f"Tocando solo 3 vías se evitaría el {g3:.0f}% de sus incidentes graves, no solo muertes",
            "Las dos medidas juntas (notebook 06). Barra = mediana; línea = intervalo de 90%. Base: promedio anual 2019–2024.")
    fig.subplots_adjust(left=0.13, right=0.98, top=0.8, bottom=0.14, wspace=0.12)
    return fig


def lo_que_cambia(evita: pd.DataFrame, comp: pd.DataFrame, km: float):
    """Las cifras de la propuesta como tarjetas: vidas, heridos graves, 10 años y costo en tiempo.
    evita = historia.lo_que_se_evita(); comp = historia.comparacion(); km = largo de las 3 vías."""
    tot = comp.loc[("Total 3 vías", "Las dos juntas")]
    seg = comp.xs("Tope de 50", level="medida")["segundos por viaje (día)"].drop("Total 3 vías", errors="ignore")
    g3 = evita[(evita["qué"] == "incidentes graves") & (evita["escala"] == "Las 3 vías")].iloc[0]
    m3 = evita[(evita["qué"] == "muertes") & (evita["escala"] == "Las 3 vías")].iloc[0]
    coma = lambda v, d=1: f"{v:.{d}f}".replace(".", ",")
    miles = lambda v: f"{v:,.0f}".replace(",", ".")
    tarjetas = [
        (coma(tot["muertes evitadas/año"]), "vidas salvadas al año",
         f"entre {coma(tot['muertes p5'])} y {coma(tot['muertes p95'])}\n1 de cada {100 / m3['%']:.0f} muertes en esas vías", ROJO),
        (miles(tot["graves evitados/año"]), "incidentes graves menos al año",
         f"1 de cada {100 / g3['%']:.0f} en esas vías\nchoques con heridos o muertos que no ocurren", AZUL),
        (f"~{tot['muertes evitadas/año'] * 10:.0f}", "vidas en 10 años",
         f"y unos {miles(round(tot['graves evitados/año'] * 10, -2))} incidentes graves menos\nsi se mantienen las medidas", VERDE),
        (f"{seg.max():.0f} s", "el mayor costo por viaje",
         f"en la Regional; {seg.min():.0f} a {seg.drop(seg.idxmax()).max():.0f} s en las autopistas\nmenos de un minuto por viaje", NARANJA),
    ]
    fig, axs = plt.subplots(1, 4, figsize=(14, 3.6))
    for ax, (cifra, que, detalle, color) in zip(axs, tarjetas):
        ax.axis("off")
        ax.add_patch(FancyBboxPatch((0.02, 0.04), 0.96, 0.9, boxstyle="round,pad=0,rounding_size=0.06",
                                    transform=ax.transAxes, fc=color, ec="none", alpha=0.12))
        ax.add_patch(FancyBboxPatch((0.02, 0.04), 0.03, 0.9, boxstyle="square,pad=0", transform=ax.transAxes,
                                    fc=color, ec="none"))
        ax.text(0.12, 0.7, cifra, transform=ax.transAxes, fontsize=30, weight="bold", color=TINTA, va="center")
        ax.text(0.12, 0.46, que, transform=ax.transAxes, fontsize=11.5, weight="bold", color=TINTA, va="center")
        ax.text(0.12, 0.22, detalle, transform=ax.transAxes, fontsize=9.5, color=TINTA_2, va="center", linespacing=1.4)
    _titulo(fig, f"Con solo {coma(km)} km de vía intervenidos: 1 de cada 4 muertes e incidentes graves de esas vías",
            "Las dos medidas juntas, mediana del Monte Carlo (notebook 06). Base: promedio anual 2019–2024.")
    fig.subplots_adjust(left=0.005, right=0.995, top=0.8, bottom=0.02, wspace=0.05)
    return fig
