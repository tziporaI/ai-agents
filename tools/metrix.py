# metrix.py

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

    file_path = create_file_path(fr"C:\Users\This User\Music\AppsFlyer\Partner Reach Overlap Agent\Agent Development Kit\2-agent\visualization\images", "pairwise_overlap_metrix")
    plt.tight_layout(rect=(0, 0, 1, 0.92))
    plt.savefig(file_path["full_file_path"], dpi=300)
    plt.close()

    return {
        "status": "success",
        "full_image_path": file_path["full_file_path"]
    }
