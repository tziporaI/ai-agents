import json
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from google.cloud import storage
from io import BytesIO
import os
load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
CHANNEL_NAME = os.getenv("CHANNEL_NAME")
CHANNEL_ID = os.getenv("CHANNEL_ID")


def send_to_slack_str(result_data: str) -> str:
    """
    Sends a formatted result string to a predefined Slack channel.

    Args:
        result_data (str): The message content to send. Can be a JSON-formatted string or plain text.

    Returns:
        str: Success message if sent successfully.

    Raises:
        Exception: If the Slack API request fails or responds with an error.
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
    Uploads one or more visualization images from GCS to a Slack channel.

    Args:
        routing_image (list[dict]): A list of dictionaries, each containing:
            - "name" (str): A display name or title for the image.
            - "gcs_path" (str): Full GCS URI of the image file (must start with "gs:.//visualisation//images//...").

    Returns:
        dict: Contains either:
            - "status": "success", indicating all images were uploaded successfully
            - "status": "error", with "error_message" (only if handled manually)

    Raises:
        ValueError: If required keys are missing or GCS path format is invalid.
        RuntimeError: If an image upload to Slack fails.
    """

    client = WebClient(token=SLACK_BOT_TOKEN, timeout=15)
    gcs_client = storage.Client()

    for idx, item in enumerate(routing_image):
        if not all(k in item for k in ("name", "gcs_path")):
            raise ValueError(f"Missing required keys in routing_image[{idx}]: {item}")

        gcs_path = item["gcs_path"]
        if not gcs_path.startswith("gs://"):
            raise ValueError(f"Invalid GCS path: {gcs_path}")

        try:
            # Parse GCS path
            _, _, bucket_name, *blob_parts = gcs_path.split("/")
            blob_name = "/".join(blob_parts)

            # Download image into memory
            bucket = gcs_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            image_stream = BytesIO()
            blob.download_to_file(image_stream)
            image_stream.seek(0)

            # Upload to Slack
            client.files_upload_v2(
                channel=CHANNEL_ID,
                file=image_stream,
                filename=os.path.basename(blob_name),
                title=os.path.basename(blob_name),
                initial_comment=f"🖼️ *Visualization –* {item['name']}"
            )

        except Exception as e:
            raise RuntimeError(f"Slack upload failed for {gcs_path}: {e}")

    return {"status": "success"}

