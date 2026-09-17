import os
from pathlib import Path
import numpy as np
import pandas as pd
from deltalake import DeltaTable, write_deltalake

# =====================================================================
# 1. RESOLUÇÃO DINÂMICA DE DIRETÓRIOS (USANDO A PASTA DELTA)
# =====================================================================
BASE_DIR = Path(__file__).resolve().parent.parent / "data"

BRONZE_DIR = BASE_DIR / "bronze"
DELTA_DIR = BASE_DIR / "delta"  # Substituted silver for delta
GOLD_DIR = BASE_DIR / "gold"

for folder in [BRONZE_DIR, DELTA_DIR, GOLD_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# =====================================================================
# 2. CARGA DAS FONTES (SUPORTE A CSV E JSON)
# =====================================================================
def carregar_fonte(nome_arquivo):
    caminho_raw = BASE_DIR / "raw" / nome_arquivo
    caminho_data = BASE_DIR / nome_arquivo

    if caminho_raw.exists():
        caminho_final = caminho_raw
    elif caminho_data.exists():
        caminho_final = caminho_data
    else:
        raise FileNotFoundError(
            f"Arquivo '{nome_arquivo}' não encontrado em:\n"
            f" - {caminho_raw}\n"
            f" - {caminho_data}"
        )

    # Verifica a extensão para usar a função de leitura correta
    if nome_arquivo.endswith('.json'):
        return pd.read_json(caminho_final)
    return pd.read_csv(caminho_final)

# Leitura dos arquivos
df_clientes = carregar_fonte("clientes.csv")
df_pedidos = carregar_fonte("pedidos.csv")
df_pagamentos = carregar_fonte("pagamentos.json")

# =====================================================================
# 3. SIMULAÇÃO DE RUÍDOS/DEFEITOS NOS DADOS BRUTOS
# =====================================================================
np.random.seed(42)

# Defeitos Clientes
df_clientes.loc[
    np.random.choice(df_clientes.index, size=min(5, len(df_clientes)), replace=False), "email"
] = np.nan
state_map = {"SP": "sp", "RJ": "rj", "MG": "mg"}
for i in np.random.choice(df_clientes.index, size=min(3, len(df_clientes)), replace=False):
    if df_clientes.loc[i, "estado"] in state_map:
        df_clientes.loc[i, "estado"] = state_map[df_clientes.loc[i, "estado"]]

# Defeitos Pedidos
df_pedidos.loc[
    np.random.choice(df_pedidos.index, size=min(7, len(df_pedidos)), replace=False), "valor_total"
] = np.nan
status_map = {"CONCLUIDO": "concluido", "PENDENTE": "pendentte", "CANCELADO": "Cancelado"}
for i in np.random.choice(df_pedidos.index, size=min(10, len(df_pedidos)), replace=False):
    if df_pedidos.loc[i, "status"] in status_map:
        df_pedidos.loc[i, "status"] = status_map[df_pedidos.loc[i, "status"]]

# Defeitos Pagamentos
df_pagamentos.loc[
    np.random.choice(df_pagamentos.index, size=min(4, len(df_pagamentos)), replace=False), "valor_pago"
] = np.nan

# =====================================================================
# 4. CAMADA BRONZE (RAW PRESERVATION)
# =====================================================================
print("--- GRAVANDO CAMADA BRONZE ---")

write_deltalake(str(BRONZE_DIR / "clientes"), df_clientes, mode="overwrite")
write_deltalake(str(BRONZE_DIR / "pedidos"), df_pedidos, mode="overwrite")
write_deltalake(str(BRONZE_DIR / "pagamentos"), df_pagamentos, mode="overwrite")

print("Camada Bronze criada em data/bronze/.")

# =====================================================================
# 5. GRAVAÇÃO NA PASTA DELTA (CLEANSED & STANDARDIZED)
# =====================================================================
print("\n--- PROCESSANDO DADOS E SALVANDO EM data/delta/ ---")

# 5.1 Staging Clientes
raw_clientes = DeltaTable(str(BRONZE_DIR / "clientes")).to_pandas()
stg_clientes = raw_clientes.copy()
stg_clientes["nome"] = stg_clientes["nome"].str.strip()
stg_clientes["email"] = stg_clientes["email"].str.lower().fillna("nao_informado@email.com")
stg_clientes["estado"] = stg_clientes["estado"].str.upper()
stg_clientes = stg_clientes.drop_duplicates(subset=["cliente_id"])

write_deltalake(str(DELTA_DIR / "stg_clientes"), stg_clientes, mode="overwrite")

# 5.2 Staging Pedidos
raw_pedidos = DeltaTable(str(BRONZE_DIR / "pedidos")).to_pandas()
stg_pedidos = raw_pedidos.copy()
stg_pedidos["status"] = stg_pedidos["status"].str.upper().replace({"PENDENTTE": "PENDENTE"})
stg_pedidos["data_pedido"] = pd.to_datetime(stg_pedidos["data_pedido"], errors="coerce")
stg_pedidos["valor_total"] = pd.to_numeric(stg_pedidos["valor_total"], errors="coerce").fillna(0.00)
stg_pedidos = stg_pedidos.dropna(subset=["pedido_id"]).drop_duplicates(subset=["pedido_id"])

write_deltalake(str(DELTA_DIR / "stg_pedidos"), stg_pedidos, mode="overwrite")

# 5.3 Staging Pagamentos
raw_pagamentos = DeltaTable(str(BRONZE_DIR / "pagamentos")).to_pandas()
stg_pagamentos = raw_pagamentos.copy()
stg_pagamentos["metodo_pagamento"] = stg_pagamentos["metodo_pagamento"].str.lower()
stg_pagamentos["data_pagamento"] = pd.to_datetime(stg_pagamentos["data_pagamento"], errors="coerce")
stg_pagamentos["valor_pago"] = pd.to_numeric(stg_pagamentos["valor_pago"], errors="coerce").fillna(0.00)
stg_pagamentos = stg_pagamentos.dropna(subset=["pagamento_id"]).drop_duplicates(subset=["pagamento_id"])

write_deltalake(str(DELTA_DIR / "stg_pagamentos"), stg_pagamentos, mode="overwrite")

print("Dados limpos gravados com sucesso na pasta data/delta/.")

# =====================================================================
# 6. CAMADA GOLD (LENDO A PARTIR DA PASTA DELTA)
# =====================================================================
print("\n--- PROCESSANDO CAMADA GOLD ---")

delta_pedidos = DeltaTable(str(DELTA_DIR / "stg_pedidos")).to_pandas()
delta_clientes = DeltaTable(str(DELTA_DIR / "stg_clientes")).to_pandas()

pedidos_validos = delta_pedidos[delta_pedidos["status"] == "CONCLUIDO"].copy()
pedidos_validos["mes"] = pedidos_validos["data_pedido"].dt.to_period("M").astype(str)

vendas_cliente = (
    pedidos_validos.groupby(["cliente_id", "mes"], as_index=False)
    .agg(
        quantidade_pedidos=("pedido_id", "count"),
        faturamento_total=("valor_total", "sum")
    )
)

gold_faturamento = vendas_cliente.merge(delta_clientes, on="cliente_id", how="left")

write_deltalake(str(GOLD_DIR / "faturamento_cliente_mensal"), gold_faturamento, mode="overwrite")

print("Camada Gold criada em data/gold/.")