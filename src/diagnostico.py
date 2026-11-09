"""src/diagnostico.py — tablas y figuras del diagnóstico (Tareas 4 y 5)."""
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams.update({"font.size": 14, "axes.labelsize": 14, "xtick.labelsize": 12, "ytick.labelsize": 12})

from src import seguridad as seg

FIG = pathlib.Path("figuras")
FIG.mkdir(exist_ok=True)
TAB = pathlib.Path("data/processed")
ROJO, NARANJA, GRIS, AZUL = "#C0392B", "#E67E22", "#95A5A6", "#2C3E50"
DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


def _cargar(nombre, funcion):
    ruta = TAB / f"{nombre}.csv"
    return pd.read_csv(ruta) if ruta.exists() else funcion()


def datos():
    inc = _cargar("incidentes_limpios", seg.incidentes_limpios)
    vic = _cargar("victimas_limpias", seg.victimas_limpias)
    mor = _cargar("mortalidad_distrito", seg.mortalidad_distrito)
    for d in (inc, vic, mor):
        d["fecha"] = pd.to_datetime(d["fecha"])
    vic["anio"] = vic["fecha"].dt.year
    vic["dia_semana"] = vic["fecha"].dt.day_of_week
    mor["anio"] = mor["fecha"].dt.year
    return inc, vic, mor


def _fig(ncols=1):
    fig, axs = plt.subplots(1, ncols, figsize=(16, 9))
    return fig, axs


def _guardar(fig, nombre):
    fig.tight_layout()
    fig.savefig(FIG / nombre, dpi=100)
    plt.close(fig)
    print("figura guardada:", nombre)


def _tasa_muerte(s):
    return (s == "muerto").mean() * 100


# 01 ---------------------------------------------------------------
def fig_tendencia(inc, vic, mor):
    itm = inc[(inc.gravedad == "muerto") & (inc.anio < 2025)].groupby("anio").size()
    v = vic[(vic.gravedad_victima == "muerto") & (vic.anio < 2021)].groupby("anio").size()
    m = mor.groupby("anio").size()

    comp = pd.DataFrame({"itm_incidentes_con_muerto": itm, "distrito_fallecidos": m}).dropna()
    comp["cobertura_itm"] = comp.itm_incidentes_con_muerto / comp.distrito_fallecidos
    comp.to_csv(TAB / "diag_itm_vs_distrito.csv")
    print(comp.round(2).to_string())

    fig, ax = _fig()
    ax.plot(itm.index, itm.values, marker="o", color=AZUL, lw=3, label="Base del ITM (incidentes con muerto)")
    ax.plot(v.index, v.values, marker="s", color=ROJO, lw=3, label="MEData víctimas (muertos)")
    ax.plot(m.index, m.values, marker="^", color=NARANJA, lw=3, label="Capa de mortalidad del Distrito (fallecidos)")
    ax.set_xlabel("Año")
    ax.set_ylabel("Muertos por año")
    ax.legend(fontsize=14)
    ax.grid(alpha=.3)
    ax.set_title(f"La base del ITM registra entre {comp.cobertura_itm.min():.0%} y "
                 f"{comp.cobertura_itm.max():.0%} de los muertos oficiales (2019–2024)", fontsize=20)
    _guardar(fig, "01_tendencia_muertos.png")


# 02 ---------------------------------------------------------------
def fig_hora_incidentes(inc):
    g = inc[inc.gravedad.isin(["herido", "muerto"])].dropna(subset=["hora"])
    c = g.groupby("hora").size().reindex(range(24), fill_value=0)
    fig, ax = _fig()
    ax.bar(c.index, c.values, color=AZUL)
    ax.set_xticks(range(24))
    ax.set_xlabel("Hora del día (0–23)")
    ax.set_ylabel("Incidentes graves (2008–2025)")
    ax.set_title(f"La hora con más incidentes graves es las {int(c.idxmax())}:00 "
                 f"({c.max():,} en 2008–2025)", fontsize=20)
    _guardar(fig, "02_incidentes_graves_por_hora.png")


