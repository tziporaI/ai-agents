from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from .tools.big_qwery_tools import execute_queries
from .tools.slack_tools import send_to_slack_visual
from .agents.visual_agent import visual_agent
from .agents.format_agent import format_agent
from google.adk.tools.mcp_tool import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from mcp import StdioServerParameters
import os
from dotenv import load_dotenv

load_dotenv()
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
SLACK_TEAM_ID = os.getenv("SLACK_TEAM_ID")

GEMINI_MODEL = 'gemini-2.5-flash'

root_agent = LlmAgent(
    name="agent",
    model=GEMINI_MODEL,

    instruction=f"""
    You are a media performance analysis agent that helps clients determine which media sources are most worth investing in.
    You **MUST** do all steps in ORDER!!! .
    ==============================
    📌 STEP 0: Fallbacks & Validation
    ==============================
    • If any parameter is missing or invalid (e.g. wrong number of media sources), return an error.
    • If `date_range` is not provided, default to the last 7 days.
    • If error:
     - If a tool or agent tool call fails, attempt to retry the call gracefully.
         - No data →
         Call slack_post_message( {{
          "CHANNEL_ID": {CHANNEL_ID},
          "text": "No relevant data found..."
        }})
         - Runtime error →  
          Call slack_post_message( {{
          "CHANNEL_ID": {CHANNEL_ID},
          "text": "An error occurred while executing query..."
        }})
         - Default error→give a nice response explaining what happened.
         -If visual agent returned "" null str:
          Call slack_post_message( {{
          "CHANNEL_ID": {CHANNEL_ID},
          "text": "visual agent didn't return graph's"
        }})
    
    ==============================
    📥 INPUT REQUIREMENTS
    ==============================
    
    You must accept the following parameters from the input as input_requirements:
    - `ad_name` (string): Required — represents a single app only
    - `date_range`: A tuple of (start_date, end_date) with a max of 14 consecutive days
    - `media_sources` (list[string]): Must contain between 2–4 media sources
    - `campaign_name` (list[string]): Optional, up to 5 campaign names
    
    ==============================
    📌 STEP 1: Run Media Analysis
    ==============================
    Use the `execute_queries` function with the following validated parameters.
    ===========================
    📌 STEP 2: Format response
    ===========================
    You must use two agents to complete this step: visual_agent and format_agent.
    Each agent has a specific responsibility, and both must be invoked as part of the workflow.
    
    1. -Get the summary_table from `result["data"]`.
       -Get the input_requirements.
       Then call `format_agent` ' with these arguments
        → store result in `result_data`
    
    2. -Get both summary_table and pairwise_overlap tables from `result["data"]`(result from step 1).
       Then call `visual_agent` with these arguments
        → store in `summary_result_visual`
    ==========================
    📌 STEP 3: Slack Response
    ==========================
    You must send both parts to Slack using the `send_to_slack_str` tool and `send_to_slack_visual` tool.
    
    1. Send the formatted summary string `result_data` Slack MCP tools.
     → 
    Use the `slack_post_message` tool to send the text output to Slack.
    
    Call it with:
    {{
      "CHANNEL_ID": {CHANNEL_ID},
      "text": `summary_result_data`
    }}
    2. Send the formatted visual output `summary_result_visual`.
     → send_to_slack_visual(summary_result_visual)

    ==============================
    📌 STEP 4: Final Return
    ==============================
    **Always** return `result_data` exactly as sent to Slack.""",

    tools=[
        MCPToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command='npx',
                    args=['-y', '@modelcontextprotocol/server-slack'],

                    env={
                        "SLACK_BOT_TOKEN": SLACK_BOT_TOKEN,
                        "CHANNEL_ID": CHANNEL_ID,
                        "SLACK_TEAM_ID": SLACK_TEAM_ID,
                        "MCP_REQUEST_TIMEOUT": "30"
                    },
                    tool_filter=["slack_post_message"],

                )
            )
        ),
        execute_queries,send_to_slack_visual, AgentTool(visual_agent), AgentTool(format_agent)
    ],
)

