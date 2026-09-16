-- =====================================================================
-- SILVER | stg_pedidos
-- =====================================================================
-- Tipagem, deduplicação de pedidos e padronização do status do pedido.
-- =====================================================================
{{ config(
    materialized='external',
    format='parquet',
    location='../data/silver/stg_pedidos.parquet'
) }}


with fonte as (

    select distinct * from {{ source('bronze', 'pedidos') }}

)

select
    try_cast(pedido_id as bigint) as pedido_id,
    try_cast(cliente_id as integer) as cliente_id,

    -- Trata formato ISO e formato DD/MM/YYYY de datas
    coalesce(
        try_cast(data_pedido as date),
        try_cast(try_strptime(data_pedido, '%d/%m/%Y') as date)
    ) as data_pedido,

    -- Garante conversão numérica correta e substitui nulos por zero
    coalesce(try_cast(valor_total as numeric(10,2)), 0.00) as valor_total,

    -- Padroniza acentuação e caixa alta do status
    case upper(trim(status))
        when 'CONCLUIDO' THEN 'CONCLUÍDO'
        when 'PENDENTTE' THEN 'PENDENTE'
        else upper(trim(status))
    end as status

from fonte
where pedido_id is not null