-- =====================================================================
-- GOLD | resumo_metodos_pagamento
-- =====================================================================
-- PERGUNTA DE NEGÓCIO: Qual a distribuição financeira por método de pagamento?
-- GRÃO: Um registro por método de pagamento e mês.
-- =====================================================================

{{ config(
    materialized='external',
    format='parquet',
    location='../data/gold/resumo_metodos_pagamento.parquet'
) }}

with pagamentos as (

    select *
    from {{ ref('stg_pagamentos') }}

),

pedidos as (

    select *
    from {{ ref('stg_pedidos') }}
    where status = 'CONCLUÍDO'

)

select
    strftime(pag.data_pagamento, '%Y-%m') as mes_ano,
    pag.metodo_pagamento,
    count(distinct pag.pagamento_id) as quantidade_transacoes,
    sum(pag.valor_pago) as valor_total_processado

from pagamentos pag
inner join pedidos ped
    on pag.pedido_id = ped.pedido_id
group by 1, 2