# heatmap.py

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from .file_name import create_file_path

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

    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print(df_pairs)
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

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

    file_path = create_file_path(fr"C:\Users\This User\Music\AppsFlyer\Partner Reach Overlap Agent\Agent Development Kit\2-agent\visualization\images", "overlap_heatmap")
    plt.savefig(file_path["full_file_path"])
    plt.close()

    return {
        "status": "success",
        "full_image_path": file_path["full_file_path"]
    }
