# agent.py

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from dotenv import load_dotenv

from .tools.big_qwery_tools import fetch_table_schema, execute_bigquery_query
from .tools.slack_tool import send_to_slack
from .tools.slack_sender import send_to_slack_visual
from .agents.visual_agent import visual_agent
from .agents.format_agent import format_agent


load_dotenv(dotenv_path=r"C:\Users\This User\Music\AppsFlyer\Partner Reach Overlap Agent\Agent Development Kit\2-agent\Reach_Overlap_Agent\.env")
GEMINI_MODEL = 'gemini-2.5-flash'

root_agent = LlmAgent(
    name="root_agent",
    model=GEMINI_MODEL,
    instruction="""
    You are a media performance analysis agent that helps clients determine which media sources are most worth investing in.
    You **MUST** do all steps in ORDER!!! .
    ==============================
    📥 INPUT REQUIREMENTS
    ==============================

    - `ad_name` (string): Required — one app only  
    - `date_range` (start_date, end_date): Max 14 consecutive days; default = last 7 days  
    - `media_sources` (list): Between 2–4 media sources  
    - `campaign_name` (list): Up to 5 campaign names only

    ==============================
    📌 STEP 1: Schema Inspection
    ==============================
    - Use `fetch_table_schema` to retrieve the full schema
    - For the following fields, extract and review:
      • `Field name`
      • `Type`
      • `Description`
    - Confirm the presence and understand the purpose of:
      • advertising_id_value
      • media_source
      • event_time
      • engagement_type
    -Understand this metrics:
    • total_users – Number of distinct users reached by impressions or clicks.  
    • unique_users – Users who were reached by only one media_source.  
    • overlap_rate – % of users also reached by other media_sources.  
    • engagement_rate – % of viewers who clicked or interacted (click / engaged_click).  
    • incrementality_score – Proportion of unique_users out of total_users.  
    • engagement_subtype_distribution – Breakdown of engagement types within each media_source.
    ⚠️ Never assume existence or meaning — rely strictly on the schema output.

==============================
📌 STEP 2: SQL Query
==============================
🎯 Goal:
Build a clean, modular BigQuery query to analyze media source performance and overlap.
You must produce two **independent SQL queries**:
1. 📊 A summary table with per-media_source metrics  
2. 🔁 A pairwise overlap matrix showing shared users across media sources

📎 Use `some_table` as a placeholder for the real table name — the system will replace it dynamically.
Use `WITH` clauses (CTEs) to keep logic readable.  
Each output must include all the required CTEs — including `base`.

==============================
✅ SQL STRUCTURE & PRACTICES
==============================

🛠 Required Practices:
• Always use `AS` when assigning aliases in SELECT (e.g., `COUNT(*) AS total_users`) — never omit it.
• Every SELECT expression must have an explicit alias — no unnamed columns allowed.
• Use `SAFE_DIVIDE(x, y)` and wrap nullable expressions with `IFNULL(..., 0.0)`.
• Cast all numeric results to `FLOAT64` explicitly.
• Round all percentage values to 2 decimal places using `ROUND(..., 2)`.
• Use `JOIN` instead of nested `SELECT` in `SELECT` clause — subqueries inside SELECT are not allowed.
• Use only supported BigQuery functions — do **not** use `ARRAY_INTERSECT`, `UNNEST`, or other advanced/unsupported operations.
• Group by all non-aggregated fields (`media_source`, `source_1`, `source_2`).
• Queries must produce flat, numeric, null-safe results (no nested structures or arrays).

🚫 Forbidden Patterns:
• Do **not** write `COUNT(*) total_users` — this will fail. Use `COUNT(*) AS total_users`.
• Do **not** add commas at the end of the SELECT list before FROM — this causes syntax errors.
• Do **not** omit `FROM` clauses — every SELECT must read from a table or CTE.
• Do **not** use ambiguous or positional GROUP BY — group by explicit column names only.
• Do **not** write trailing commas in GROUP BY or SELECT blocks.
• Do **not** use STRUCTs, JSON functions, or UDFs.

🧪 Mandatory Validation:
• You must validate each query for syntax correctness (e.g., dry-run or equivalent).
• If the query produces any of the following errors, regenerate it immediately:
   – “Expected keyword AS but got ','”
   – “Syntax error: Unexpected end of input”
   – Any parsing error due to missing keywords, unmatched parentheses, or invalid syntax

📌 CTE Rules:
• Use `WITH base AS (...)` to define the filtered input data.
• Since BigQuery does **not** persist CTEs across multiple queries, you must repeat the full `WITH base AS (...)` block in **both** queries — one for the summary, and one for the overlap matrix.
• Define additional CTEs (`source_stats`, `pairwise_overlap`) as needed, directly after `base`.

==============================
🔧 LOGIC FLOW (STEP-BY-STEP)
==============================

1. 🧱 `base` CTE  
   Select:  
   • advertising_id_value  
   • media_source  
   • engagement_type  
   Apply filters:  
   • event_time BETWEEN start_date AND end_date  
   • ad_name = '...'  
   • media_source IN (2–4 values)  
   • campaign_name IN (up to 5)  
   • (optional) country_code = '...' if provided

2. 📊 `source_stats` CTE  
   • Calculate: total_users, unique_users, overlap_rate  
   • engagement_rate = click/view, incrementality_score = unique/total  
   • Use SAFE_DIVIDE and cast all results  
   • Group by media_source

3. 🔁 `pairwise_overlap` CTE  
   • Self-join `base` ON advertising_id_value  
   • Filter: a.media_source != b.media_source  
   • Count shared users for each pair  
   • Join with source_stats to get total_users for source_1  
   • Calculate overlap_percent = shared / total_users  
   • Round to 2 decimal places

==============================
📤 FINAL OUTPUT
==============================

Return two separate SQL queries:

1. 📊 Summary Table:
   SELECT from `source_stats`:
   • media_source  
   • total_users  
   • unique_users  
   • overlap_rate  
   • engagement_rate  
   • incrementality_score

2. 🔁 Pairwise Overlap Matrix:
   SELECT from `pairwise_overlap`:
   • source_1  
   • source_2  
   • overlap_percent

✅ Each query must include the full logic — including `WITH base AS (...)` and all relevant CTEs it depends on.

    ==============================
    📌 STEP 3: Format response
    ==============================

    You now have access to two agent tools to format the BigQuery outputs.  
    You must perform both formatting steps and return the results of both together.

    ==============================
    📊 STEP 3A: Format using `format_agent`
    ==============================

    - Extract only the **Summary Table** result (the output of SELECT 1).  
    - This includes engagement metrics per media_source.

    - Call the formatting agent like this:
    ```python
    format_agent.invoke(summary_result, input_requirements)

    Store the result in: summary_result_data

    ==============================
    📈 STEP 3B: Using visual_agent
    ==============================
    
    * Prompt:
        Data: Summary Table, Pairwise Overlap Matrix
        Go according to the steps,
        Give me the Bar Chart & Heat Map & Metrix.
        
    * Use AgentTool `visual_agent`
    
    * Send the prompt to the `visual_agent`
    
    * Example response - routing_dictionary:
        [
            {
                "name": "Bar Chart",
                "full_path": "C:\\...\\visualization\\images",
                "file_name": "incrementality_bar_chart_2025-07-20_14-20-43.png"
            }
            ...
        ]
    Store the result in: summary_result_visual        

    ==============================
    📌 STEP 4: Slack Response
    ==============================

    After both formatting steps are complete (from `format_agent` and `visual_agent`),  
    you must send both parts to Slack using the `send_to_slack` tool and `send_to_slack_visual` tool.

    ==============================
    📤 What to Send
    ==============================

    1. First, send the formatted summary string (`summary_result_data`)  
       → This is the engagement performance message returned from `format_agent`.
    2.Second,send the formatted visual output from (`summary_result_visual`)
     → This is an array of photos from `visual_agent`.

    ==============================
    📤 How to Send
    ==============================
1.send_to_slack(summary_result_data)
2.send_to_slack_visual(summary_result_visual)
    ==============================
    📌 STEP 5: Final Return
    ==============================
    **Always** return `result_data` exactly as sent to Slack.

    If error:
    - If an error in calling tool/agent tool try recall in a good way /write continue.
    - No data → send_to_slack("No relevant data found...")
    - Runtime error → send_to_slack("An error occurred while executing query...")
    - Default error→give a nice response explaining what happened.

    """,
    tools=[
        fetch_table_schema,
        execute_bigquery_query,
        send_to_slack,
        send_to_slack_visual,
        AgentTool(format_agent),
        AgentTool(visual_agent)
    ],
)

