import os
import json
from slack_sdk.errors import SlackApiError
from slack_sdk import WebClient
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
CHANNEL_NAME = os.getenv("CHANNEL_NAME")
CHANNEL_ID = os.getenv("CHANNEL_ID")


def send_to_slack_str(result_data: str) -> str:
    """
    Sends a string (possibly JSON-formatted) to a fixed Slack channel.
    If result_data looks like JSON, we format it as a code block.
    """
    client = WebClient(token=SLACK_BOT_TOKEN)

    try:
        parsed = json.loads(result_data)
        message = "📊 *Partner Reach Overlap Result:*```json\n" + json.dumps(parsed, indent=2) + "\n```"
    except Exception:
        # Not JSON – just treat as plain text
        message = "📊 *Partner Reach Overlap Result:*" + result_data

    try:
        response = client.chat_postMessage(channel=CHANNEL_NAME, text=message)
        if not response["ok"]:
            raise Exception(f"Slack API error: {response['error']}")
        return "✅ Message sent successfully!"
    except SlackApiError as e:
        raise Exception(f"Slack API error: {e.response['error']}") from e


def send_to_slack_visual(routing_image: list[dict]) -> dict:
    """
    Uploads visualization images to Slack.

    Args:
        routing_image: A list of dicts. Each must contain:
            - name: Chart type (e.g., "Bar Chart")
            - full_path: Full path to the image directory
            - file_name: Name of the image file

    Returns:
        dict: {"status": "success"} if upload completes
    """
    client = WebClient(token=SLACK_BOT_TOKEN)

    for idx, row in enumerate(routing_image):
        # Validate required keys
        if not all(k in row for k in ("name", "full_path", "file_name")):
            raise ValueError(f"Missing required keys in routing_image[{idx}]: {row}")

        file_path = os.path.join(row["full_path"], row["file_name"])

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(file_path, "rb") as f:
                client.files_upload_v2(
                    channel=CHANNEL_ID,
                    file=f,
                    title=os.path.basename(file_path),
                    initial_comment=f"🖼️ *Visualization –* {row['name']}"
                )
        except SlackApiError as e:
            raise Exception(f"Slack upload failed: {e.response['error']}")

    return {"status": "success"}

#for GCP

# from slack_sdk import WebClient
# from slack_sdk.errors import SlackApiError
# from google.cloud import storage
# from io import BytesIO
# import os
#
#
# def send_to_slack_visual(routing_image: list[dict]) -> dict:
#     """
#     Uploads visualization images to Slack from Google Cloud Storage.
#
#     Args:
#         routing_image: A list of dicts. Each must contain:
#             - name: Chart type (e.g., "Bar Chart")
#             - gcs_path: Full GCS path (e.g., 'gs://my-bucket/folder/image.jpg')
#
#     Returns:
#         dict: {"status": "success"} if upload completes
#     """
#     client = WebClient(token=SLACK_BOT_TOKEN)
#     gcs_client = storage.Client()
#
#     for idx, item in enumerate(routing_image):
#         if not all(k in item for k in ("name", "gcs_path")):
#             raise ValueError(f"Missing required keys in routing_image[{idx}]: {item}")
#
#         gcs_path = item["gcs_path"]
#         if not gcs_path.startswith("gs://"):
#             raise ValueError(f"Invalid GCS path: {gcs_path}")
#
#         try:
#             # Parse GCS path
#             _, _, bucket_name, *blob_parts = gcs_path.split("/")
#             blob_name = "/".join(blob_parts)
#
#             # Download image into memory
#             bucket = gcs_client.bucket(bucket_name)
#             blob = bucket.blob(blob_name)
#             image_stream = BytesIO()
#             blob.download_to_file(image_stream)
#             image_stream.seek(0)
#
#             # Upload to Slack
#             client.files_upload_v2(
#                 channel=CHANNEL_ID,
#                 file=image_stream,
#                 filename=os.path.basename(blob_name),
#                 title=os.path.basename(blob_name),
#                 initial_comment=f"🖼️ *Visualization –* {item['name']}"
#             )
#
#         except Exception as e:
#             raise RuntimeError(f"Slack upload failed for {gcs_path}: {e}")
#
#     return {"status": "success"}
#
