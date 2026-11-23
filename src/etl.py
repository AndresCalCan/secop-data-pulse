"""
SECOP II ETL Pipeline
Extracts, transforms, and loads Colombian public contract data from Datos Abiertos Colombia (SODA API).
"""

import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import requests

API_ENDPOINT = "https://www.datos.gov.co/resource/jbjy-vk9h.json"

COLUMNS_OF_INTEREST = [
    "id_contrato",
    "referencia_del_contrato",
    "nombre_entidad",
    "nit_entidad",
    "departamento",
    "ciudad",
    "sector",
    "modalidad_de_contratacion",
    "tipo_de_contrato",
    "proveedor_adjudicado",
    "documento_proveedor",
    "valor_del_contrato",
    "fecha_de_firma",
    "fecha_de_inicio_del_contrato",
    "fecha_de_fin_del_contrato",
    "objeto_del_contrato",
    "estado_contrato"
]


def fetch_contracts(
    departamento: Optional[str] = None,
    modalidad: Optional[str] = None,
    limit: int = 1000
) -> List[Dict[str, Any]]:
    """
    Extracts contracts from Socrata (SODA) API using SoQL query parameters.
    """
    params = {
        "$limit": limit,
        "$order": "fecha_de_firma DESC",
        "$select": ",".join(COLUMNS_OF_INTEREST)
    }
    
    where_clauses = ["valor_del_contrato IS NOT NULL"]
    if departamento and departamento != "Todos":
        where_clauses.append(f"departamento = '{departamento}'")
    if modalidad and modalidad != "Todas":
        where_clauses.append(f"modalidad_de_contratacion = '{modalidad}'")
        
    if where_clauses:
        params["$where"] = " AND ".join(where_clauses)

    response = requests.get(API_ENDPOINT, params=params, timeout=20)
    response.raise_for_status()
    return response.json()


def transform_contracts(raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Cleans raw API data, formats dates, and normalizes numeric contract values.
    """
    if not raw_data:
        return pd.DataFrame(columns=COLUMNS_OF_INTEREST)

    df = pd.DataFrame(raw_data)

    # Convert numeric fields
    if "valor_del_contrato" in df.columns:
        df["valor_del_contrato"] = pd.to_numeric(df["valor_del_contrato"], errors="coerce").fillna(0.0)

    # Parse date columns
    date_cols = ["fecha_de_firma", "fecha_de_inicio_del_contrato", "fecha_de_fin_del_contrato"]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Clean text columns
    text_cols = ["nombre_entidad", "departamento", "ciudad", "sector", "proveedor_adjudicado", "modalidad_de_contratacion"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()

    return df


def save_to_sqlite(df: pd.DataFrame, db_path: str = "data/secop_contracts.db") -> int:
    """
    Loads transformed contracts into a local SQLite database for fast analytical queries.
    """
    import os
    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        df.to_sql("contracts", conn, if_exists="replace", index=False)
    return len(df)
