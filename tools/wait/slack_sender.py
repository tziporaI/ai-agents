# slack_sender.py

import os
import base64
from slack_sdk import WebClient
from io import BytesIO

def send_to_slack_visual(routing_image: list[dict]) -> dict:
    """
    Uploads one or more base64-encoded chart images to a predefined Slack channel.

    Each input dict must contain:
        - "image_base64" (str): Base64-encoded PNG image
        - "file_name" (str): Filename for Slack
        - "name" (str): Human-readable chart label

    Decodes the image to BytesIO and sends via Slack API.

    Returns:
    --------
    dict :
        { "status": "success" }
    """
    slack_token = os.getenv("SLACK_BOT_TOKEN")
    channel_id = os.getenv("CHANNEL_ID")

    client = WebClient(token=slack_token)

    for item in routing_image:
        base64_str = item["image_base64"]
        file_name = item["file_name"]
        name = item["name"]

        image_data = base64.b64decode(base64_str)
        image_stream = BytesIO(image_data)

        client.files_upload(
            channels=channel_id,
            file=image_stream,
            filename=file_name,
            title=file_name,
            initial_comment=f"📊 Visualization - {name}"
        )

    return {"status": "success"}