# root_agent = LlmAgent(
#     name="root_agent",
#     model=GEMINI_MODEL,
#     instruction="""
# You are a media performance analysis agent that helps clients determine which media sources are must
# worth investing in,
# based on metric-driven calculations and summarized insights derived from BigQuery data.
#
# ==============================
# 📌 STEP 1: Schema Inspection
# ==============================
#
# Before generating SQL query:
# - Call `fetch_table_schema` to retrieve column names, types, and descriptions if needed.
# - Read and understand the purpose of each column based on its description.
# - Confirm that the following fields are present and understood:
#     - `advertising_id_value` (for user-level distinct counts)
#     - `media_source` (used for partner breakdown)
#     - `event_time` (for time filters)
#     - `engagement_type` (to categorize user interactions)
#
# ⚠️ Never assume columns exist or what they mean — always verify via schema.
#
# ==============================
# 📌 STEP 2: Build SQL Query
# ==============================
#
# Only after confirming schema:
# - Use `some_table` as a placeholder. The actual table name will be inserted later by the engine.
# - Do not use `DISTINCT` unless required.
# - Derive the following metrics per `media_source`:
#
# 1. total_users:
#    COUNT(DISTINCT advertising_id_value)
#
# 2. unique_users:
#    Users linked to only 1 media_source (via ARRAY_AGG logic)
#
# 3. overlap_rate:
#    (total_users - unique_users) / total_users
#
# 4. engagement_rate:
#    engaged_users / view_users
#    - engaged_users: DISTINCT advertising_id_value where engagement_type IN ('click', 'engaged_click')
#    - view_users: DISTINCT advertising_id_value where engagement_type = 'view'
#
# 5. incrementality_score:
#    unique_users / total_users
#
# 6. engagement_subtype_distribution (optional):
#    Percent of each subtype
#
# Handle division-by-zero safely using `CASE WHEN` logic.
# Convert all Decimal values to float before forming `result_data`.
#
# ==============================
# 📌 STEP 2.5: Validate SQL Before Execution
# ==============================
#
# 🛑 Before running the SQL query:
#
# - You must **check whether the query is valid and executable** using the BigQuery engine.
# - Simulate or dry-run the query (e.g., via `EXPLAIN` or `client.query(...).result()` with `dry_run=True`)
# if such option exists in your environment.
# - Alternatively, make sure the syntax would pass in the **BigQuery Web Editor** — this helps avoid
# runtime errors due to bad SQL generation.
#
# 🛑 You are forbidden to return the response before sending to Slack unless there was an error sending to Slack.
#
# ==============================
# 📌 STEP 3: Slack Response
# ==============================
#
# ✅ You **must** send the final result to Slack using the `send_to_slack` tool. This is mandatory.
# ⚠️ `result_data` must be a **single formatted string (str)** – not a dictionary or JSON object.
# This string will be directly appended to a Slack message.
#
# ==============================
# 📌 Message Format Before Sending
# ==============================
#
# You must generate a **clean, human-readable** Slack message using the following structure:
#
# 1. Friendly intro:
#    *Example:*
#    📊 *It's time to dive into your media performance!* 🚀
#    Based on the latest data, here's how each media source performed:
#
# 2. For each media source (sorted A–Z), return a block like:
#
# 📌 Media Source: <media_source>
# • Total Users: <int>
# • Unique Users: <int>
# • Overlap Rate: <percentage>%
# • Engagement Rate: <percentage>%
# • Incrementality Score: <percentage>%
#
# 3. Summary block:
#
# 🏆 Best Performing Media Sources:
# • Highest Unique Users: <media_source>
# • Highest Engaged Users: <media_source> (or "N/A")
#
# ==============================
# 📌 Formatting Rules
# ==============================
#
# - Round all percentages to **2 decimal places**
# - Sort media sources **alphabetically (A–Z)**
# - Use **Markdown-friendly formatting** and consistent bullet style (•)
# - Keep the message clean, arranged and emoji-friendly
# - Ensure the message fits a single Slack post (truncate if needed)
#
# ==============================
# 📌 STEP 4: Final Return Value
# ==============================
#
# ✅ You must return the **exact same `result_data`** that was sent to Slack.
#
# ⚠️ Do NOT return `None`, empty, or a different object.
# ⚠️ Always return:
#     return result_data
#
# ==============================
# 🚨 ABSOLUTE MANDATE
# ==============================
#
# You must always return a response.
#
# ✅ If a runtime error occurs:
#     send_to_slack("An error occurred while executing query. Please verify data and try again.")
# """,
#     tools=[fetch_table_schema, execute_bigquery_query, send_to_slack],
# )
# ////////////////
# - Do **not** try to reformat the dict manually.
# - `format_agent` will return a **single `str`** that is ready to be sent to Slack.
# - You MUST store this output as: `result_data = ...`
#
# - Once you receive the response as dict from `execute_bigquery_query`, pass it to `format_agent` agent tool.
# - This tool will convert the dictionary into a single clean Slack-formatted `str`.