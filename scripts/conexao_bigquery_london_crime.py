"""
conexao_bigquery_london_crime.py
===============================================================================
OBJETIVO:
Integração entre Google BigQuery e Python para extração, validação de qualidade,
tratamento e exportação da base analítica de crimes em Londres (London Crime).
===============================================================================
"""

import os
import sys
import re
import pandas as pd
from google.cloud import bigquery

# =============================================================================
# 1. CONFIGURAÇÕES DO PROJETO E CAMINHOS
# =============================================================================
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "london-crime-analytics-515714")  # <-- Coloque seu Project ID aqui

# Aponta para a tabela que você criou no Passo 1 (ou use 'bigquery-public-data.london_crime.crime_by_lsoa')
SOURCE_TABLE = f"{PROJECT_ID}.london_crime_dw.tb_london_crime"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(BASE_DIR, "data", "raw", "london_crime_raw.csv")
READY_PATH = os.path.join(BASE_DIR, "data", "ready", "london_crime_ready.csv")

os.makedirs(os.path.dirname(RAW_PATH), exist_ok=True)
os.makedirs(os.path.dirname(READY_PATH), exist_ok=True)


# =============================================================================
# 2. CONEXÃO E VALIDAÇÃO DE AMBIENTE
# =============================================================================
def conectar_bigquery(project_id: str) -> bigquery.Client:
    print("=== 1. VERIFICANDO AMBIENTE E CONEXÃO BIGQUERY ===")
    print(f"Python Executable : {sys.executable}")
    print(f"Credenciais GCP   : {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'Via gcloud auth / ADC')}")

    try:
        client = bigquery.Client(project=project_id)
        print(f"Conexão estabelecida com sucesso no projeto: {client.project}\n")
        return client
    except Exception as e:
        print(f"[ERRO] Falha ao conectar ao BigQuery: {e}")
        print("Rode no terminal: gcloud auth application-default login")
        sys.exit(1)


# =============================================================================
# 3. EXECUÇÃO DE QUERIES SQL (VALIDAÇÃO E EXTRAÇÃO)
# =============================================================================
def validar_schema_e_qualidade(client: bigquery.Client, table_name: str) -> pd.DataFrame:
    print("=== 2. EXECUTANDO AUDITORIA E VALIDAÇÃO NO BIGQUERY ===")

    query_validacao = f"""
    SELECT
        COUNT(*) AS total_linhas,
        COUNTIF(borough IS NULL OR borough = '') AS nulos_borough,
        COUNTIF(major_category IS NULL OR major_category = '') AS nulos_categoria,
        COUNTIF(total_crimes IS NULL) AS nulos_crimes,
        MIN(year) AS ano_inicio,
        MAX(year) AS ano_fim,
        SUM(total_crimes) AS total_crimes_registrados
    FROM `{table_name}`
    """

    df_audit = client.query(query_validacao).to_dataframe()
    print(df_audit.to_string(index=False))
    print()
    return df_audit


def extrair_dados_consolidados(client: bigquery.Client, table_name: str) -> pd.DataFrame:
    print("=== 3. EXTRAINDO DADOS ANALÍTICOS DO BIGQUERY ===")

    query_extracao = f"""
    SELECT
        year,
        month,
        reference_date,
        borough,
        major_category,
        minor_category,
        SUM(total_crimes) AS total_crimes
    FROM `{table_name}`
    WHERE total_crimes IS NOT NULL
      AND total_crimes > 0
    GROUP BY
        year,
        month,
        reference_date,
        borough,
        major_category,
        minor_category
    ORDER BY
        year ASC,
        month ASC,
        total_crimes DESC
    """

    df = client.query(query_extracao).to_dataframe()
    print(f"Registros consolidados extraídos: {len(df):,}\n")
    return df


# =============================================================================
# 4. MANIPULAÇÃO, LIMPEZA E PADRONIZAÇÃO (CAMADA RAW -> READY)
# =============================================================================
def tratar_e_salvar_dados(df: pd.DataFrame, raw_path: str, ready_path: str) -> pd.DataFrame:
    print("=== 4. TRATAMENTO E PADRONIZAÇÃO (RAW -> READY) ===")

    df.to_csv(raw_path, index=False, encoding="utf-8")
    print(f"Camada RAW salva em: {raw_path}")

    df_clean = df.copy()
    df_clean.columns = [
        re.sub(r"[^a-zA-Z0-9]+", "_", col.strip().lower()).strip("_")
        for col in df_clean.columns
    ]

    df_clean["year"] = pd.to_numeric(df_clean["year"], errors="coerce").astype("Int64")
    df_clean["month"] = pd.to_numeric(df_clean["month"], errors="coerce").astype("Int64")
    df_clean["total_crimes"] = pd.to_numeric(df_clean["total_crimes"], errors="coerce").fillna(0).astype("int64")
    df_clean["reference_date"] = pd.to_datetime(df_clean["reference_date"])

    for col_texto in ["borough", "major_category", "minor_category"]:
        df_clean[col_texto] = df_clean[col_texto].astype(str).str.strip()

    df_clean = df_clean.dropna(how="all").drop_duplicates()

    df_clean.to_csv(ready_path, index=False, encoding="utf-8")
    print(f"Camada READY salva em: {ready_path}")
    print(f"Total de registros prontos para o Power BI: {len(df_clean):,}\n")

    return df_clean


# =============================================================================
# 5. RESUMO ANALÍTICO PARA CONFERÊNCIA NO POWER BI
# =============================================================================
def gerar_resumo_negocio(df: pd.DataFrame) -> None:
    print("=== 5. RESUMO ANALÍTICO (CONFERÊNCIA DE INDICADORES) ===")

    print("Top 5 Bairros com maior volume de crimes:")
    print(df.groupby("borough")["total_crimes"].sum().sort_values(ascending=False).head(5).to_string())
    print()

    print("Top 5 Categorias de Crime:")
    print(df.groupby("major_category")["total_crimes"].sum().sort_values(ascending=False).head(5).to_string())
    print()


if __name__ == "__main__":
    bq_client = conectar_bigquery(PROJECT_ID)
    validar_schema_e_qualidade(bq_client, SOURCE_TABLE)
    df_bruto = extrair_dados_consolidados(bq_client, SOURCE_TABLE)
    df_pronto = tratar_e_salvar_dados(df_bruto, RAW_PATH, READY_PATH)
    gerar_resumo_negocio(df_pronto)
    print(">>> Pipeline concluído com sucesso! Base pronta para o Power BI.")