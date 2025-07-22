import json
import os
import requests
from dotenv import load_dotenv
load_dotenv(dotenv_path=r"C:\Users\This User\Music\AppsFlyer\Partner Reach Overlap Agent\Agent Development Kit\2-agent\Reach_Overlap_Agent\.env")


SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")


# send data
def send_to_slack(result_data: str) -> str:
    """Send the agent's final result to a fixed Slack channel.{testing_agent}"""
    url = 'https://slack.com/api/chat.postMessage'
    channel = '#testing-agent'

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {SLACK_BOT_TOKEN}'
    }
    message = "📊 *Partner Reach Overlap Result:*\n" + result_data

    # message = "📊 *Partner Reach Overlap Result:*\n```" + json.dumps(result_data, indent=2) + "```"

    payload = {
        'channel': channel,
        'text': message
    }

    response = requests.post(url, headers=headers, json=payload)

    if not response.ok or not response.json().get("ok"):
        raise Exception("Slack API Error: " + response.text)
