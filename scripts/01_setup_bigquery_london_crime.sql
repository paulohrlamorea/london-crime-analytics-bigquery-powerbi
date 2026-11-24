-- 1. Criar o Dataset no seu projeto
CREATE SCHEMA IF NOT EXISTS `seu-projeto-id.london_crime_dw`
OPTIONS(
  location = 'US',
  description = 'Base analítica de crimes em Londres para integração Python e Power BI'
);

-- 2. Criar e popular a tabela analítica estruturada
CREATE OR REPLACE TABLE `seu-projeto-id.london_crime_dw.tb_london_crime` AS
SELECT
  lsoa_code,
  borough,
  major_category,
  minor_category,
  CAST(value AS INT64) AS total_crimes,
  CAST(year AS INT64) AS year,
  CAST(month AS INT64) AS month,
  PARSE_DATE('%Y-%m-%d', CONCAT(CAST(year AS STRING), '-', LPAD(CAST(month AS STRING), 2, '0'), '-01')) AS reference_date
FROM `bigquery-public-data.london_crime.crime_by_lsoa`
WHERE value IS NOT NULL;

-- 3. Validação do Schema e Tipos de Dados
SELECT
  column_name,
  data_type,
  is_nullable
FROM `seu-projeto-id.london_crime_dw.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'tb_london_crime';

-- 4. Auditoria de Volume e Consistência
SELECT
  COUNT(*) AS total_registros,
  SUM(total_crimes) AS soma_ocorrencias,
  MIN(year) AS ano_inicial,
  MAX(year) AS ano_final,
  COUNT(DISTINCT borough) AS qtd_bairros,
  COUNT(DISTINCT major_category) AS qtd_categorias
FROM `seu-projeto-id.london_crime_dw.tb_london_crime`;