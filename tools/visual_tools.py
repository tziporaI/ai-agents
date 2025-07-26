import uuid
from io import BytesIO
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
from datetime import datetime
from google.cloud import storage
from dotenv import load_dotenv

load_dotenv()

BUCKET_NAME = os.getenv("BUCKET_NAME")


def upload_to_gcs(image_stream, folder="visualization/images", filename_prefix="chart"):
    """
    Uploads an image stream to a Google Cloud Storage bucket with a timestamped filename.

    Args:
        image_stream: A file-like binary stream (e.g., BytesIO) containing the image to upload.
        folder (str): The destination folder path inside the GCS bucket. Defaults to "visualization/images".
        filename_prefix (str): The prefix to use for the uploaded file's name. Defaults to "chart".

    Returns:
        dict: Contains either:
            - "status": "success", with:
                • str: GCS URI of the uploaded image (e.g., gs://<bucket>/<path>)
            - "status": "error", with "error_message"

    Raises:
        RuntimeError: If the required Google credentials are missing from the environment.
        Exception: If the image upload fails for any reason.
    """

    key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not key_path:
        raise RuntimeError("Missing GOOGLE_APPLICATION_CREDENTIALS in .env!")

    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    filename = f"{folder}/{filename_prefix}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.jpg"
    blob = bucket.blob(filename)

    try:
        blob.upload_from_file(image_stream, content_type='image/jpeg')
        print(f"[GCS] ✅ Uploaded successfully to: gs://{BUCKET_NAME}/{filename}")
    except Exception as e:
        print(f"[GCS] ❌ Upload failed: {e}")
        raise
    return f"gs://{BUCKET_NAME}/{filename}"


def create_pairwise_overlap_metrix(data: list[dict]) -> dict:
    """
    Generates a pairwise overlap matrix heatmap from input data and uploads the image to GCS.

    Args:
        data (list[dict]): A list of dictionaries, each containing:
            - "source_1" (str): Name of the first media source.
            - "source_2" (str): Name of the second media source.
            - "overlap_percent" (float): Percentage of shared users between source_1 and source_2.

    Returns:
        dict: Contains either:
            - "status": "success", with:
                • "full_image_path": GCS URI of the generated matrix image
            - "status": "error", with "error_message"

    Raises:
        None
    """
    sources = sorted(set(row["source_1"] for row in data) | set(row["source_2"] for row in data))
    df = pd.DataFrame(0.0, index=sources, columns=sources)
    for row in data:
        df.at[row["source_1"], row["source_2"]] = row["overlap_percent"]

    df_display = df.copy()
    for col in df_display.columns:
        df_display[col] = df_display[col].map(lambda x: "—" if x == 0 else f"{x:.2f}%")

    plt.figure(figsize=(8, 8))
    sns.set(font_scale=1.2)
    sns.set_style("white")
    sns.heatmap(df, annot=df_display, fmt="", cmap=["#e8f4fa"],
                linewidths=0.5, linecolor='gray', cbar=False, square=True)
    plt.title("Pairwise Overlap Metrix", fontsize=16, weight='bold', pad=20)
    plt.tight_layout(rect=(0, 0, 1, 0.92))

    image_stream = BytesIO()
    plt.savefig(image_stream, format='jpeg', dpi=300)
    plt.close()
    image_stream.seek(0)

    gcs_path = upload_to_gcs(image_stream, filename_prefix="pairwise_overlap_metrix")
    return {"status": "success", "full_image_path": gcs_path}


def plot_pairwise_overlap_heatmap(data_dict: list[dict]) -> dict:
    """
    Creates a heatmap showing pairwise user overlap between media sources and uploads it to GCS.

    Args:
        data_dict (list[dict]): A list of dictionaries, each containing:
            - "source_1" (str): Name of the source media.
            - "source_2" (str): Name of the target media.
            - "overlap_percent" (float): Percentage of users shared between the two sources.

    Returns:
        dict: Contains either:
            - "status": "success", with:
                • "full_image_path": GCS URI of the generated heatmap image
            - "status": "error", with "error_message"

    Raises:
        None
    """

    df_pairs = pd.DataFrame(data_dict)
    all_sources = sorted(set(df_pairs["source_1"]) | set(df_pairs["source_2"]))
    pivot = df_pairs.pivot(index="source_1", columns="source_2", values="overlap_percent")
    pivot = pivot.reindex(index=all_sources, columns=all_sources).fillna(0)

    plt.figure(figsize=(8, 6))
    sns.heatmap(pivot, annot=True, fmt=".3f", cmap="Reds",
                linewidths=0.5, linecolor="gray", cbar_kws={'label': 'Overlap %'},
                vmin=0, vmax=pivot.to_numpy().max())
    plt.title("Pairwise Media Source Overlap Heatmap")
    plt.xlabel("Target Media Source (j)")
    plt.ylabel("Source Media Source (i)")
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()

    image_stream = BytesIO()
    plt.savefig(image_stream, format='jpeg')
    plt.close()
    image_stream.seek(0)

    gcs_path = upload_to_gcs(image_stream, filename_prefix="overlap_heatmap")
    return {"status": "success", "full_image_path": gcs_path}


def plot_incrementality_bar_chart(data: list[dict]) -> dict:
    """
    Generates a bar chart showing the incrementality score per media source and uploads it to GCS.

    Args:
        data (list[dict]): A list of dictionaries, each containing:
            - "media_source" (str): The name of the media source.
            - "incrementality_score" (float): The incrementality score (between 0 and 1) for the media source.

    Returns:
        dict: Contains either:
            - "status": "success", with:
                • "gcs_path": GCS URI of the generated bar chart image
            - "status": "error", with "error_message"

    Raises:
        None
    """

    df = pd.DataFrame(data)

    plt.figure(figsize=(10, 6))
    sns.barplot(data=df, x="media_source", y="incrementality_score",
                hue="media_source", legend=False, palette="colorblind")

    for i, row in df.iterrows():
        plt.text(i, row["incrementality_score"] + 0.01, f'{row["incrementality_score"]:.2%}',
                 ha='center', va='bottom')

    plt.ylim(0, 1.05)
    plt.title("Incrementality Score per Media Source")
    plt.xlabel("Media Source")
    plt.ylabel("Incrementality Score")
    plt.tight_layout()

    image_stream = BytesIO()
    plt.savefig(image_stream, format='jpeg')
    plt.close()
    image_stream.seek(0)

    gcs_path = upload_to_gcs(image_stream, filename_prefix="incrementality_bar_chart")
    return {"status": "success", "full_image_path": gcs_path}
