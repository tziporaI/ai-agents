# heatmap.py

import base64
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO

def plot_pairwise_overlap_heatmap(data_dict: list[dict]) -> dict:
    """
    Generates a heatmap showing user overlap between media sources and returns it as a base64-encoded PNG image.

    Parameters:
    -----------
    data_dict : list of dict
        Each item must contain:
            - "source_1" (str)
            - "source_2" (str)
            - "overlap_percent" (float)

    Returns:
    --------
    dict :
        {
            "status": "success",
            "image_base64": <str>,         # base64-encoded PNG image
            "file_name": "Heat Map - overlap matrix"
        }
    """

    df_pairs = pd.DataFrame(data_dict)
    pivot_table = df_pairs.pivot(index="source_1", columns="source_2", values="overlap_percent")

    all_sources = sorted(set(df_pairs["source_1"]) | set(df_pairs["source_2"]))
    pivot_table = pivot_table.reindex(index=all_sources, columns=all_sources).fillna(0)

    plt.figure(figsize=(8, 6))
    sns.heatmap(
        pivot_table,
        annot=True,
        fmt=".2f",
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

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("utf-8")

    return {
        "status": "success",
        "image_base64": encoded,
        "file_name": "Heat Map - overlap matrix"
    }
