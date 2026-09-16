# 🚀 Pipeline de Dados com Delta Lake & dbt (CredOn)

Este projeto implementa um pipeline de dados ponta a ponta na arquitetura **Medallion (Bronze, Delta/Silver, Gold)**. Ele realiza a ingestão de dados brutos com ruídos (simulando falhas reais do sistema), aplica tratamento de formatos e tipos, persiste as camadas localmente em **Delta Lake** e **Parquet**, e aplica testes de qualidade de dados.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.10+
* **Manipulação de Dados:** Pandas, PyArrow
* **Storage Engine:** Delta Lake (`deltalake`)
* **Transformação SQL / Data Modeling:** dbt-core / dbt-duckdb
* **Formato de Armazenamento:** Parquet / Delta

---
###  Instalar as dependências do projeto

Para instalar todas as dependências do projeto, crie um arquivo chamado `requirements.txt` na raiz do projeto com o seguinte conteúdo:

```text
pandas
numpy
deltalake
pyarrow
dbt-duckdb
```

## 🚀 Executando o Pipeline

### Passagem 1: Pipeline Python & Delta Lake


```bash
python src/pipeline.py
```

Executar as transformações dos modelos SQL
```bash
dbt run
```
Executar testes de qualidade configurados no dbt

```bash
dbt test
```
O script `src/delta_manager.py` executa a carga bruta, aplica a limpeza de dados e persiste as tabelas no **Delta Lake**:

```bash
python src/delta_manager.py