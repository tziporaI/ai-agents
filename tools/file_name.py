from datetime import datetime

def create_file_path(file_path: str, file_name: str) -> dict[str]:

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    full_file_path = fr"{file_path}/{file_name}_{timestamp}.png"

    return { "full_file_path": full_file_path }
