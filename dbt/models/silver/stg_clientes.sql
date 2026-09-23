-- =====================================================================
-- SILVER | stg_clientes
-- =====================================================================
-- Padroniza o cadastro de clientes tratando inconsistências de formato,
-- e-mails nulos, datas de cadastro inválidas e duplicidade de IDs.
-- =====================================================================

{{ config(
    materialized='external',
    format='parquet',
    location='../data/silver/stg_clientes.parquet'
) }}


with fonte as (

    select * from {{ source('bronze', 'clientes') }}

),

tratamento_datas as (

    select
        *,
        -- 1. Tenta converter múltiplos formatos de data e timestamp
        coalesce(
            try_cast(data_cadastro as date),                                     -- ISO 'YYYY-MM-DD'
            try_cast(try_strptime(data_cadastro, '%d/%m/%Y') as date),          -- pt-BR 'DD/MM/YYYY'
            try_cast(try_strptime(data_cadastro, '%Y-%m-%d %H:%M:%S') as date), -- ISO Timestamp 'YYYY-MM-DD HH:MM:SS'
            try_cast(try_strptime(data_cadastro, '%d/%m/%Y %H:%M:%S') as date)  -- pt-BR Timestamp 'DD/MM/YYYY HH:MM:SS'
        ) as data_cadastro_convertida

    from fonte

),

datas_sanitizadas as (

    select
        *,
        -- 2. Descarta datas fora da faixa plausível do negócio
        case
            when data_cadastro_convertida < '2000-01-01'::date then null
            when data_cadastro_convertida > current_date then null
            else data_cadastro_convertida
        end as data_cadastro_final

    from tratamento_datas

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

        data_cadastro_final as data_cadastro,

        -- Identifica duplicatas de cliente_id mantendo a ocorrência com a menor data de cadastro válida
        row_number() over (
            partition by cast(cliente_id as integer)
            order by data_cadastro_final asc nulls last
        ) as rn

    from datas_sanitizadas

)

select
    cliente_id,
    nome,
    email,
    estado,
    data_cadastro
from tratada
where rn = 1
  and cliente_id is not null