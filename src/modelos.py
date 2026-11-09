"""
src/modelos.py — modelos de Cristopher: logística, exponente, predicción, Monte Carlo y backtest.
Todo se lee con src.descarga.leer() desde las URLs de src/fuentes.py.

Por ahora contiene la regresión logística (notebook 02, decisiones D12, D16, D22 y D24):
- preparar_victimas(): el archivo de víctimas limpio y con las variables del modelo.
- modelo_logistico(): el modelo principal (D22) o el de predicción validado (D24).
- tabla_or(): odds ratios con IC 95%.
- validar_logistico(): entrena con 2014–2019 y prueba con 2020–2021 (AUC, Brier, calibración).
- probabilidad_perfiles(): probabilidad de morir según el perfil de la víctima.

Backtest de la cuarentena (notebook 04, D26):
- velocidad_cuarentena(): cuánto se aceleró cada corredor (20 mar – 31 ago 2020 vs 2017–2019).
- oe_periodos(), placebos_cuarentena(), oe_por_actor(), oe_dia(): muertos observados / esperados.
- exponente_implicito(): el exponente de la letalidad que implica el exceso, frente a Nilsson.
- hospitales_cuarentena(): ¿subieron las muertes en centros asistenciales?
- backtest(): todo lo anterior en un solo llamado (para el notebook final).

Uso desde un notebook:
    from src.modelos import preparar_victimas, modelo_logistico, tabla_or
    m = preparar_victimas()
    modelo = modelo_logistico(m)                       # principal (D22)
    pred = modelo_logistico(m, tipo="prediccion")      # para el Monte Carlo y el backtest (D24)
    bt = backtest(m)                                   # diccionario con todas las tablas del backtest

Pruebas (desde la carpeta principal del repo):  python -m src.modelos
"""
from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sklearn.metrics import brier_score_loss, roc_auc_score

from scipy import stats

from src.descarga import leer
from src.utilidades import normalizar_columnas

PROCESSED = pathlib.Path("data/processed")

CUARENTENA = ("2020-03-20", "2020-08-31")
RAPIDAS = ["AV_REGIONAL", "AUT_NORTE", "AUT_SUR", "AV_PALMAS"]        # D18

# D22: modelo principal. La clase de incidente va solo como sensibilidad (casi coincide con el actor).
FORMULA_PRINCIPAL = (
    "muerto ~ C(actor, Treatment('Moto')) + C(grupo_edad, Treatment('20-29'))"
    " + C(sexo, Treatment('M')) + C(franja, Treatment('dia (6-17)'))"
    " + fin_de_semana + cuarentena + C(ano_c)"
)
# D24: modelo de predicción. Sin año ni cuarentena, porque no se pueden estimar para años nuevos.
FORMULA_PREDICCION = (
    "muerto ~ C(actor, Treatment('Moto')) + C(grupo_edad, Treatment('20-29'))"
    " + C(sexo, Treatment('M')) + C(franja, Treatment('dia (6-17)')) + fin_de_semana"
)

PERFILES = pd.DataFrame([
    ("Moto · 20-29 · de día",     "Moto",     "20-29", "M", "dia (6-17)"),
    ("Moto · 20-29 · madrugada",  "Moto",     "20-29", "M", "madrugada (0-5)"),
    ("Ciclista · 30-44 · de día", "Ciclista", "30-44", "M", "dia (6-17)"),
    ("Peatón · 30-44 · de día",   "Peatón",   "30-44", "M", "dia (6-17)"),
    ("Peatón · 60+ · de día",     "Peatón",   "60+",   "M", "dia (6-17)"),
    ("Peatón · 60+ · madrugada",  "Peatón",   "60+",   "M", "madrugada (0-5)"),
], columns=["perfil", "actor", "grupo_edad", "sexo", "franja"])


