import pandas as pd
import numpy as np

# ==========================================
# 0. CARREGAMENTO DOS DADOS (LEITURA APENAS DOS CSVs)
# ==========================================
df_clientes = pd.read_csv("data/raw/clientes.csv")
df_pedidos = pd.read_csv("data/raw/pedidos.csv")
df_pagamentos = pd.read_csv("data/raw/pagamentos.csv")


# ==========================================
# 1. DIAGNÓSTICO DE PROBLEMAS (AUDITORIA)
# ==========================================
print("--- 1. DIAGNÓSTICO INICIAL ---")

# A. Identificar duplicatas
print(f"Duplicatas em clientes (ID 101): {df_clientes['cliente_id'].duplicated().sum()} registro(s)")
print(f"Linhas idênticas em pedidos: {df_pedidos.duplicated().sum()} registro(s)")

# B. Valores Nulos
print("\nValores nulos por tabela:")
print("Clientes:\n", df_clientes.isnull().sum()[df_clientes.isnull().sum() > 0])
print("Pedidos:\n", df_pedidos.isnull().sum()[df_pedidos.isnull().sum() > 0])

# C. Integridade Referencial (Chaves Órfãs)
orfaos_pedidos = df_pedidos[~df_pedidos['cliente_id'].isin(df_clientes['cliente_id'])]
print(f"\nPedidos com cliente_id inexistente: {len(orfaos_pedidos)}")

orfaos_pagamentos = df_pagamentos[~df_pagamentos['pedido_id'].isin(df_pedidos['pedido_id'])]
print(f"Pagamentos com pedido_id inexistente: {len(orfaos_pagamentos)}")


# ==========================================
# 2. LIMPEZA E PADRONIZAÇÃO DADOS
# ==========================================

# --- TRATAMENTO: CLIENTES ---
df_clientes_clean = df_clientes.copy()

# 1. Padronizar caixa dos nomes (Title Case: "Joao Da Silva")
df_clientes_clean['nome'] = df_clientes_clean['nome'].str.strip().str.title()

# 2. Normalizar Estados/UF (Mapeamento de siglas)
uf_map = {'São Paulo': 'SP', 'SP': 'SP', 'RJ': 'RJ', 'MG': 'MG', 'PR': 'PR', 'RS': 'RS'}
df_clientes_clean['estado'] = df_clientes_clean['estado'].map(uf_map).fillna(df_clientes_clean['estado'])

# 3. Tratar emails nulos
df_clientes_clean['email'] = df_clientes_clean['email'].fillna('nao_informado@email.com')

# 4. Remover duplicatas de ID mantendo o primeiro registro
df_clientes_clean = df_clientes_clean.drop_duplicates(subset=['cliente_id'], keep='first')


# --- TRATAMENTO: PEDIDOS ---
df_pedidos_clean = df_pedidos.copy()

# 1. Remover duplicatas idênticas
df_pedidos_clean = df_pedidos_clean.drop_duplicates()

# 2. Padronizar status (Tratar erros de digitação e caixa baixa)
status_map = {
    'CONCLUIDO': 'CONCLUÍDO',
    'concluido': 'CONCLUÍDO',
    'pendentte': 'PENDENTE',
    'CANCELADO': 'CANCELADO'
}
df_pedidos_clean['status'] = df_pedidos_clean['status'].map(status_map).fillna('INDEFINIDO')

# 3. Converter para numérico (float) e tratar valor_total nulo
df_pedidos_clean['valor_total'] = pd.to_numeric(df_pedidos_clean['valor_total'], errors='coerce').fillna(0.0)


# --- TRATAMENTO: PAGAMENTOS ---
df_pagamentos_clean = df_pagamentos.copy()

# 1. Padronizar meio de pagamento
metodo_map = {
    'cartao_credito': 'Cartão de Crédito',
    'Cartão de Crédito': 'Cartão de Crédito',
    'PIX': 'PIX',
    'pix': 'PIX',
    'Boleto': 'Boleto'
}
df_pagamentos_clean['metodo_pagamento'] = df_pagamentos_clean['metodo_pagamento'].map(metodo_map)

# 2. Converter valor_pago para numérico (float)
df_pagamentos_clean['valor_pago'] = pd.to_numeric(df_pagamentos_clean['valor_pago'], errors='coerce').fillna(0.0)

# 3. Padronizar formato de datas (DD/MM/YYYY vs YYYY-MM-DD -> YYYY-MM-DD)
def parse_data(data_str):
    if pd.isna(data_str):
        return None
    if '/' in str(data_str):
        return pd.to_datetime(data_str, format='%d/%m/%Y').strftime('%Y-%m-%d')
    return pd.to_datetime(data_str, format='%Y-%m-%d').strftime('%Y-%m-%d')

df_pagamentos_clean['data_pagamento'] = df_pagamentos_clean['data_pagamento'].apply(parse_data)


# ==========================================
# 3. REGRAS DE NEGÓCIO E VALIDAÇÃO CRUZADA
# ==========================================
print("\n--- 3. RELATÓRIO DE INCONSISTÊNCIAS E REGRA DE NEGÓCIO ---")

# A. Cruzamento Pedidos x Pagamentos (Divergência Financeira)
df_reconciliacao = pd.merge(
    df_pedidos_clean,
    df_pagamentos_clean,
    on='pedido_id',
    how='inner',
    suffixes=('_pedido', '_pagamento')
)

df_reconciliacao['diferenca'] = df_reconciliacao['valor_total'] - df_reconciliacao['valor_pago']
divergencias = df_reconciliacao[df_reconciliacao['diferenca'].abs() > 0.01]

print("\n[ALERT] Divergências de valor pago vs valor cobrado:")
print(divergencias[['pedido_id', 'valor_total', 'valor_pago', 'diferenca']])

# B. Exibição dos registros órfãos
print("\n[ALERT] Registros com falha de chave estrangeira (Órfãos):")
print("Pedidos sem Cliente válido:\n", orfaos_pedidos[['pedido_id', 'cliente_id']])
print("Pagamentos sem Pedido válido:\n", orfaos_pagamentos[['pagamento_id', 'pedido_id']])

# ==========================================
# 4. EXIBIÇÃO DOS DATAFRAMES TRATADOS EM MEMÓRIA
# ==========================================
print("\n--- 4. DATAFRAMES LIMPOS EM MEMÓRIA ---")
print("\n[CLIENTES]:\n", df_clientes_clean)
print("\n[PEDIDOS]:\n", df_pedidos_clean)
print("\n[PAGAMENTOS]:\n", df_pagamentos_clean)