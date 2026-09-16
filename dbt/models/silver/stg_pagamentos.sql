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

)

select
    try_cast(pagamento_id as bigint) as pagamento_id,
    try_cast(pedido_id as bigint) as pedido_id,

    -- Normaliza formas de escrita dos métodos de pagamento
    case lower(trim(metodo_pagamento))
        when 'cartao_credito' then 'Cartão de Crédito'
        when 'cartão de crédito' then 'Cartão de Crédito'
        when 'pix' then 'PIX'
        when 'boleto' then 'Boleto'
        else trim(metodo_pagamento)
    end as metodo_pagamento,

    coalesce(try_cast(valor_pago as numeric(10,2)), 0.00) as valor_pago,

    coalesce(
        try_cast(data_pagamento as date),
        try_cast(try_strptime(data_pagamento, '%d/%m/%Y') as date)
    ) as data_pagamento

from fonte
where pagamento_id is not null