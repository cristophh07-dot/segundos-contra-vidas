"""
src/utilidades.py — funciones pequeñas que usan varios módulos y notebooks.
"""
from __future__ import annotations

import re
import unicodedata

import pandas as pd


def _arreglar_texto(s: str) -> str:
    """Corrige textos mal decodificados ("AÃ±o" -> "Año")."""
    for codif in ("latin-1", "cp1252"):
        try:
            return s.encode(codif).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return s


def normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Nombres de columnas uniformes: minúscula, sin tildes, con guion bajo ("Año" -> "ano")."""
    nuevas = []
    for c in df.columns:
        c = unicodedata.normalize("NFKD", _arreglar_texto(str(c))).encode("ascii", "ignore").decode()
        nuevas.append(re.sub(r"[^0-9a-z]+", "_", c.lower()).strip("_"))
    df.columns = nuevas
    return df
