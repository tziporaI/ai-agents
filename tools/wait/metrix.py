# metrix.py

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import base64
from io import BytesIO

def create_pairwise_overlap_metrix(data: list[dict]) -> dict:
    """
    Generates a matrix-style heatmap for pairwise media overlap and returns it as a base64-encoded PNG image.

    Parameters:
    -----------
    data : list of dict
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
            "file_name": "Matrix - overlap table"
        }
    """
    sources = sorted({row["source_1"] for row in data} | {row["source_2"] for row in data})
    df = pd.DataFrame(0.0, index=sources, columns=sources)

    for row in data:
        df.at[row["source_1"], row["source_2"]] = row["overlap_percent"]

    df_display = df.copy().applymap(lambda x: "—" if x == 0 else f"{x:.2f}%")

    plt.figure(figsize=(8, 8))
    sns.set(font_scale=1.2)
    sns.set_style("white")

    ax = sns.heatmap(
        df,
        annot=df_display,
        fmt="",
        cmap=sns.color_palette(["#e8f4fa"]),
        linewidths=0.5,
        linecolor='gray',
        cbar=False,
        square=True
    )

    plt.title("Pairwise Overlap Metrix", fontsize=16, weight='bold', pad=20)

    ax.tick_params(top=True, bottom=False, labeltop=True, labelbottom=False)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
    plt.tight_layout(rect=(0, 0, 1, 0.92))

    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=300)
    plt.close()
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("utf-8")

    return {
        "status": "success",
        "image_base64": encoded,
        "file_name": "Matrix - overlap table"
    }