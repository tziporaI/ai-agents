from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from dotenv import load_dotenv
load_dotenv(dotenv_path=r"C:\Users\This User\Music\AppsFlyer\Partner Reach Overlap Agent\Agent Development Kit\2-agent\Reach_Overlap_Agent\.env")
GEMINI_MODEL = 'gemini-2.5-flash'

google_search_agent = LlmAgent(
    name="google_search_agent",
    model='gemini-2.5-flash',
    description="Agent that finds external information using Google Search.",
    instruction="""
You are a web search assistant. Your task is to perform Google searches based on user queries and return the most relevant and concise explanation from the web.

- Always return clear and factual answers.
- Do not generate SQL or assume values.
- Focus only on answering what the user asked using external sources.
""",
    tools=[google_search]
)
