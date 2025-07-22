# slack_sender.py

from slack_sdk import WebClient
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=r"C:\Users\This User\Music\AppsFlyer\Partner Reach Overlap Agent\Agent Development Kit\2-agent\Reach_Overlap_Agent\.env")


def send_to_slack_visual(routing_image: list[dict]) -> dict:
    """
    Uploads one or more visualization image files to a predefined Slack channel.

    This function takes a list of image metadata dictionaries (as returned by the visual_agent)
    and uploads each image file to Slack using the Slack WebClient API.

    Each image is accompanied by a title (the filename) and a visual type comment (e.g., "Bar Chart").

    Args:
        routing_image (list of dict): A list where each item contains:
            • 'Full Path' (str): Absolute path to the image file on disk.
            • 'Name' (str): Human-readable label for the type of visualization (e.g., "Heat Map").

    Returns:
        dict: A dictionary indicating success:
            {
                "status": "success"
            }

    Raises:
        slack_sdk.errors.SlackApiError: If the upload to Slack fails.
    """
    slack_token = os.getenv("SLACK_BOT_TOKEN")
    channel_id = os.getenv("CHANNEL_ID")

    client = WebClient(token=slack_token)

    for row in routing_image:
        file_path = os.path.join(row["full_path"], row["file_name"])
        client.files_upload_v2(
            channel=channel_id,
            file=file_path,
            title=os.path.basename(file_path),
            initial_comment="📊 Visualization - " + row["name"]
        )
    return {
        "status": "success"
    }
