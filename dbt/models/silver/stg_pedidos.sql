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

),

clientes_validos as (

    select cliente_id from {{ ref('stg_clientes') }}

)

select
    try_cast(f.pedido_id as bigint) as pedido_id,
    try_cast(f.cliente_id as integer) as cliente_id,

    coalesce(
        try_cast(f.data_pedido as date),
        try_cast(try_strptime(f.data_pedido, '%d/%m/%Y') as date)
    ) as data_pedido,

    coalesce(
        try_cast(
            replace(
                replace(
                    replace(f.valor_total, 'R$', ''),
                '.', ''),
            ',', '.') as numeric(10,2)
        ),
        0.00
    ) as valor_total,

    case upper(trim(f.status))
        when 'CONCLUIDO' THEN 'CONCLUÍDO'
        when 'PENDENTTE' THEN 'PENDENTE'
        when 'CANCELADO' THEN 'CANCELADO'
        else upper(trim(f.status))
    end as status

from fonte f
inner join clientes_validos c on try_cast(f.cliente_id as integer) = c.cliente_id
where f.pedido_id is not null