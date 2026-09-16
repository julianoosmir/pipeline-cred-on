-- =====================================================================
-- GOLD | faturamento_cliente_mensal
-- =====================================================================
-- PERGUNTA DE NEGÓCIO: Qual o faturamento realizado por cliente por mês?
-- GRÃO: Um registro por cliente por mês.
-- ARQUITETURA: Tabela larga de consumo para dashboards.
-- =====================================================================
{{ config(
    materialized='external',
    format='parquet',
    location='../data/gold/faturamento_cliente_mensal.parquet'
) }}

with pedidos as (

    select *
    from {{ ref('stg_pedidos') }} p
    inner join {{ ref('stg_clientes') }} c
    on p.cliente_id = c.cliente_id
    where status = 'CONCLUÍDO'

),

clientes as (

    select *
    from {{ ref('stg_clientes') }}

),

vendas_mensais as (

    select
        cliente_id,
        strftime(data_pedido, '%Y-%m') as mes_ano,
        count(distinct pedido_id) as total_pedidos,
        sum(valor_total) as faturamento_total,
        avg(valor_total) as ticket_medio

    from pedidos
    group by 1, 2

)

select
    v.mes_ano,
    c.cliente_id,
    c.nome as nome_cliente,
    c.email as email_cliente,
    c.estado,
    v.total_pedidos,
    v.faturamento_total,
    round(v.ticket_medio, 2) as ticket_medio

from vendas_mensais v
left join clientes c
    on v.cliente_id = c.cliente_id