-- =====================================================================
-- SILVER | stg_clientes
-- =====================================================================
-- Padroniza o cadastro de clientes tratando inconsistências de formato,
-- e-mails nulos e duplicidade de IDs.
-- =====================================================================

{{ config(
    materialized='external',
    format='parquet',
    location='../data/silver/stg_clientes.parquet'
) }}


with fonte as (

    select * from {{ source('bronze', 'clientes') }}

),

tratada as (

    select
        cast(cliente_id as integer) as cliente_id,

        -- Capitaliza o nome (Title Case) e remove espaços extras
        array_to_string(
            list_transform(
                string_split(lower(trim(nome)), ' '),
                w -> upper(w[1]) || w[2:]
            ),
            ' '
        ) as nome,

        -- Normaliza o e-mail para minúsculas ou aplica valor padrão se nulo
        coalesce(lower(trim(email)), 'nao_informado@email.com') as email,

        -- Mapeia formas por extenso para a sigla da UF correspondente
        case upper(trim(estado))
            when 'SÃO PAULO' THEN 'SP'
            when 'RIO DE JANEIRO' THEN 'RJ'
            when 'MINAS GERAIS' THEN 'MG'
            when 'PARANÁ' THEN 'PR'
            when 'RIO GRANDE DO SUL' THEN 'RS'
            else upper(trim(estado))
        end as estado,

        try_cast(data_cadastro as date) as data_cadastro,

        -- Identifica duplicatas de cliente_id mantendo a primeira ocorrência
        row_number() over (
            partition by cast(cliente_id as integer)
            order by data_cadastro asc
        ) as rn

    from fonte

)

select
    cliente_id,
    nome,
    email,
    estado,
    data_cadastro
from tratada
where rn = 1