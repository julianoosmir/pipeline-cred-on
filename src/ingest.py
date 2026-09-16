"""Ingestão: leva os dados das FONTES (data/raw) para o BRONZE (data/bronze).

Regras desta camada:
    - Ler os arquivos de origem (CSV,JSON) com Pandas.
    - Fazer APENAS normalizações técnicas mínimas (nomes de coluna,
      metadado de ingestão). Regra de negócio NÃO entra aqui —
      limpeza, padronização e integração são papel do dbt/transformação (Silver).
    - Persistir em Parquet, preservando o dado o mais próximo
      possível de como ele chegou.

raw = os arquivos que a origem nos entregou.
bronze = o que o NOSSO pipeline capturou e persistiu.
"""

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

# ---------------------------------------------------------------------
# Configuração via .env (Caminhos dinâmicos)
# ---------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

DATA_RAW_PATH = PROJECT_ROOT / os.getenv("DATA_RAW_PATH", "data/raw")
DATA_BRONZE_PATH = PROJECT_ROOT / os.getenv("DATA_BRONZE_PATH", "data/bronze")

logger = logging.getLogger(__name__)


def _gravar_bronze(df: pd.DataFrame, nome: str) -> None:
    """Acrescenta metadado técnico de ingestão e grava Parquet no Bronze."""
    df = df.copy()
    # Adiciona timestamp UTC para rastreabilidade de linhagem (lineage)
    df["_ingerido_em"] = datetime.now(timezone.utc).isoformat()
    DATA_BRONZE_PATH.mkdir(parents=True, exist_ok=True)
    destino = DATA_BRONZE_PATH / f"{nome}.parquet"
    df.to_parquet(destino, index=False)
    logger.info("Bronze gravado: %s (%d registros)", destino.name, len(df))


def ingest_clientes() -> None:
    """Ingestão do CSV de cadastro de clientes.

    Contém inconsistências de caixa, duplicatas e campos nulos no raw.
    """
    origem = DATA_RAW_PATH / "clientes.csv"
    logger.info("Lendo %s", origem.name)
    # dtype=str => tudo chega como texto.
    # Decisão consciente: o Bronze preserva o dado como veio;
    # tipar e limpar é decisão de transformação (Silver).
    df = pd.read_csv(origem, dtype=str)
    logger.info("%d registros encontrados", len(df))
    _gravar_bronze(df, "clientes")


def ingest_pedidos() -> None:
    """Ingestão do CSV de pedidos efetuados.

    Contém duplicatas idênticas, valores ausentes, status não padronizados
    e chave estrangeira sem correspondência no cadastro (cliente_id = 999).
    """
    origem = DATA_RAW_PATH / "pedidos.csv"
    logger.info("Lendo %s", origem.name)
    df = pd.read_csv(origem, dtype=str)
    logger.info("%d registros encontrados", len(df))
    _gravar_bronze(df, "pedidos")


def ingest_pagamentos() -> None:
    """Ingestão do JSON de transações e pagamentos.

    Contém divergência financeira de valores com o pedido, múltiplos formatos
    de data (DD/MM/YYYY vs YYYY-MM-DD) e pedido_id órfão.
    """
    origem = DATA_RAW_PATH / "pagamentos.json"
    logger.info("Lendo %s", origem.name)
    df = pd.read_json(origem, dtype=str)
    logger.info("%d registros encontrados", len(df))
    _gravar_bronze(df, "pagamentos")