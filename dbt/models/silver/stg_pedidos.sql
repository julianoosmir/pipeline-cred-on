-- =====================================================================
-- SILVER | stg_pedidos
-- =====================================================================
-- Tipagem, tratamento de datas inválidas, deduplicação e padronização.
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

),

tratamento_datas as (

    select
        f.*,

        -- 1. Tenta converter diferentes formatos de data e string com hora
        coalesce(
            try_cast(f.data_pedido as date),                                     -- Formato ISO padrão 'YYYY-MM-DD'
            try_cast(try_strptime(f.data_pedido, '%d/%m/%Y') as date),          -- Formato pt-BR 'DD/MM/YYYY'
            try_cast(try_strptime(f.data_pedido, '%Y-%m-%d %H:%M:%S') as date), -- ISO com Timestamp 'YYYY-MM-DD HH:MM:SS'
            try_cast(try_strptime(f.data_pedido, '%d/%m/%Y %H:%M:%S') as date)  -- pt-BR com Timestamp 'DD/MM/YYYY HH:MM:SS'
        ) as data_pedido_convertida

    from fonte f

),

datas_sanitizadas as (

    select
        *,
        -- 2. Filtra datas fora da faixa plausível de negócio (ex: entre os anos 2000 e a data atual)
        case
            when data_pedido_convertida < '2000-01-01'::date then null
            when data_pedido_convertida > current_date then null
            else data_pedido_convertida
        end as data_pedido_final

    from tratamento_datas

)

select
    try_cast(f.pedido_id as bigint) as pedido_id,
    try_cast(f.cliente_id as integer) as cliente_id,

    -- Data limpa e validada (fallback para data atual se nula/inválida, se desejado)
    f.data_pedido_final as data_pedido,

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

from datas_sanitizadas f
inner join clientes_validos c on try_cast(f.cliente_id as integer) = c.cliente_id
where f.pedido_id is not null
  and f.data_pedido_final is not null  -- Remove registros que possuem datas totalmente irrecuperáveis