# ---------------------------------------------------------------------------------------------
# Regresión logística (notebook 02)
# ---------------------------------------------------------------------------------------------
def preparar_victimas() -> pd.DataFrame:
    """Víctimas listas para el modelo (D12): solo las filas reales, sexo M/F y sin faltantes.

    Columnas: muerto, actor, grupo_edad, sexo, franja, fin_de_semana, cuarentena, ano_c, clase,
    incidente (para agrupar los errores por radicado), ano, edad, fecha, hora.
    """
    vic = normalizar_columnas(leer("victimas_medata"))
    vic = vic[vic["ano"].notna()].copy()                      # el archivo trae ~800 mil filas vacías

    vic["fecha"] = pd.to_datetime(vic["fecha_incidente"], dayfirst=True, errors="coerce")
    vic["hora"] = pd.to_numeric(vic["hora"], errors="coerce")
    vic["edad"] = pd.to_numeric(vic["edad"], errors="coerce")
    vic["ano"] = vic["ano"].astype(int)
    vic["muerto"] = (vic["gravedad_victima"] == "Muertos").astype(int)

    vic["condicion"] = vic["condicion"].replace({"Acompañante de Motocicleta": "Acompañante de motocicleta"})
    vic["actor"] = vic["condicion"].replace({"Motociclista": "Moto", "Acompañante de motocicleta": "Moto"})

    vic["grupo_edad"] = pd.cut(vic["edad"], [0, 19, 29, 44, 59, 120], labels=["<20", "20-29", "30-44", "45-59", "60+"])
    vic["franja"] = pd.cut(vic["hora"], [-1, 5, 17, 23], labels=["madrugada (0-5)", "dia (6-17)", "noche (18-23)"])
    vic["fin_de_semana"] = (vic["fecha"].dt.dayofweek >= 5).astype(int)
    vic["cuarentena"] = vic["fecha"].between(*CUARENTENA).astype(int)
    vic["ano_c"] = vic["ano"].astype(str)

    # Clases con pocos casos se agrupan en "Otro"
    frec = vic["clase_incidente"].value_counts()
    vic["clase"] = vic["clase_incidente"].where(vic["clase_incidente"].isin(frec[frec >= 1000].index), "Otro")

    # Víctimas del mismo incidente comparten radicado: se usa para los errores agrupados (D22)
    sin_radicado = pd.Series("sin_" + vic.index.astype(str), index=vic.index)
    vic["incidente"] = pd.factorize(vic["radicado"].astype(str).where(vic["radicado"].notna(), sin_radicado))[0]

    usadas = ["muerto", "actor", "grupo_edad", "sexo", "franja", "fin_de_semana", "cuarentena", "ano_c", "clase", "incidente"]
    m = vic[vic["sexo"].isin(["M", "F"])].dropna(subset=usadas)
    return m[usadas + ["ano", "edad", "fecha", "hora"]].reset_index(drop=True)


def modelo_logistico(datos: pd.DataFrame | None = None, tipo: str = "principal", hasta: int = 2019,
                     excluir: int | None = None):
    """Ajusta la regresión logística de la probabilidad de morir.

    tipo="principal"  (D22): todas las víctimas, con año y cuarentena, errores agrupados por radicado.
                             Es el que se interpreta (odds ratios).
    tipo="prediccion" (D24): entrenado con las víctimas hasta `hasta` (2019), sin año ni cuarentena.
                             Es el que se usa para predecir (Monte Carlo y backtest).
                             `excluir` deja un año fuera del entrenamiento (placebos del backtest).
    """
    m = preparar_victimas() if datos is None else datos
    if tipo == "principal":
        return smf.logit(FORMULA_PRINCIPAL, data=m).fit(
            disp=0, cov_type="cluster", cov_kwds={"groups": m["incidente"]})
    if tipo == "prediccion":
        entreno = m[(m["ano"] <= hasta) & (m["ano"] != excluir)]
        return smf.logit(FORMULA_PREDICCION, data=entreno).fit(disp=0)
    raise ValueError("tipo debe ser 'principal' o 'prediccion'")


