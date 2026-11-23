"""
Database Analytical Queries Module
Demonstrates practical SQL analytics (Window Functions, CTEs, Aggregations) on SECOP II contracts.
"""

import os
import sqlite3
import pandas as pd


def get_connection(db_path: str = "data/secop_contracts.db") -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
    return sqlite3.connect(db_path)


def get_kpi_summary(conn: sqlite3.Connection) -> dict:
    """Calculates high-level metrics for executive dashboard."""
    query = """
    SELECT 
        COUNT(*) as total_contratos,
        SUM(valor_del_contrato) as monto_total_cop,
        AVG(valor_del_contrato) as promedio_contrato_cop,
        MAX(valor_del_contrato) as mayor_contrato_cop
    FROM contracts
    """
    df = pd.read_sql_query(query, conn)
    if not df.empty and df["total_contratos"].iloc[0] > 0:
        return df.iloc[0].to_dict()
    return {
        "total_contratos": 0,
        "monto_total_cop": 0.0,
        "promedio_contrato_cop": 0.0,
        "mayor_contrato_cop": 0.0
    }


def get_top_entidades(conn: sqlite3.Connection, limit: int = 10) -> pd.DataFrame:
    """Uses GROUP BY and ORDER BY to get top public entities by spending."""
    query = f"""
    SELECT 
        nombre_entidad,
        COUNT(*) as cantidad_contratos,
        SUM(valor_del_contrato) as total_invertido_cop
    FROM contracts
    WHERE nombre_entidad IS NOT NULL AND nombre_entidad != 'NAN'
    GROUP BY nombre_entidad
    ORDER BY total_invertido_cop DESC
    LIMIT {limit}
    """
    return pd.read_sql_query(query, conn)


def get_top_contratistas_ranking(conn: sqlite3.Connection, limit: int = 10) -> pd.DataFrame:
    """
    Demonstrates SQL CTE (Common Table Expression) and Window Functions (DENSE_RANK)
    to rank contractors by awarded contract value.
    """
    query = f"""
    WITH ContratistasTotal AS (
        SELECT 
            proveedor_adjudicado,
            documento_proveedor,
            COUNT(*) as numero_adjudicaciones,
            SUM(valor_del_contrato) as total_adjudicado_cop
        FROM contracts
        WHERE proveedor_adjudicado IS NOT NULL 
          AND proveedor_adjudicado != 'NAN' 
          AND proveedor_adjudicado != ''
        GROUP BY proveedor_adjudicado, documento_proveedor
    )
    SELECT 
        DENSE_RANK() OVER (ORDER BY total_adjudicado_cop DESC) as ranking,
        proveedor_adjudicado,
        documento_proveedor,
        numero_adjudicaciones,
        total_adjudicado_cop
    FROM ContratistasTotal
    ORDER BY total_adjudicado_cop DESC
    LIMIT {limit}
    """
    return pd.read_sql_query(query, conn)


def get_distribucion_modalidad(conn: sqlite3.Connection) -> pd.DataFrame:
    """Aggregates spending and volume by procurement modality."""
    query = """
    SELECT 
        modalidad_de_contratacion,
        COUNT(*) as cantidad,
        SUM(valor_del_contrato) as monto_total
    FROM contracts
    WHERE modalidad_de_contratacion IS NOT NULL AND modalidad_de_contratacion != 'NAN'
    GROUP BY modalidad_de_contratacion
    ORDER BY monto_total DESC
    """
    return pd.read_sql_query(query, conn)


def get_gasto_por_departamento(conn: sqlite3.Connection) -> pd.DataFrame:
    """Calculates total contract spend grouped by Colombian department."""
    query = """
    SELECT 
        departamento,
        COUNT(*) as total_contratos,
        SUM(valor_del_contrato) as monto_total_cop
    FROM contracts
    WHERE departamento IS NOT NULL AND departamento != 'NAN'
    GROUP BY departamento
    ORDER BY monto_total_cop DESC
    """
    return pd.read_sql_query(query, conn)
