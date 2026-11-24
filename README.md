# London Crime Analytics (BigQuery, Python e Power BI)

Projeto de análise de dados desenvolvido para estruturar, extrair e visualizar ocorrências criminais em Londres (2008–2016) utilizando a base pública `bigquery-public-data.london_crime.crime_by_lsoa`.

## Arquitetura do Projeto

1. **Google BigQuery (SQL):** Criação do dataset `london_crime_dw` e estruturação da tabela analítica `tb_london_crime` com tipagem dos dados (`INT64` e `DATE`) e validações de consistência.
2. **Python (`google-cloud-bigquery` e `pandas`):** Script de conexão via Conta de Serviço (GCP) para consulta, validação e extração dos dados tratados.
3. **Power BI:** Modelagem relacional com tabela `dCalendario`, medidas DAX (`Total Crimes`, `% Participação Total` e `Variação YoY %`) e dashboard executivo com filtro temporal, ranking dos Top 10 bairros e detalhamento por categoria de crime.

## Estrutura das Pastas

- `scripts/`: Código SQL de criação/validação no BigQuery (`01_setup_bigquery_london_crime.sql`) e script Python de extração (`conexao_bigquery_london_crime.py`).
- `dash/`: Arquivo do relatório completo no Power BI (`london_crime_dashboard.pbix`).
- `prints/`: Evidências da execução no BigQuery, terminal Python e dashboard final.

## Como Executar

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
