from pathlib import Path
import pandas as pd
import plotly.express as px

# =====================================================================
# 1. DIRETÓRIOS E CONFIGURAÇÕES
# =====================================================================
BASE_DIR = Path(__file__).resolve().parent
GOLD_DIR = BASE_DIR / "data" / "gold"
OUTPUT_HTML = BASE_DIR / "dashboard_gold.html"


def carregar_dados():
    """Busca e carrega todos os Parquets da camada Gold."""
    dados = {}

    # 1. Tentar ler faturamento_cliente_mensal
    path_fat = GOLD_DIR / "faturamento_cliente_mensal.parquet"
    if not path_fat.exists():
        path_fat = GOLD_DIR / "faturamento_cliente_mensal"  # Caso seja pasta

    if path_fat.exists():
        try:
            dados["faturamento"] = pd.read_parquet(path_fat)
            print(f"✅ Loaded faturamento_cliente_mensal ({len(dados['faturamento'])} linhas)")
        except Exception as e:
            print(f"❌ Erro ao ler faturamento: {e}")

    # 2. Tentar ler resumo_metodos_pagamento
    path_pag = GOLD_DIR / "resumo_metodos_pagamento.parquet"
    if not path_pag.exists():
        path_pag = GOLD_DIR / "resumo_metodos_pagamento"  # Caso seja pasta

    if path_pag.exists():
        try:
            dados["pagamentos"] = pd.read_parquet(path_pag)
            print(f"✅ Loaded resumo_metodos_pagamento ({len(dados['pagamentos'])} linhas)")
        except Exception as e:
            print(f"❌ Erro ao ler pagamentos: {e}")

    return dados


def gerar_dashboard():
    dados = carregar_dados()

    if not dados:
        print("⚠️ Nenhum dado encontrado na pasta data/gold!")
        return

    divs_graficos = []

    # --- GRÁFICO 1: Faturamento Mensal ---
    if "faturamento" in dados:
        df_fat = dados["faturamento"]
        col_mes = "mes_ano" if "mes_ano" in df_fat.columns else "mes"

        if col_mes in df_fat.columns and "faturamento_total" in df_fat.columns:
            df_mes = df_fat.groupby(col_mes, as_index=False)["faturamento_total"].sum().sort_values(col_mes)

            fig1 = px.bar(
                df_mes,
                x=col_mes,
                y="faturamento_total",
                title="<b>📈 Faturamento Total por Mês</b>",
                labels={col_mes: "Mês/Ano", "faturamento_total": "Faturamento (R$)"},
                text_auto=".2f",
                color_discrete_sequence=["#1e3c72"]
            )
            fig1.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=50, b=20))
            # Usamos include_plotlyjs='inline' na 1ª figura para carregar o JS embutido
            divs_graficos.append(fig1.to_html(full_html=False, include_plotlyjs='inline'))

        # --- GRÁFICO 2: Top Clientes ---
        col_cliente = "nome_cliente" if "nome_cliente" in df_fat.columns else "nome"
        if col_cliente in df_fat.columns and "faturamento_total" in df_fat.columns:
            df_top = df_fat.groupby(col_cliente, as_index=False)["faturamento_total"].sum().sort_values(
                "faturamento_total", ascending=False).head(10)

            fig2 = px.bar(
                df_top,
                x="faturamento_total",
                y=col_cliente,
                orientation="h",
                title="<b>🏆 Top 10 Clientes por Faturamento</b>",
                labels={col_cliente: "Cliente", "faturamento_total": "Faturamento (R$)"},
                text_auto=".2f",
                color_discrete_sequence=["#00a86b"]
            )
            fig2.update_layout(template="plotly_white", yaxis={"categoryorder": "total ascending"},
                               margin=dict(l=20, r=20, t=50, b=20))
            divs_graficos.append(fig2.to_html(full_html=False, include_plotlyjs=False))

    # --- GRÁFICO 3: Meios de Pagamento ---
    if "pagamentos" in dados:
        df_pag = dados["pagamentos"]
        col_val = "valor_total_processado" if "valor_total_processado" in df_pag.columns else "valor_pago"

        if "metodo_pagamento" in df_pag.columns and col_val in df_pag.columns:
            fig3 = px.pie(
                df_pag,
                names="metodo_pagamento",
                values=col_val,
                title="<b>💳 Distribuição por Método de Pagamento</b>",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig3.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=50, b=20))
            divs_graficos.append(fig3.to_html(full_html=False, include_plotlyjs=False))

    # --- ESTRUTURAÇÃO DO HTML ---
    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Dashboard Camada Gold</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f6f9;
                margin: 0;
                padding: 20px;
            }}
            .header {{
                text-align: center;
                background: linear-gradient(135deg, #1e3c72, #2a5298);
                color: white;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
            }}
            .grid {{
                display: inline;
                grid-template-columns: repeat(auto-fit, minmax(480px, 1fr));
                gap: 20px;
            }}
            .card {{
                background: white;
                padding: 10px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                margin: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>🚀 Dashboard Executivo - Camada Gold</h2>
        </div>
        <div class="grid">
            {"".join([f'<div class="card">{div}</div>' for div in divs_graficos])}
        </div>
    </body>
    </html>
    """

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\n🎉 Dashboard HTML gerado em: {OUTPUT_HTML}")


if __name__ == "__main__":
    gerar_dashboard()