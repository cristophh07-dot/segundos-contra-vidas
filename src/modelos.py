"""
src/modelos.py — modelos de Cristopher: logística, exponente, predicción, Monte Carlo y backtest.
Todo se lee con src.descarga.leer() desde las URLs de src/fuentes.py.

Por ahora contiene la regresión logística (notebook 02, decisiones D12, D16, D22 y D24):
- preparar_victimas(): el archivo de víctimas limpio y con las variables del modelo.
- modelo_logistico(): el modelo principal (D22) o el de predicción validado (D24).
- tabla_or(): odds ratios con IC 95%.
- validar_logistico(): entrena con 2014–2019 y prueba con 2020–2021 (AUC, Brier, calibración).
- probabilidad_perfiles(): probabilidad de morir según el perfil de la víctima.

Uso desde un notebook:
    from src.modelos import preparar_victimas, modelo_logistico, tabla_or
    m = preparar_victimas()
    modelo = modelo_logistico(m)                       # principal (D22)
    pred = modelo_logistico(m, tipo="prediccion")      # para el Monte Carlo y el backtest (D24)

Pruebas (desde la carpeta principal del repo):  python -m src.modelos
"""
from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sklearn.metrics import brier_score_loss, roc_auc_score

from src.descarga import leer
from src.utilidades import normalizar_columnas

PROCESSED = pathlib.Path("data/processed")

CUARENTENA = ("2020-03-20", "2020-08-31")

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


def modelo_logistico(datos: pd.DataFrame | None = None, tipo: str = "principal", hasta: int = 2019):
    """Ajusta la regresión logística de la probabilidad de morir.

    tipo="principal"  (D22): todas las víctimas, con año y cuarentena, errores agrupados por radicado.
                             Es el que se interpreta (odds ratios).
    tipo="prediccion" (D24): entrenado con las víctimas hasta `hasta` (2019), sin año ni cuarentena.
                             Es el que se usa para predecir (Monte Carlo y backtest).
    """
    m = preparar_victimas() if datos is None else datos
    if tipo == "principal":
        return smf.logit(FORMULA_PRINCIPAL, data=m).fit(
            disp=0, cov_type="cluster", cov_kwds={"groups": m["incidente"]})
    if tipo == "prediccion":
        return smf.logit(FORMULA_PREDICCION, data=m[m["ano"] <= hasta]).fit(disp=0)
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