def tabla_or(res) -> pd.DataFrame:
    """Odds ratios con IC 95% y p, con nombres legibles ("actor = Peatón")."""
    ic = res.conf_int()
    t = pd.DataFrame({"OR": np.exp(res.params), "IC95_inf": np.exp(ic[0]),
                      "IC95_sup": np.exp(ic[1]), "p": res.pvalues}).drop("Intercept")
    t.index = t.index.str.replace(r"C\((\w+).*\[T\.(.+)\]$", r"\1 = \2", regex=True)
    return t


def validar_logistico(datos: pd.DataFrame | None = None, hasta: int = 2019) -> dict:
    """Entrena con las víctimas hasta `hasta` y prueba con los años siguientes (D24).

    Devuelve: n_entreno, n_prueba, auc, auc_solo_actor, brier, brier_sin_modelo,
    esperados, observados y calibracion (DataFrame por deciles de riesgo, en %).
    """
    m = preparar_victimas() if datos is None else datos
    entreno, prueba = m[m["ano"] <= hasta], m[m["ano"] > hasta]
    mod = modelo_logistico(m, tipo="prediccion", hasta=hasta)
    p = mod.predict(prueba)
    p_actor = smf.logit("muerto ~ C(actor)", data=entreno).fit(disp=0).predict(prueba)

    cal = pd.DataFrame({"pred": p, "obs": prueba["muerto"]})
    cal["decil"] = pd.qcut(cal["pred"].rank(method="first"), 10, labels=False) + 1
    cal = cal.groupby("decil").agg(pred_pct=("pred", "mean"), obs_pct=("obs", "mean"), n=("obs", "size"))
    cal[["pred_pct", "obs_pct"]] *= 100

    return {
        "n_entreno": len(entreno), "n_prueba": len(prueba),
        "auc": roc_auc_score(prueba["muerto"], p),
        "auc_solo_actor": roc_auc_score(prueba["muerto"], p_actor),
        "brier": brier_score_loss(prueba["muerto"], p),
        "brier_sin_modelo": brier_score_loss(prueba["muerto"], np.full(len(prueba), entreno["muerto"].mean())),
        "esperados": float(p.sum()), "observados": int(prueba["muerto"].sum()),
        "calibracion": cal,
    }


def probabilidad_perfiles(modelo, perfiles: pd.DataFrame | None = None, ano: str = "2019") -> pd.DataFrame:
    """Probabilidad de morir (%) y "1 de cada N" para cada perfil (hombre, entre semana, sin cuarentena)."""
    t = (PERFILES if perfiles is None else perfiles).copy()
    t["fin_de_semana"], t["cuarentena"], t["ano_c"] = 0, 0, ano
    t["prob_%"] = modelo.predict(t) * 100
    t["1_de_cada"] = (100 / t["prob_%"]).round(0).astype(int)
    return t


# ---------------------------------------------------------------------------------------------
# Backtest de la cuarentena (notebook 04, D26)
# ---------------------------------------------------------------------------------------------
PERIODOS = {
    "2020 antes (1 ene – 19 mar)":  ("2020-01-01", "2020-03-19"),
    "Cuarentena (20 mar – 31 ago)": CUARENTENA,
    "Reapertura (sep – dic 2020)":  ("2020-09-01", "2020-12-31"),
    "2021 (ene – sep)":             ("2021-01-01", "2021-09-30"),
}
ANOS_PLACEBO = range(2015, 2020)


def misma_ventana(fechas: pd.Series, ano: int) -> pd.Series:
    """True si la fecha cae entre el 20 de marzo y el 31 de agosto del año indicado."""
    inicio, fin = (pd.Timestamp(f).replace(year=ano) for f in CUARENTENA)
    return fechas.between(inicio, fin)


