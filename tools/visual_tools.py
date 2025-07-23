from io import BytesIO

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from .file_name import create_file_path


def create_pairwise_overlap_metrix(data: list[dict]) -> dict:
    sources = set()
    for row in data:
        sources.add(row["source_1"])
        sources.add(row["source_2"])
    sources = sorted(sources)

    df = pd.DataFrame(0.0, index=sources, columns=sources)

    for row in data:
        a = row["source_1"]
        b = row["source_2"]
        value = row["overlap_percent"]
        df.at[a, b] = value

    df_display = df.copy()
    df_display = df_display.copy()
    for col in df_display.columns:
        df_display[col] = df_display[col].map(lambda x: "—" if x == 0 else f"{x:.2f}%")

    plt.figure(figsize=(8, 8))
    sns.set(font_scale=1.2)
    sns.set_style("white")
    cmap = sns.color_palette(["#e8f4fa"])

    ax = sns.heatmap(
        df,
        annot=df_display,
        fmt="",
        cmap=cmap,
        linewidths=0.5,
        linecolor='gray',
        cbar=False,
        square=True
    )

    plt.title("Pairwise Overlap Metrix", fontsize=16, weight='bold', pad=20)

    ax.tick_params(top=True, bottom=False, labeltop=True, labelbottom=False)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)

    file_path = create_file_path("visualization/images", "pairwise_overlap_metrix")
    plt.tight_layout(rect=(0, 0, 1, 0.92))
    plt.savefig(file_path["full_file_path"], dpi=300)
    plt.close()

    return {
        "status": "success",
        "full_image_path": file_path["full_file_path"]
    }


def plot_pairwise_overlap_heatmap(data_dict: list[dict]) -> dict:
    """
    Generates and saves a heatmap showing the percentage of user overlap between media sources.

    Parameters:
        data_dict (list[dict]): A list of dictionaries, where each dictionary represents
            an overlap relationship between two media sources. Each dictionary must include:
                - "source_1" (str): Name of the first media source.
                - "source_2" (str): Name of the second media source.
                - "overlap_percent" (float): Percentage of users that overlap between the two sources.

            Example:
            [
                {"source_1": "Facebook", "source_2": "Instagram", "overlap_percent": 22.0},
                {"source_1": "Instagram", "source_2": "Facebook", "overlap_percent": 30.0},
                ...
            ]

    Returns:
        dict: A dictionary with the status and full file path to the saved heatmap image.
            Example:
            {
                "status": "success",
                "full_image_path": "C:\\path\\to\\your\\heatmap_2025-07-20_14-03-00.png"
            }

    Notes:
        - Missing overlap values are filled with 0.
        - The heatmap is symmetric (i ≠ j), and diagonal values are also set to 0 by default.
    """

    df_pairs = pd.DataFrame(data_dict)

    pivot_table = df_pairs.pivot(index="source_1", columns="source_2", values="overlap_percent")

    all_sources = sorted(set(df_pairs["source_1"]) | set(df_pairs["source_2"]))
    pivot_table = pivot_table.reindex(index=all_sources, columns=all_sources)

    pivot_table = pivot_table.fillna(0)

    plt.figure(figsize=(8, 6))
    sns.heatmap(
        pivot_table,
        annot=True,
        fmt=".3f",
        cmap="Reds",
        linewidths=0.5,
        linecolor="gray",
        cbar_kws={'label': 'Overlap %'},
        vmin=0,
        vmax=pivot_table.to_numpy().max()
    )
    plt.title("Pairwise Media Source Overlap Heatmap")
    plt.xlabel("Target Media Source (j)")
    plt.ylabel("Source Media Source (i)")
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()

    file_path = create_file_path("visualization/images", "overlap_heatmap.png")
    plt.savefig(file_path["full_file_path"])
    plt.close()

    return {
        "status": "success",
        "full_image_path": file_path["full_file_path"]
    }


def plot_incrementality_bar_chart(data: list[dict]) -> dict:
    """
    Generates and saves a bar chart visualizing incrementality scores per media source.

    Parameters:
    -----------
    data : list of dict
        A list where each dictionary represents a media source with the following required keys:
            - "media_source" (str): The name of the media source.
            - "incrementality_score" (float): A value between 0 and 1 representing the incrementality score.

        Example:
        [
            {"media_source": "Facebook", "incrementality_score": 0.72},
            {"media_source": "TikTok", "incrementality_score": 0.95},
            ...
        ]

    Behavior:
    ---------
    - Converts the input data into a pandas DataFrame.
    - Creates a bar chart using seaborn, with media sources on the x-axis and their incrementality scores on the y-axis.
    - Saves the chart as an image file in the /2-agent/visualization/images directory, using a timestamped filename.
    - The output directory is created automatically if it does not exist.

    Returns:
    --------
    dict :
        A dictionary containing:
            - "status": "success"
            - "full_image_path": Full path to the saved PNG file.

        Example:
        {
            "status": "success",
            "full_image_path": "/2-agent/visualization/images/incrementality_bar_chart_2025-07-20_13-33-05.png"
        }
    """

    df = pd.DataFrame(data)

    plt.figure(figsize=(10, 6))
    sns.barplot(
        data=df,
        x="media_source",
        y="incrementality_score",
        hue="media_source",
        legend=False,
        palette="colorblind"
    )

    for i, row in df.iterrows():
        plt.text(i, row["incrementality_score"] + 0.01, f'{row["incrementality_score"]:.2%}',
                 ha='center', va='bottom')

    plt.ylim(0, 1.05)
    plt.title("Incrementality Score per Media Source")
    plt.xlabel("Media Source")
    plt.ylabel("Incrementality Score")
    plt.tight_layout()

    file_path = create_file_path("visualization/images","incrementality_bar_chart")
    plt.savefig(file_path["full_file_path"])
    plt.close()

    return {
        "status": "success",
        "full_image_path": file_path["full_file_path"]
    }

