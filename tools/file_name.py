from pathlib import Path
from datetime import datetime


def create_file_path(relative_folder: str, file_name: str) -> dict[str]:
    """
    Builds a timestamped file path within the project directory.

    Parameters:
        relative_folder: subdirectory path inside the project (e.g., 'visualization/images')
        file_name: base name for the file (without extension)

    Returns:
        dict with 'full_file_path': full absolute path to the PNG file
    """
    project_root = Path(__file__).resolve().parent

    target_folder = project_root / relative_folder
    target_folder.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    full_file_path = target_folder / f"{file_name}_{timestamp}.png"

    return {"full_file_path": str(full_file_path)}
