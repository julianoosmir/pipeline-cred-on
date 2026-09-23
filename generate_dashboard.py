from pathlib import Path
import pandas as pd
import plotly.express as px

# =====================================================================
# 1. RESOLUÇÃO DE CAMINHOS
# =====================================================================
BASE_DIR = Path(__file__).resolve().parent
GOLD_DIR = BASE_DIR / "data" / "gold"
OUTPUT_HTML = BASE_DIR / "dashboard_gold.html"


def carregar_dados():
    """Busca e carrega os Parquets da camada Gold."""
    dados = {}

    # 1. Carrega faturamento_cliente_mensal
    path_fat = GOLD_DIR / "faturamento_cliente_mensal.parquet"
    if not path_fat.exists():
        path_fat = GOLD_DIR / "faturamento_cliente_mensal"

    if path_fat.exists():
        try:
            dados["faturamento"] = pd.read_parquet(path_fat)
            print(f"✅ Tabela faturamento carregada ({len(dados['faturamento'])} linhas)")
        except Exception as e:
            print(f"❌ Erro ao ler faturamento: {e}")

    # 2. Carrega resumo_metodos_pagamento
    path_pag = GOLD_DIR / "resumo_metodos_pagamento.parquet"
    if not path_pag.exists():
        path_pag = GOLD_DIR / "resumo_metodos_pagamento"

    if path_pag.exists():
        try:
            dados["pagamentos"] = pd.read_parquet(path_pag)
            print(f"✅ Tabela pagamentos carregada ({len(dados['pagamentos'])} linhas)")
        except Exception as e:
            print(f"❌ Erro ao ler pagamentos: {e}")

    return dados