# העלאה לגוגל סטורייג
# import os
# load_dotenv()
#
# BUCKET_NAME = os.getenv("BUCKET_NAME")
#
# def upload_to_gcs(image_stream, folder="visualization/images", filename_prefix="chart"):
#     key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
#     if not key_path:
#         raise RuntimeError("Missing GOOGLE_APPLICATION_CREDENTIALS in .env!")
#
#     client = storage.Client()
#     bucket = client.bucket(BUCKET_NAME)
#     filename = f"{folder}/{filename_prefix}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.jpg"
#     blob = bucket.blob(filename)
#
#     try:
#         blob.upload_from_file(image_stream, content_type='image/jpeg')
#         print(f"[GCS] ✅ Uploaded successfully to: gs://{BUCKET_NAME}/{filename}")
#     except Exception as e:
#         print(f"[GCS] ❌ Upload failed: {e}")
#         raise
#
#     return f"gs://{BUCKET_NAME}/{filename}"
#
# def create_pairwise_overlap_metrix(data: list[dict]) -> dict:
#     sources = sorted(set(row["source_1"] for row in data) | set(row["source_2"] for row in data))
#     df = pd.DataFrame(0.0, index=sources, columns=sources)
#     for row in data:
#         df.at[row["source_1"], row["source_2"]] = row["overlap_percent"]
#
#     df_display = df.copy()
#     for col in df_display.columns:
#         df_display[col] = df_display[col].map(lambda x: "—" if x == 0 else f"{x:.2f}%")
#
#     plt.figure(figsize=(8, 8))
#     sns.set(font_scale=1.2)
#     sns.set_style("white")
#     sns.heatmap(df, annot=df_display, fmt="", cmap=["#e8f4fa"],
#                 linewidths=0.5, linecolor='gray', cbar=False, square=True)
#     plt.title("Pairwise Overlap Metrix", fontsize=16, weight='bold', pad=20)
#     plt.tight_layout(rect=(0, 0, 1, 0.92))
#
#     image_stream = BytesIO()
#     plt.savefig(image_stream, format='jpeg', dpi=300)
#     plt.close()
#     image_stream.seek(0)
#
#     gcs_path = upload_to_gcs(image_stream, filename_prefix="pairwise_overlap_metrix")
#     return {"status": "success", "full_image_path": gcs_path}
#
#
# def plot_pairwise_overlap_heatmap(data_dict: list[dict]) -> dict:
#     df_pairs = pd.DataFrame(data_dict)
#     all_sources = sorted(set(df_pairs["source_1"]) | set(df_pairs["source_2"]))
#     pivot = df_pairs.pivot(index="source_1", columns="source_2", values="overlap_percent")
#     pivot = pivot.reindex(index=all_sources, columns=all_sources).fillna(0)
#
#     plt.figure(figsize=(8, 6))
#     sns.heatmap(pivot, annot=True, fmt=".3f", cmap="Reds",
#                 linewidths=0.5, linecolor="gray", cbar_kws={'label': 'Overlap %'},
#                 vmin=0, vmax=pivot.to_numpy().max())
#     plt.title("Pairwise Media Source Overlap Heatmap")
#     plt.xlabel("Target Media Source (j)")
#     plt.ylabel("Source Media Source (i)")
#     plt.xticks(rotation=45, ha="right")
#     plt.yticks(rotation=0)
#     plt.tight_layout()
#
#     image_stream = BytesIO()
#     plt.savefig(image_stream, format='jpeg')
#     plt.close()
#     image_stream.seek(0)
#
#     gcs_path = upload_to_gcs(image_stream, filename_prefix="overlap_heatmap")
#     return {"status": "success", "full_image_path": gcs_path}
#
#
# def plot_incrementality_bar_chart(data: list[dict]) -> dict:
#     df = pd.DataFrame(data)
#
#     plt.figure(figsize=(10, 6))
#     sns.barplot(data=df, x="media_source", y="incrementality_score",
#                 hue="media_source", legend=False, palette="colorblind")
#
#     for i, row in df.iterrows():
#         plt.text(i, row["incrementality_score"] + 0.01, f'{row["incrementality_score"]:.2%}',
#                  ha='center', va='bottom')
#
#     plt.ylim(0, 1.05)
#     plt.title("Incrementality Score per Media Source")
#     plt.xlabel("Media Source")
#     plt.ylabel("Incrementality Score")
#     plt.tight_layout()
#
#     image_stream = BytesIO()
#     plt.savefig(image_stream, format='jpeg')
#     plt.close()
#     image_stream.seek(0)
#
#     gcs_path = upload_to_gcs(image_stream, filename_prefix="incrementality_bar_chart")
#     return {"status": "success", "full_image_path": gcs_path}