def o_sobre_e(obs: int, esp: float) -> dict:
    """O/E con IC 95% exacto de Poisson para O, y p de la prueba O ~ Poisson(E)."""
    lo = stats.chi2.ppf(0.025, 2 * obs) / 2 if obs > 0 else 0.0
    hi = stats.chi2.ppf(0.975, 2 * (obs + 1)) / 2
    p = min(1.0, 2 * min(stats.poisson.cdf(obs, esp), stats.poisson.sf(obs - 1, esp)))
    return {"observados": int(obs), "esperados": esp, "O/E": obs / esp,
            "IC95_inf": lo / esp, "IC95_sup": hi / esp, "p": p}


def velocidad_cuarentena() -> tuple[pd.DataFrame, dict]:
    """Velocidad de Google Traffic por corredor: 20 mar – 31 ago 2020 contra las mismas fechas de 2017–2019.

    Devuelve la tabla por corredor y la razón (media geométrica) para todos, vías rápidas y arterias.
    """
    from src.velocidad import tiempo_viaje_gt

    tv = tiempo_viaje_gt()
    tv["fecha"] = pd.to_datetime(tv["fecha"])
    tv["ano"] = tv["fecha"].dt.year
    tv = tv[tv["velocidad_gt_kmh"] > 0]

    en_ventana = pd.concat([misma_ventana(tv["fecha"], a) for a in range(2017, 2021)], axis=1).any(axis=1)
    v = tv[en_ventana].assign(periodo=np.where(tv.loc[en_ventana, "ano"] == 2020, "cuarentena", "2017_2019"))
    por_corr = v.groupby(["corredor_id", "periodo"])["velocidad_gt_kmh"].mean().unstack()
    por_corr["razon"] = por_corr["cuarentena"] / por_corr["2017_2019"]
    por_corr["tipo"] = np.where(por_corr.index.isin(RAPIDAS), "vías rápidas", "arterias")

    def media_geo(s):
        return float(np.exp(np.log(s).mean()))

    razon = {"todos": media_geo(por_corr["razon"]),
             "vías rápidas": media_geo(por_corr.loc[por_corr["tipo"] == "vías rápidas", "razon"]),
             "arterias": media_geo(por_corr.loc[por_corr["tipo"] == "arterias", "razon"])}
    return por_corr.sort_values("razon", ascending=False), razon


def oe_periodos(m: pd.DataFrame, modelo) -> pd.DataFrame:
    """Muertos observados / esperados en 2020 antes, cuarentena, reapertura y 2021."""
    filas = []
    for nombre, (ini, fin) in PERIODOS.items():
        d = m[m["fecha"].between(ini, fin)]
        filas.append({"periodo": nombre, "victimas": len(d), **o_sobre_e(d["muerto"].sum(), modelo.predict(d).sum())})
    return pd.DataFrame(filas).set_index("periodo")


