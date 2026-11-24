"""
aula3_limpeza_padronizacao.py
=====================================================

OBJETIVO
--------
Este script realiza o processo completo de extração,
limpeza e padronização dos dados dos Objetivos de
Desenvolvimento Sustentável (ODS) da ONU, armazenados
no Google BigQuery.

ETAPAS DO PIPELINE
------------------
1. Conexão com o BigQuery
2. Extração do dataset bruto
3. Padronização de nomes de colunas
4. Remoção de colunas sem valores
5. Limpeza semântica da coluna de valores
6. Ajuste de tipos de dados
7. Salvamento do dataset final (camada READY)

O resultado é um dataset limpo, auditável e pronto
para análise, BI ou modelagem.

Autor: Prof. Rodrigo Garcia Brunini
"""

# =====================================================
# 1. IMPORTAÇÕES
# =====================================================
# google-cloud-bigquery -> conexão e execução de queries
# pandas                -> manipulação e limpeza de dados
# os, sys               -> controle de paths e debug
# re                    -> padronização de strings
# =====================================================

from google.cloud import bigquery
import pandas as pd
import os
import sys
import re

# =====================================================
# 2. CONFIGURAÇÕES GERAIS
# =====================================================
# PROJECT_ID : projeto no Google Cloud
# TABLE      : tabela no BigQuery
# OUTPUT     : local onde o dataset limpo será salvo
# =====================================================

PROJECT_ID = "projectonu"
TABLE = "projectonu.tab_onu_brazil.dados_onu_brazil"
DATASET_LOCATION = None  # use "US" ou "EU" se necessário

OUTPUT_PATH = (
    r"C:\Users\Rodrigo\Desktop\ebac_tutoria\revisao"
    r"\Modulo_38\data\ready\dados_ods_limpos.csv"
)

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

# =====================================================
# 3. INFORMAÇÕES DO AMBIENTE (DEBUG)
# =====================================================
# Útil para diagnóstico de problemas de execução,
# versões de Python e credenciais.
# =====================================================

print("=== Ambiente de Execução ===")
print("Python executable:", sys.executable)
print("Python version:", sys.version.splitlines()[0])
print("GOOGLE_APPLICATION_CREDENTIALS:",
      os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
print()

# =====================================================
# 4. CLIENTE BIGQUERY
# =====================================================
# Cria o cliente responsável por executar queries SQL
# diretamente no BigQuery.
# =====================================================

client = bigquery.Client(project=PROJECT_ID)

def run_query(query: str):
    """
    Executa uma query no BigQuery.

    Caso o dataset esteja em uma região específica
    (US, EU, etc.), o parâmetro location é aplicado.

    Parâmetros
    ----------
    query : str
        SQL a ser executado

    Retorno
    -------
    bigquery.job.QueryJob
    """
    if DATASET_LOCATION:
        return client.query(query, location=DATASET_LOCATION)
    return client.query(query)

# =====================================================
# 5. EXTRAÇÃO DO DATASET BRUTO
# =====================================================
# Nesta etapa, os dados são extraídos exatamente como
# estão no BigQuery, sem qualquer tratamento.
# =====================================================

print(">>> Extraindo dados do BigQuery (RAW)")

sql_raw = f"""
SELECT *
FROM {TABLE}
"""

df = run_query(sql_raw).to_dataframe()

print(f"Total de registros extraídos: {len(df)}")
print()

# =====================================================
# 6. PADRONIZAÇÃO DOS NOMES DAS COLUNAS
# =====================================================
# Objetivo:
# - Padronizar nomes para snake_case
# - Evitar espaços, caracteres especiais e maiúsculas
# - Facilitar uso em SQL, pandas, BI e ML
# =====================================================

print(">>> Padronizando nomes das colunas")

def normalize_column(col: str) -> str:
    """
    Normaliza nomes de colunas para snake_case.
    """
    col = col.strip().lower()
    col = re.sub(r"[^\w]+", "_", col)
    col = re.sub(r"_+", "_", col)
    return col.strip("_")

df.columns = [normalize_column(c) for c in df.columns]

# =====================================================
# 7. REMOÇÃO DE COLUNAS SEM VALORES (COM LOG)
# =====================================================
# Remove colunas onde TODOS os valores são nulos.
# Além disso, imprime explicitamente quais colunas
# foram removidas para auditoria e debug.
# =====================================================

print(">>> Removendo colunas totalmente vazias")

cols_before = set(df.columns)

# Remove colunas completamente nulas
df = df.dropna(axis=1, how="all")

cols_after = set(df.columns)

# Identifica colunas removidas
removed_columns = sorted(list(cols_before - cols_after))

print(f"Total de colunas removidas: {len(removed_columns)}")

if removed_columns:
    print("Colunas excluídas:")
    for col in removed_columns:
        print(f"- {col}")
else:
    print("Nenhuma coluna foi removida.")

print()

# =====================================================
# 8. LIMPEZA SEMÂNTICA DA COLUNA 'value'
# =====================================================
# A coluna 'value' contém valores censurados ou
# anotados (>95, <5, ~10).
#
# Estratégia:
# - Preservar o valor original
# - Remover símbolos semânticos
# - Converter para numérico quando possível
# =====================================================

print(">>> Limpando coluna 'value'")

if "value" in df.columns:
    # Preserva rastreabilidade
    df["value_original"] = df["value"]

    # Remove símbolos semânticos
    df["value"] = (
        df["value"]
        .astype(str)
        .str.replace(r"[<>~=]", "", regex=True)
    )

    # Converte para número
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

# =====================================================
# 9. AJUSTE DE TIPOS BÁSICOS
# =====================================================
# Garante que colunas temporais e numéricas estejam
# corretamente tipadas para análises futuras.
# =====================================================

print(">>> Ajustando tipos de dados")

if "timeperiod" in df.columns:
    df["timeperiod"] = pd.to_numeric(
        df["timeperiod"], errors="coerce"
    )

# =====================================================
# 10. REMOÇÃO DE LINHAS TOTALMENTE VAZIAS
# =====================================================
# Remove registros onde todas as colunas são nulas.
# =====================================================

df = df.dropna(how="all")

# =====================================================
# 11. SALVAMENTO DO DATASET LIMPO (READY)
# =====================================================
# O dataset final é salvo em CSV para uso em BI,
# análises exploratórias ou ingestão em outros sistemas.
# =====================================================

print(">>> Salvando dataset limpo")

df.to_csv(OUTPUT_PATH, index=False)

print("Arquivo salvo com sucesso:")
print(OUTPUT_PATH)
print(f"Linhas finais: {len(df)}")
print(f"Colunas finais: {df.shape[1]}")

# =====================================================
# 12. CONSIDERAÇÕES FINAIS
# =====================================================
print("\n>>> Pipeline concluído")
print("- Dataset limpo e padronizado")
print("- Rastreabilidade preservada (value_original)")
print("- Pronto para BI, análises e modelos")
print("- Padrão profissional raw → ready aplicado")
