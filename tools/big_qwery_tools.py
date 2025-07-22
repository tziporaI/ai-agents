from google.cloud import bigquery
import os
import re
import pandas as pd
from decimal import Decimal
from dotenv import load_dotenv
load_dotenv(dotenv_path=r"C:\Users\This User\Music\AppsFlyer\Partner Reach Overlap Agent\Agent Development Kit\2-agent\Reach_Overlap_Agent\.env")


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
