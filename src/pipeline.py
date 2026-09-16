"""Orquestrador do pipeline de ingestão.

Sequência de execução para gerar os arquivos Parquet da camada Bronze.

Execução:  python -m src.pipeline
"""

import logging
import os

from src import ingest

# O nível de log vem do .env (carregado via dotenv).
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="[%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Iniciando pipeline de ingestão (Bronze)")

    etapas = [
        ingest.ingest_clientes,
        ingest.ingest_pedidos,
        ingest.ingest_pagamentos,
    ]

    for etapa in etapas:
        etapa()

    logger.info("Ingestão concluída. Bronze disponível em data/bronze/")


if __name__ == "__main__":
    main()