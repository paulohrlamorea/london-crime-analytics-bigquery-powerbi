"""
aula2_importacao_onu.py

Script didático para executar queries no Google BigQuery usando Python
sobre dados da ONU (ODS), visualizar resultados com pandas e salvar
saídas em CSV e Parquet.

Dataset: Indicadores ONU – Brasil
Autor: Prof. Rodrigo Garcia Brunini
"""

# ======================
# Imports
# ======================
from google.cloud import bigquery
import pandas as pd
import os
import sys

# ======================
# Configurações
# ======================
PROJECT_ID = "projectonu"
TABLE = "projectonu.tab_onu_brazil.dados_onu_brazil"
DATASET_LOCATION = None  # ajuste se necessário

# ======================
# Ambiente / Debug
# ======================
print("=== Ambiente de Execução ===")
print("Python executable:", sys.executable)
print("Python version:", sys.version.splitlines()[0])
print("GOOGLE_APPLICATION_CREDENTIALS:",
      os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
print()

# ======================
# Cliente BigQuery
# ======================
client = bigquery.Client(project=PROJECT_ID)

def run_query(query: str) -> bigquery.job.QueryJob:
    """
    Executa uma query no BigQuery respeitando a região do dataset.
    """
    if DATASET_LOCATION:
        return client.query(query, location=DATASET_LOCATION)
    return client.query(query)

# ======================================================
# Query 1 — Preview dos dados
# ======================================================
print(">>> Query 1: Preview (10 linhas)")

sql_preview = f"""
SELECT
  goal,
  target,
  indicator,
  seriescode,
  geoareaname,
  timeperiod,
  value,
  units,
  sex
FROM {TABLE}
LIMIT 10
"""

df_preview = run_query(sql_preview).to_dataframe()
print(df_preview.to_string(index=False))
print()

# ======================================================
# Extração do dataset bruto (sem limpeza)
# ======================================================
print(">>> Extração do dataset bruto (RAW)")

sql_raw = f"""
SELECT *
FROM {TABLE}
"""

df_raw = run_query(sql_raw).to_dataframe()

RAW_OUTPUT_PATH = (
    r"C:\Users\Rodrigo\Desktop\ebac_tutoria\revisao"
    r"\Modulo_38\data\raw\dados_onu_brazil_raw.csv"
)

os.makedirs(os.path.dirname(RAW_OUTPUT_PATH), exist_ok=True)

df_raw.to_csv(RAW_OUTPUT_PATH, index=False)

print(f"Dataset RAW salvo em:\n{RAW_OUTPUT_PATH}")
print(f"Total de registros RAW: {len(df_raw)}")
print()


# ======================================================
# Query 2 — Agregação por indicador (Brasil)
# ======================================================
print(">>> Query 2: Média do valor por indicador (Brasil)")

sql_agg = f"""
WITH cleaned AS (
  SELECT
    seriescode,
    seriesdescription,
    units,
    SAFE_CAST(
      REGEXP_REPLACE(value, r'[<>~=]', '')
      AS FLOAT64
    ) AS value_num
  FROM {TABLE}
  WHERE geoareaname = 'Brazil'
)
SELECT
  seriescode,
  seriesdescription,
  units,
  COUNT(value_num) AS qtd_registros_validos,
  ROUND(AVG(value_num), 2) AS media_valor
FROM cleaned
WHERE value_num IS NOT NULL
GROUP BY seriescode, seriesdescription, units
ORDER BY media_valor DESC
LIMIT 20
"""


df_agg = run_query(sql_agg).to_dataframe()
print(df_agg.to_string(index=False))
print()

# ======================================================
# Query 3 — Série temporal de um indicador específico
# ======================================================
print(">>> Query 3: Série temporal (exemplo de indicador)")

INDICATOR_EXAMPLE = "SI_POV_EMP1"

sql_ts = f"""
WITH cleaned AS (
  SELECT
    timeperiod AS year,
    sex,
    SAFE_CAST(
      REGEXP_REPLACE(value, r'[<>~=]', '')
      AS FLOAT64
    ) AS value_num
  FROM {TABLE}
  WHERE geoareaname = 'Brazil'
    AND seriescode = '{INDICATOR_EXAMPLE}'
)
SELECT
  year,
  sex,
  value_num AS value
FROM cleaned
WHERE value_num IS NOT NULL
ORDER BY year
"""


df_ts = run_query(sql_ts).to_dataframe()
df_ts["year"] = pd.to_numeric(df_ts["year"], errors="coerce")

print(df_ts.tail(10).to_string(index=False))
print()


# ======================================================
# Dicas finais
# ======================================================
print(">>> Dicas finais")
print("- Dataset ONU é longitudinal e categórico: explore séries e segmentações.")
print("- Prefira Parquet para séries temporais e análises analíticas.")
print("- Sempre valide units antes de comparar indicadores diferentes.")
