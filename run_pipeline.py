"""
CLI Runner for the SECOP II ETL Pipeline.
Allows running data extraction, transformation, and SQLite loading from the terminal
without needing to launch the Streamlit web interface.

Example:
    python run_pipeline.py --limit 500 --departamento "ANTIOQUIA"
"""

from contextlib import closing
import argparse
import logging
from src.etl import fetch_contracts, transform_contracts, save_to_sqlite
from src.database import get_connection, get_kpi_summary

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="SECOP II ETL Pipeline Runner")
    parser.add_argument("--limit", type=int, default=500, help="Number of records to fetch from SODA API")
    parser.add_argument("--departamento", type=str, default="Todos", help="Filter by Colombian department")
    parser.add_argument("--modalidad", type=str, default="Todas", help="Filter by procurement modality")
    parser.add_argument("--db", type=str, default="data/secop_contracts.db", help="Target SQLite database path")
    args = parser.parse_args()

    logger.info("Starting SECOP II extraction (limit=%d, departamento=%s, modalidad=%s)",
                args.limit, args.departamento, args.modalidad)
    raw_data = fetch_contracts(
        departamento=args.departamento,
        modalidad=args.modalidad,
        limit=args.limit
    )
    logger.info("Extracted %d raw records from datos.gov.co", len(raw_data))

    df = transform_contracts(raw_data)
    saved = save_to_sqlite(df, db_path=args.db)
    logger.info("Loaded %d clean records into %s", saved, args.db)

    with closing(get_connection(args.db)) as conn:
        kpis = get_kpi_summary(conn)
        logger.info(
            "Pipeline Summary | Contracts: %.0f | Total COP: $%,.0f | Avg COP: $%,.0f",
            kpis["total_contratos"],
            kpis["monto_total_cop"],
            kpis["promedio_contrato_cop"]
        )


if __name__ == "__main__":
    main()
