# barChart.py

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from .file_name import create_file_path

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

    file_path = create_file_path(fr"C:\Users\This User\Music\AppsFlyer\Partner Reach Overlap Agent\Agent Development Kit\2-agent\visualization\images", "incrementality_bar_chart")
    plt.savefig(file_path["full_file_path"])
    plt.close()

    return {
        "status": "success",
        "full_image_path": file_path["full_file_path"]
    }