# 03 ---------------------------------------------------------------
def fig_hora_letalidad(vic):
    v = vic.dropna(subset=["hora"])
    t = v.groupby("hora").gravedad_victima.apply(_tasa_muerte).reindex(range(24))
    ln = _tasa_muerte(v[v.hora <= 5].gravedad_victima) / 100
    ld = _tasa_muerte(v[(v.hora >= 6) & (v.hora <= 17)].gravedad_victima) / 100
    fig, ax = _fig()
    ax.bar(t.index, t.values, color=ROJO)
    ax.set_xticks(range(24))
    ax.set_xlabel("Hora del día (0–23)")
    ax.set_ylabel("Muertos por cada 100 víctimas")
    ax.set_title(f"De madrugada (0–5 h) 1 de cada {round(1/ln)} víctimas muere; "
                 f"de día (6–17 h), 1 de cada {round(1/ld)}", fontsize=20)
    _guardar(fig, "03_letalidad_por_hora.png")
    print(f"Letalidad madrugada {ln:.2%} | día {ld:.2%} | razón {ln/ld:.1f}x")


# 04 ---------------------------------------------------------------
def fig_dia_semana(vic):
    t = vic.groupby("dia_semana").gravedad_victima.apply(_tasa_muerte).reindex(range(7))
    n = vic.groupby("dia_semana").size().reindex(range(7))
    fig, ax = _fig()
    ax.bar([DIAS[i] for i in t.index], t.values, color=ROJO)
    ax.set_xlabel("Día de la semana")
    ax.set_ylabel("Muertos por cada 100 víctimas")
    ax.set_title(f"El {DIAS[int(t.idxmax())]} es el día más letal: {t.max():.1f} muertos por cada 100 víctimas",
                 fontsize=20)
    _guardar(fig, "04_letalidad_por_dia.png")
    print("Víctimas por día:", dict(zip(DIAS, n.astype(int).tolist())))


# 05 ---------------------------------------------------------------
def fig_actor(vic):
    mapa = {"conductor_moto": "Moto", "parrillero": "Moto", "peaton": "Peatón",
            "ciclista": "Ciclista", "conductor_carro": "Carro y pasajero", "pasajero": "Carro y pasajero"}
    v = vic.assign(actor=vic.condicion.map(mapa)).dropna(subset=["actor"])
    res = v.groupby("actor").agg(victimas=("gravedad_victima", "size"),
                                 muertos=("gravedad_victima", lambda s: (s == "muerto").sum()))
    res["letalidad_por_100"] = res.muertos / res.victimas * 100
    res = res.sort_values("victimas", ascending=False)
    res.to_csv(TAB / "diag_actor.csv")
    print(res.round(2).to_string())

    moto = res.loc["Moto", "victimas"] / res.victimas.sum()
    top = res.letalidad_por_100.idxmax()
    fig, (a1, a2) = _fig(2)
    a1.bar(res.index, res.victimas, color=AZUL)
    a1.set_ylabel("Víctimas (2014–sep. 2021)")
    a2.bar(res.index, res.letalidad_por_100, color=ROJO)
    a2.set_ylabel("Muertos por cada 100 víctimas")
    for a in (a1, a2):
        a.set_xlabel("Actor vial")
    fig.suptitle(f"{moto:.0%} de las víctimas iba en moto, pero el actor más letal es: {top.lower()}", fontsize=20)
    _guardar(fig, "05_victimas_y_letalidad_por_actor.png")


# 06 ---------------------------------------------------------------
def fig_mapa(mor):
    d = mor.dropna(subset=["lat", "lon"])
    fig, ax = _fig()
    hb = ax.hexbin(d.lon, d.lat, gridsize=35, cmap="Reds", mincnt=1)
    cuentas = np.sort(hb.get_array())[::-1]
    k = max(1, int(round(len(cuentas) * 0.10)))
    p = cuentas[:k].sum() / cuentas.sum()
    ax.set_aspect("equal")
    ax.set_xlabel("Longitud (grados)")
    ax.set_ylabel("Latitud (grados)")
    fig.colorbar(hb, ax=ax).set_label("Muertos por celda")
    print(f"Mapa: el 10 % de celdas con más muertes concentra {p:.0%} de {len(d)} fallecidos")
    ax.set_title(f"Entre las celdas con al menos un muerto, el 10 % con más muertes concentra el {p:.0%} "
                 f"de los {len(d):,} fallecidos (2019–2024)", fontsize=18)
    _guardar(fig, "06_mapa_muertos_2019_2024.png")


def generar_todo():
    inc, vic, mor = datos()
    fig_tendencia(inc, vic, mor)
    fig_hora_incidentes(inc)
    fig_hora_letalidad(vic)
    fig_dia_semana(vic)
    fig_actor(vic)
    fig_mapa(mor)


if __name__ == "__main__":
    generar_todo()