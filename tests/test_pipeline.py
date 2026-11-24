"""
Unit tests for the SECOP II ETL and SQL analytical queries.
Run with: python -m unittest discover -s tests -v
"""

from contextlib import closing
import os
import tempfile
import unittest
import pandas as pd
from src.etl import transform_contracts, save_to_sqlite
from src.database import (
    get_connection,
    get_kpi_summary,
    get_top_entidades,
    get_top_contratistas_ranking,
    get_distribucion_modalidad,
    get_gasto_por_departamento,
)


SAMPLE_RAW_CONTRACTS = [
    {
        "id_contrato": "CO1.PCCNTR.1",
        "referencia_del_contrato": "REF-001",
        "nombre_entidad": "alcaldía de bogotá",
        "nit_entidad": "899999061",
        "departamento": "bogotá d.c.",
        "ciudad": "bogotá",
        "sector": "gobierno",
        "modalidad_de_contratacion": "contratación directa",
        "tipo_de_contrato": "Prestación de servicios",
        "proveedor_adjudicado": "empresa alfa sas",
        "documento_proveedor": "900111222",
        "valor_del_contrato": "50000000",
        "fecha_de_firma": "2026-01-15T10:00:00.000",
        "fecha_de_inicio_del_contrato": "2026-01-20T00:00:00.000",
        "fecha_de_fin_del_contrato": "2026-06-20T00:00:00.000",
        "objeto_del_contrato": "Desarrollo de software",
        "estado_contrato": "En ejecución",
    },
    {
        "id_contrato": "CO1.PCCNTR.2",
        "referencia_del_contrato": "REF-002",
        "nombre_entidad": "alcaldía de bogotá",
        "nit_entidad": "899999061",
        "departamento": "bogotá d.c.",
        "ciudad": "bogotá",
        "sector": "gobierno",
        "modalidad_de_contratacion": "licitación pública",
        "tipo_de_contrato": "Obra",
        "proveedor_adjudicado": "empresa alfa sas",
        "documento_proveedor": "900111222",
        "valor_del_contrato": "150000000",
        "fecha_de_firma": "2026-02-10T10:00:00.000",
        "fecha_de_inicio_del_contrato": "2026-02-15T00:00:00.000",
        "fecha_de_fin_del_contrato": "2026-12-15T00:00:00.000",
        "objeto_del_contrato": "Infraestructura vial",
        "estado_contrato": "En ejecución",
    },
    {
        "id_contrato": "CO1.PCCNTR.3",
        "referencia_del_contrato": "REF-003",
        "nombre_entidad": "gobernación de antioquia",
        "nit_entidad": "890900286",
        "departamento": "antioquia",
        "ciudad": "medellín",
        "sector": "salud",
        "modalidad_de_contratacion": "contratación directa",
        "tipo_de_contrato": "Suministro",
        "proveedor_adjudicado": "proveedor beta ltda",
        "documento_proveedor": "800333444",
        "valor_del_contrato": "invalid_number",
        "fecha_de_firma": "2026-03-01T10:00:00.000",
        "fecha_de_inicio_del_contrato": "2026-03-05T00:00:00.000",
        "fecha_de_fin_del_contrato": "2026-09-05T00:00:00.000",
        "objeto_del_contrato": "Insumos médicos",
        "estado_contrato": "Aprobado",
    },
]


class TestSecopPipeline(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_secop.db")
        self.df = transform_contracts(SAMPLE_RAW_CONTRACTS)
        save_to_sqlite(self.df, db_path=self.db_path)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_transform_normalizes_text_and_numeric_values(self) -> None:
        self.assertEqual(len(self.df), 3)
        self.assertEqual(self.df.loc[0, "nombre_entidad"], "ALCALDÍA DE BOGOTÁ")
        self.assertEqual(self.df.loc[0, "valor_del_contrato"], 50000000.0)
        # Invalid numeric values must be safely coerced to 0.0
        self.assertEqual(self.df.loc[2, "valor_del_contrato"], 0.0)

    def test_transform_handles_empty_input(self) -> None:
        empty_df = transform_contracts([])
        self.assertTrue(empty_df.empty)

    def test_kpi_summary(self) -> None:
        with closing(get_connection(self.db_path)) as conn:
            kpis = get_kpi_summary(conn)
        self.assertEqual(kpis["total_contratos"], 3)
        self.assertEqual(kpis["monto_total_cop"], 200000000.0)
        self.assertEqual(kpis["mayor_contrato_cop"], 150000000.0)

    def test_top_entidades(self) -> None:
        with closing(get_connection(self.db_path)) as conn:
            df_ent = get_top_entidades(conn, limit=5)
        self.assertEqual(df_ent.iloc[0]["nombre_entidad"], "ALCALDÍA DE BOGOTÁ")
        self.assertEqual(df_ent.iloc[0]["cantidad_contratos"], 2)
        self.assertEqual(df_ent.iloc[0]["total_invertido_cop"], 200000000.0)

    def test_top_contratistas_ranking_window_function(self) -> None:
        with closing(get_connection(self.db_path)) as conn:
            df_rank = get_top_contratistas_ranking(conn, limit=5)
        self.assertEqual(df_rank.iloc[0]["ranking"], 1)
        self.assertEqual(df_rank.iloc[0]["proveedor_adjudicado"], "EMPRESA ALFA SAS")
        self.assertEqual(df_rank.iloc[0]["numero_adjudicaciones"], 2)

    def test_distribucion_modalidad_and_departamento(self) -> None:
        with closing(get_connection(self.db_path)) as conn:
            df_mod = get_distribucion_modalidad(conn)
            df_dep = get_gasto_por_departamento(conn)
        self.assertEqual(len(df_mod), 2)
        self.assertEqual(len(df_dep), 2)
        self.assertEqual(df_dep.iloc[0]["departamento"], "BOGOTÁ D.C.")


if __name__ == "__main__":
    unittest.main()
