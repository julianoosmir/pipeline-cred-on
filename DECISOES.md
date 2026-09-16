# DECISÕES DO PROJETO

## Arquitetura
Foi utilizada a arquitetura Medallion baseada nas camadas Bronze, Silver e Gold.

## Camadas
- **Bronze / RAW:** Preservação dos dados no formato original utilizando Delta Lake para auditoria, historização e suporte ao Time Travel.
- **Silver:** Limpeza e padronização (remoção de espaços, ajuste de caixa nos textos, tratamento de datas).
- **Gold:** Modelo relacional consolidado com agregação de faturamento mensal por cliente.

## Validação de Dados
Inclusão de testes automatizados para verificar regras de unicidade, nulidade, chaves estrangeiras ed domínios aceitos.

dbt run --select silver
dbt run --select gold