def gerar_dashboard():
    dados = carregar_dados()

    if not dados:
        print("⚠️ Nenhum dado encontrado na pasta data/gold!")
        return

    divs_graficos = []
    cards_kpi = []

    # =====================================================================
    # 2. ANÁLISE DE FATURAMENTO E CLIENTES
    # =====================================================================
    if "faturamento" in dados:
        df_fat = dados["faturamento"]
        col_mes = "mes_ano" if "mes_ano" in df_fat.columns else "mes"
        col_cliente = "nome_cliente" if "nome_cliente" in df_fat.columns else "nome"

        # CÁLCULO DE VALORES TOTAIS (KPIs)
        fat_total = df_fat["faturamento_total"].sum() if "faturamento_total" in df_fat.columns else 0.0
        tot_pedidos = df_fat["total_pedidos"].sum() if "total_pedidos" in df_fat.columns else 0
        ticket_medio_geral = (fat_total / tot_pedidos) if tot_pedidos > 0 else 0.0

        cards_kpi.append(f"""
            <div class="kpi-card">
                <h3>Faturamento Total </h3>
                <p class="kpi-value">R$ {fat_total:,.2f}</p>
            </div>
            <div class="kpi-card">
                <h3>Total de Pedidos</h3>
                <p class="kpi-value">{int(tot_pedidos):,}</p>
            </div>
            <div class="kpi-card">
                <h3>Ticket Médio Geral</h3>
                <p class="kpi-value">R$ {ticket_medio_geral:,.2f}</p>
            </div>
        """)

        # GRÁFICO 1: EVOLUÇÃO DE FATURAMENTO MENSAL
        if col_mes in df_fat.columns and "faturamento_total" in df_fat.columns:
            df_mes = df_fat.groupby(col_mes, as_index=False)["faturamento_total"].sum().sort_values(col_mes)

            fig1 = px.bar(
                df_mes,
                x=col_mes,
                y="faturamento_total",
                title="<b>📈 Valor Total de Faturamento por Mês (R$)</b>",
                labels={col_mes: "Mês/Ano", "faturamento_total": "Faturamento (R$)"},
                text_auto=".2f",
                color_discrete_sequence=["#1e3c72"]
            )
            fig1.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=50, b=20))
            divs_graficos.append(fig1.to_html(full_html=False, include_plotlyjs='inline'))

        # GRÁFICO 2: TOP 10 CLIENTES POR VALOR TOTAL
        if col_cliente in df_fat.columns and "faturamento_total" in df_fat.columns:
            df_top = df_fat.groupby(col_cliente, as_index=False)["faturamento_total"].sum().sort_values(
                "faturamento_total", ascending=False).head(10)

            fig2 = px.bar(
                df_top,
                x="faturamento_total",
                y=col_cliente,
                orientation="h",
                title="<b>🏆 Top 10 Clientes por Valor Total Acumulado (R$)</b>",
                labels={col_cliente: "Cliente", "faturamento_total": "Faturamento (R$)"},
                text_auto=".2f",
                color_discrete_sequence=["#00a86b"]
            )
            fig2.update_layout(template="plotly_white", yaxis={"categoryorder": "total ascending"},
                               margin=dict(l=20, r=20, t=50, b=20))
            divs_graficos.append(fig2.to_html(full_html=False, include_plotlyjs=False))

        # GRÁFICO 3: FATURAMENTO ACUMULADO POR ESTADO (UF)
        if "estado" in df_fat.columns and "faturamento_total" in df_fat.columns:
            df_uf = df_fat.groupby("estado", as_index=False)["faturamento_total"].sum().sort_values("faturamento_total",
                                                                                                    ascending=False)

            fig3 = px.bar(
                df_uf,
                x="estado",
                y="faturamento_total",
                title="<b>🗺️ Faturamento Total por Estado (UF)</b>",
                labels={"estado": "Estado (UF)", "faturamento_total": "Faturamento (R$)"},
                text_auto=".2f",
                color_discrete_sequence=["#d97706"]
            )
            fig3.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=50, b=20))
            divs_graficos.append(fig3.to_html(full_html=False, include_plotlyjs=False))

    # =====================================================================
    # 3. ANÁLISE DE MÉTODOS DE PAGAMENTO
    # =====================================================================
    if "pagamentos" in dados:
        df_pag = dados["pagamentos"]
        col_val = "valor_total_processado" if "valor_total_processado" in df_pag.columns else "valor_pago"

        if "metodo_pagamento" in df_pag.columns and col_val in df_pag.columns:
            # GRÁFICO 4: DISTRIBUIÇÃO EM % E VALOR
            fig4 = px.pie(
                df_pag,
                names="metodo_pagamento",
                values=col_val,
                title="<b>💳 Distribuição de Valores por Método de Pagamento</b>",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig4.update_traces(textinfo="label+value+percent", texttemplate="%{label}: R$%{value:,.2f}<br>(%{percent})")
            fig4.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=50, b=20))
            divs_graficos.append(fig4.to_html(full_html=False, include_plotlyjs=False))

        # GRÁFICO 5: QUANTIDADE DE TRANSAÇÕES POR MÉTODO DE PAGAMENTO
        if "metodo_pagamento" in df_pag.columns and "quantidade_transacoes" in df_pag.columns:
            df_qtd = df_pag.groupby("metodo_pagamento", as_index=False)["quantidade_transacoes"].sum()

            fig5 = px.bar(
                df_qtd,
                x="metodo_pagamento",
                y="quantidade_transacoes",
                title="<b>🔢 Volume de Transações por Método de Pagamento</b>",
                labels={"metodo_pagamento": "Método", "quantidade_transacoes": "Qtd. Transações"},
                text_auto=True,
                color_discrete_sequence=["#2563eb"]
            )
            fig5.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=50, b=20))
            divs_graficos.append(fig5.to_html(full_html=False, include_plotlyjs=False))

    # =====================================================================
    # 4. ESTRUTURAÇÃO DO HTML COMPLETO
    # =====================================================================
    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard Camada Gold - Valores</title>
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: #f4f6f9;
                margin: 0;
                padding: 20px;
                color: #333;
            }}
            .header {{
                text-align: center;
                background: linear-gradient(135deg, #1e3c72, #2a5298);
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .header h2 {{ margin: 0; font-size: 26px; }}
            .header p {{ margin: 5px 0 0 0; opacity: 0.85; }}
            .kpi-container {{
                display: flex;
                justify-content: center;
                gap: 20px;
                margin-bottom: 20px;
                flex-wrap: wrap;
            }}
            .kpi-card {{
                background: white;
                padding: 15px 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                text-align: center;
                min-width: 200px;
            }}
            .kpi-card h3 {{
                margin: 0;
                font-size: 13px;
                color: #666;
                text-transform: uppercase;
            }}
            .kpi-value {{
                margin: 5px 0 0 0;
                font-size: 24px;
                font-weight: bold;
                color: #1e3c72;
            }}
            .grid {{
                display: inline;
                grid-template-columns: repeat(auto-fit, minmax(480px, 1fr));
                gap: 20px;
                max-width: 1400px;
                margin: 0 auto;
            }}
            .card {{
                background: white;
                padding: 15px;
                border-radius: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.08);
                margin: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>🚀 Dashboard Executivo - Valores da Camada Gold</h2>
            <p>Consolidação Analítica extraída diretamente dos arquivos</p>
        </div>

        <div class="kpi-container">
            {"".join(cards_kpi)}
        </div>

        <div class="grid">
            {"".join([f'<div class="card">{div}</div>' for div in divs_graficos])}
        </div>
    </body>
    </html>
    """

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\n🎉 Dashboard HTML com valores dos Parquets gerado com sucesso em: {OUTPUT_HTML}")


if __name__ == "__main__":
    gerar_dashboard()