def placebos_cuarentena(m: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """O/E de los mismos meses de 2015–2019, cada año predicho con un modelo entrenado sin él."""
    filas, mods = [], {}
    for ano in ANOS_PLACEBO:
        mods[ano] = modelo_logistico(m, tipo="prediccion", excluir=ano)
        d = m[misma_ventana(m["fecha"], ano)]
        filas.append({"periodo": f"Placebo {ano}", "victimas": len(d),
                      **o_sobre_e(d["muerto"].sum(), mods[ano].predict(d).sum())})
    return pd.DataFrame(filas).set_index("periodo"), mods


def _oe_filtro(m, modelo, mods, filtro) -> tuple[dict, dict, int, int]:
    """O/E de la cuarentena y de los placebos juntos para las víctimas que cumplen `filtro`."""
    obs = esp = n = 0
    for ano, mod in mods.items():
        d = m[misma_ventana(m["fecha"], ano) & filtro]
        obs, esp, n = obs + d["muerto"].sum(), esp + mod.predict(d).sum(), n + len(d)
    c = m[m["fecha"].between(*CUARENTENA) & filtro]
    return o_sobre_e(obs, esp), o_sobre_e(c["muerto"].sum(), modelo.predict(c).sum()), n, len(c)


def oe_por_actor(m: pd.DataFrame, modelo, mods: dict, actores=("Moto", "Peatón")) -> pd.DataFrame:
    """O/E por actor: placebos 2015–2019 juntos y cuarentena (D19)."""
    filas = []
    for actor in actores:
        pla, cua, n_pla, n_cua = _oe_filtro(m, modelo, mods, m["actor"] == actor)
        filas.append({"actor": actor, "periodo": "Placebos 2015–2019", "victimas": n_pla, **pla})
        filas.append({"actor": actor, "periodo": "Cuarentena 2020", "victimas": n_cua, **cua})
    return pd.DataFrame(filas).set_index(["actor", "periodo"])


def oe_dia(m: pd.DataFrame, modelo, mods: dict) -> pd.DataFrame:
    """O/E solo de 6:00 a 20:00, la ventana que mide Google Traffic."""
    pla, cua, _, _ = _oe_filtro(m, modelo, mods, m["hora"].between(6, 20))
    return pd.DataFrame([{"periodo": "Placebos 2015–2019 · 6–20 h", **pla},
                         {"periodo": "Cuarentena · 6–20 h", **cua}]).set_index("periodo")


def exponente_implicito(oe: pd.DataFrame, por_actor: pd.DataFrame, dia: pd.DataFrame, razon: dict) -> pd.DataFrame:
    """β = ln(O/E) / ln(r): el exponente de la letalidad que implica el exceso. Nilsson predice O/E = r²."""
    def fila(f, r):
        return {"β implícito": np.log(f["O/E"]) / np.log(r),
                "β IC95_inf": np.log(max(f["IC95_inf"], 1e-9)) / np.log(r),
                "β IC95_sup": np.log(f["IC95_sup"]) / np.log(r),
                "O/E observado": f["O/E"], "O/E si Nilsson (r²)": r ** 2}

    c = oe.loc["Cuarentena (20 mar – 31 ago)"]
    r = razon["todos"]
    filas = [{"víctimas": "todas", "velocidad": k, "r": rk, **fila(c, rk)} for k, rk in razon.items()]
    filas.append({"víctimas": "6–20 h", "velocidad": "todos", "r": r, **fila(dia.loc["Cuarentena · 6–20 h"], r)})
    for a in por_actor.index.get_level_values("actor").unique():
        filas.append({"víctimas": a, "velocidad": "todos", "r": r, **fila(por_actor.loc[(a, "Cuarentena 2020")], r)})
    return pd.DataFrame(filas).set_index(["víctimas", "velocidad"])


def hospitales_cuarentena() -> tuple[pd.DataFrame, float]:
    """Muertos del Distrito por lugar (20 mar – 31 ago de 2019 a 2024) y p de Fisher de 2020 contra el resto."""
    mort = normalizar_columnas(leer("mortalidad_distrito"))
    mort["fecha"] = pd.to_datetime(mort["fecha_ocurrencia"], dayfirst=True, errors="coerce")
    mort["ano"] = mort["fecha"].dt.year
    mort["lugar"] = mort["lugar_inspeccion"].astype(str).str.strip().replace(
        {"Vía Pública": "en la vía", "Centro Asistencial": "centro asistencial"})
    mort.loc[~mort["lugar"].isin(["en la vía", "centro asistencial"]), "lugar"] = "otro / sin dato"

    ventana = pd.concat([misma_ventana(mort["fecha"], a) for a in range(2019, 2025)], axis=1).any(axis=1)
    w = mort[ventana]
    lugar = pd.crosstab(w["ano"], w["lugar"])
    lugar["total"] = lugar.sum(axis=1)
    lugar["% en centro asistencial"] = (lugar.get("centro asistencial", 0) / lugar["total"] * 100).round(1)

    cuar = lugar.loc[2020]
    resto = lugar.drop(index=2020)[["centro asistencial", "total"]].sum()
    tabla = [[cuar["centro asistencial"], cuar["total"] - cuar["centro asistencial"]],
             [resto["centro asistencial"], resto["total"] - resto["centro asistencial"]]]
    return lugar, float(stats.fisher_exact(tabla)[1])


def backtest(datos: pd.DataFrame | None = None) -> dict:
    """Backtest completo de la cuarentena (D26). Devuelve un diccionario con:
    velocidad, razon, oe, placebos, por_actor, dia, exponente, hospitales, p_hospitales.
    """
    m = preparar_victimas() if datos is None else datos
    velocidad, razon = velocidad_cuarentena()
    modelo = modelo_logistico(m, tipo="prediccion")
    oe = oe_periodos(m, modelo)
    placebos, mods = placebos_cuarentena(m)
    por_actor = oe_por_actor(m, modelo, mods)
    dia = oe_dia(m, modelo, mods)
    hospitales, p_hosp = hospitales_cuarentena()
    return {"velocidad": velocidad, "razon": razon, "oe": oe, "placebos": placebos,
            "por_actor": por_actor, "dia": dia,
            "exponente": exponente_implicito(oe, por_actor, dia, razon),
            "hospitales": hospitales, "p_hospitales": p_hosp}


# ---------------------------------------------------------------------------------------------
# Pruebas de aceptación: deben reproducir las cifras del notebook 02 con los datos reales.
# ---------------------------------------------------------------------------------------------
if __name__ == "__main__":
    PROCESSED.mkdir(parents=True, exist_ok=True)
    m = preparar_victimas()
    print(f"Víctimas para el modelo: {len(m):,} · muertos: {m['muerto'].sum():,}")
    assert len(m) == 230_157 and m["muerto"].sum() == 1_887, "No coincide con el notebook 02 (230.157 y 1.887)"

    modelo = modelo_logistico(m)
    ors = tabla_or(modelo)
    ors.to_csv(PROCESSED / "or_logistico.csv", encoding="utf-8")
    claves = {"grupo_edad = 60+": 5.74, "actor = Peatón": 3.38, "franja = madrugada (0-5)": 3.21,
              "actor = Ciclista": 2.78, "sexo = F": 0.54}
    print("\nOR principales (D22):")
    for k, esperado in claves.items():
        print(f"  {k}: {ors.loc[k, 'OR']:.2f} (notebook 02: {esperado})")
        assert abs(ors.loc[k, "OR"] - esperado) < 0.01, f"OR distinto al del notebook 02: {k}"

    v = validar_logistico(m)
    print(f"\nValidación 2020–2021 (D24): AUC {v['auc']:.3f} · esperados {v['esperados']:.0f} · observados {v['observados']}")
    assert abs(v["auc"] - 0.760) < 0.001 and round(v["esperados"]) == 353 and v["observados"] == 357

    print("\n", probabilidad_perfiles(modelo)[["perfil", "prob_%", "1_de_cada"]].round(2).to_string(index=False))
    print("\nmodelos.py (logística): pruebas OK ✔")

    bt = backtest(m)
    c = bt["oe"].loc["Cuarentena (20 mar – 31 ago)"]
    print(f"\nBacktest (D26): velocidad ×{bt['razon']['todos']:.3f} · cuarentena O/E {c['O/E']:.3f} "
          f"({c['observados']} vs {c['esperados']:.1f}) · placebos {bt['placebos']['O/E'].min():.3f} a {bt['placebos']['O/E'].max():.3f}")
    assert abs(bt["razon"]["todos"] - 1.305) < 0.001, "La razón de velocidad no coincide con el notebook 04 (1,305)"
    assert c["observados"] == 70 and abs(c["esperados"] - 59.003) < 0.01, "El O/E no coincide con el notebook 04"
    assert abs(bt["placebos"]["O/E"].min() - 0.889) < 0.001 and abs(bt["placebos"]["O/E"].max() - 1.196) < 0.001
    print("modelos.py (backtest): pruebas OK ✔")
