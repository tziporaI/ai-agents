from typing import List, Dict
from google.cloud import bigquery
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


def get_table_schema() -> list[dict]:
    """
    Fetches the schema of the target BigQuery table.

    Args:
        None

    Returns:
        list[dict]: A list of dictionaries with field metadata:
            - "Field name"
            - "Type"
            - "Description"
    """

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


def connect_db() -> list:
    """
    Initializes and returns a BigQuery client along with project, dataset, and table identifiers.
    Args:
        None
    Returns:
        list: [bigquery.Client, project_id (str), dataset_id (str), table_id (str)]

    Raises:
        RuntimeError: If required environment variables are missing.
        Exception: If client initialization fails.
    """

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


def execute_queries(start_date: str, end_date: str, ad_name: str, media_sources: List[str], campaign_names: List[str]):
    """
    Runs two BigQuery queries to compute media performance metrics and pairwise user overlap.

    Args:
        start_date (str): Start date for filtering (YYYY-MM-DD).
        end_date (str): End date for filtering (YYYY-MM-DD).
        ad_name (str): Ad name to filter the dataset.
        media_sources (List[str]): List of media sources to include.
        campaign_names (List[str]): List of campaign names to filter by.

    Returns:
        dict: Contains either:
            - "status": "success", with:
                • "summary_table": List of media-level metrics
                • "pairwise_overlap": List of overlap percentages between media sources
            - "status": "error", with "error_message"
    """
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
        if not campaign_names:
            base_cte = base_cte.replace('AND campaign_name IN UNNEST([  ])', '')

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
            ROUND(SAFE_DIVIDE(IFNULL(uc.unique_users, 0), u.total_users), 4) AS incremental_score
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
            "data":{"error_message":str(e)}
        }
