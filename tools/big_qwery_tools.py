from typing import List, Dict

from google.cloud import bigquery
import os
import re
import pandas as pd
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()


def fetch_table_schema() -> list[dict]:
    client, proj, ds, tbl = connect_db()
    table_ref = f"{proj}.{ds}.{tbl}"
    table = client.get_table(table_ref)

    return [
        {
            "Field name": field.name,
            "Type": field.field_type,
            "Description": field.description or ""
        }
        for field in table.schema
    ]


def convert_decimal(obj):
    """
    Recursively convert Decimal values to float inside nested dicts/lists.
    """
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal(i) for i in obj]
    else:
        return obj


def execute_bigquery_query(sql_query: str) -> dict:
    """
    Executes a SQL query on a BigQuery table, replacing 'FROM some_table' with the actual table reference
    from environment variables.

    Returns results as JSON-serializable dict, converting Decimal and NaNs.
    """
    try:
        client, proj, ds, tbl = connect_db()
        table_ref = f"`{proj}.{ds}.{tbl}`"

        # Replace placeholder with full table path
        sql_query = re.sub(
            r"\s*\n*\s*some_table",
            f" {table_ref}",
            sql_query,
            flags=re.IGNORECASE
        )

        if "LIMIT" not in sql_query.upper() and "SELECT" in sql_query.upper():
            sql_query = sql_query.rstrip("; \n")

        print(f"--- Tool: execute_bigquery_query called ---")
        print(f"Query: {sql_query}")

        query_job = client.query(sql_query)
        df = query_job.to_dataframe()
        df = df.where(pd.notnull(df), None)

        # Convert all Decimal to float
        data = convert_decimal(df.head(10000).to_dict('records'))

        return {
            "status": "success",
            "query": sql_query,
            "row_count": len(data),
            "columns": df.columns.tolist(),
            "data": data,
            "total_rows": len(df)
        }

    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "query": sql_query
        }


def connect_db() -> list:
    key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not key_path:
        raise RuntimeError("Missing GOOGLE_APPLICATION_CREDENTIALS in .env!")

    proj = os.getenv("GOOGLE_CLOUD_PROJECT")
    ds = os.getenv("DATASET_ID")
    tbl = os.getenv("TABLE_ID")

    try:
        client = bigquery.Client(proj)
        return [client, proj, ds, tbl]

    except Exception as e:
        raise Exception(f"Error initializing BigQuery client: {e}")


def generate_queries(start_date: str, end_date: str, ad_name: str, media_sources: List[str], campaign_names: List[str]):
    media_sources_sql = ', '.join(f"'{s}'" for s in media_sources)
    campaign_names_sql = ', '.join(f"'{c}'" for c in campaign_names)
    try:
        client, proj, ds, tbl = connect_db()
        table_ref = f"`{proj}.{ds}.{tbl}`"
        base_cte = f"""
WITH base AS (
  SELECT
    advertising_id_value,
    media_source,
    engagement_type
  FROM
    {table_ref}
  WHERE
    event_time BETWEEN '{start_date}' AND '{end_date}'
    AND ad_name = '{ad_name}'
    AND media_source IN UNNEST([ {media_sources_sql} ])
    AND campaign_name IN UNNEST([ {campaign_names_sql} ])
),

deduped AS (
  SELECT DISTINCT
    advertising_id_value,
    media_source,
    engagement_type
  FROM
    base
)
"""

        # Query 1: Summary Table
        summary_query = base_cte + """

, user_counts AS (
  SELECT
    media_source,
    COUNT(DISTINCT advertising_id_value) AS total_users
  FROM
    deduped
  GROUP BY
    media_source
),

unique_users AS (
  SELECT
    advertising_id_value
  FROM
    deduped
  GROUP BY
    advertising_id_value
  HAVING
    COUNT(DISTINCT media_source) = 1
),

unique_counts AS (
  SELECT
    d.media_source,
    COUNT(DISTINCT d.advertising_id_value) AS unique_users
  FROM
    deduped d
  JOIN
    unique_users u
  ON
    d.advertising_id_value = u.advertising_id_value
  GROUP BY
    d.media_source
),

engagement AS (
  SELECT
    media_source,
    COUNTIF(engagement_type = 'click') AS clicks,
    COUNTIF(engagement_type = 'view') AS impressions
  FROM
    deduped
  GROUP BY
    media_source
),

source_stats AS (
  SELECT
    u.media_source,
    CAST(u.total_users AS FLOAT64) AS total_users,
    CAST(IFNULL(uc.unique_users, 0) AS FLOAT64) AS unique_users,
    ROUND(SAFE_DIVIDE(u.total_users - IFNULL(uc.unique_users, 0), u.total_users) * 100, 2) AS overlap_rate,
    ROUND(SAFE_DIVIDE(IFNULL(e.clicks, 0), NULLIF(e.impressions, 0)) * 100, 2) AS engagement_rate,
    ROUND(SAFE_DIVIDE(IFNULL(uc.unique_users, 0), u.total_users) * 100, 2) AS incremental_score
  FROM
    user_counts u
  LEFT JOIN
    unique_counts uc ON u.media_source = uc.media_source
  LEFT JOIN
    engagement e ON u.media_source = e.media_source
)

SELECT
  media_source,
  total_users,
  unique_users,
  overlap_rate,
  engagement_rate,
  incremental_score
FROM
  source_stats
ORDER BY
  media_source;
"""
        print("*****************************************\n", summary_query)
        # Query 2: Pairwise Overlap Matrix
        overlap_query = base_cte + """

, pairwise_overlap AS (
  SELECT
    a.media_source AS source_1,
    b.media_source AS source_2,
    COUNT(DISTINCT a.advertising_id_value) AS shared_users
  FROM
    deduped a
  JOIN
    deduped b
  ON
    a.advertising_id_value = b.advertising_id_value
    AND a.media_source != b.media_source
  GROUP BY
    source_1, source_2
),

user_counts AS (
  SELECT
    media_source,
    COUNT(DISTINCT advertising_id_value) AS total_users
  FROM
    deduped
  GROUP BY
    media_source
)

SELECT
  p.source_1,
  p.source_2,
  ROUND(SAFE_DIVIDE(p.shared_users, NULLIF(u.total_users, 0)) * 100, 2) AS overlap_percent
FROM
  pairwise_overlap p
JOIN
  user_counts u
ON
  p.source_1 = u.media_source
ORDER BY
  source_1, source_2;
"""
        print("*****************************************\n", overlap_query)

        query_job_1 = client.query(summary_query)
        query_job_2 = client.query(overlap_query)

        summary_table = query_job_1.to_dataframe()
        summary_table = summary_table.where(pd.notnull(summary_table), None)
        pairwise_overlap = query_job_2.to_dataframe()
        pairwise_overlap = pairwise_overlap.where(pd.notnull(pairwise_overlap), None)

        return {
            "status": "success",
            "data": {
                "summary_table": summary_table.to_dict(orient="records"),
                "pairwise_overlap": pairwise_overlap.to_dict(orient="records")
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
        }
