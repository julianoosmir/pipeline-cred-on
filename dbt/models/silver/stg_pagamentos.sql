-- =====================================================================
-- SILVER | stg_pagamentos
-- =====================================================================
-- Padronização do método de pagamento e normalização financeira/temporal.
-- =====================================================================

{{ config(
    materialized='external',
    format='parquet',
    location='../data/silver/stg_pagamentos.parquet'
) }}

with fonte as (

    select * from {{ source('bronze', 'pagamentos') }}

),

pedidos_validos as (

    select pedido_id from {{ ref('stg_pedidos') }}

)

select
    try_cast(f.pagamento_id as bigint) as pagamento_id,
    try_cast(f.pedido_id as bigint) as pedido_id,

    -- Normaliza formas de escrita dos métodos de pagamento
    case lower(trim(f.metodo_pagamento))
        when 'cartao_credito' then 'Cartão de Crédito'
        when 'cartão de crédito' then 'Cartão de Crédito'
        when 'pix' then 'PIX'
        when 'boleto' then 'Boleto'
        else trim(f.metodo_pagamento)
    end as metodo_pagamento,

    -- Limpa R$, ponto e vírgula antes de converter para numeric
    coalesce(
        try_cast(
            replace(
                replace(
                    replace(f.valor_pago, 'R$', ''),
                '.', ''),
            ',', '.') as numeric(10,2)
        ),
        0.00
    ) as valor_pago,

    coalesce(
        try_cast(f.data_pagamento as date),
        try_cast(try_strptime(f.data_pagamento, '%d/%m/%Y') as date)
    ) as data_pagamento

from fonte f
inner join pedidos_validos p on try_cast(f.pedido_id as bigint) = p.pedido_id
where f.pagamento_id is not null