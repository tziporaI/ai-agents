# barChart.py

import base64
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from .file_name import create_file_path

def plot_incrementality_bar_chart(data: list[dict]) -> dict:
    """
    Generates a bar chart visualizing incrementality scores per media source and returns it as an in-memory PNG image.

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
    - Saves the chart to an in-memory PNG image using BytesIO.

    Returns:
    --------
    dict :
        A dictionary containing:
            - "status": "success"
            - "image_buffer": BytesIO object containing the PNG image
            - "file_name": Suggested filename for the image

        Example:
        {
            "status": "success",
            "image_buffer": <BytesIO object>,
            "file_name": "Bar Chart - incrementality score"
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

    plt.ylim(0, 1)
    plt.title("Incrementality Score per Media Source")
    plt.xlabel("Media Source")
    plt.ylabel("Incrementality Score")
    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("utf-8")

    return {
        "status": "success",
        "image_base64": encoded,
        "file_name": "Bar Chart - incrementality score"
    }


