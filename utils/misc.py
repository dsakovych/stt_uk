import os
import pandas as pd

from pathlib import Path


def recursive_search(search_path, file_ext=("*.mp3", "*.wav")):
    res = []
    for ext in file_ext:
        for file_path in Path(search_path).rglob(ext):
            file_path = str(file_path)
            res.append((os.path.basename(file_path), file_path))
    return pd.DataFrame(res, columns=["file_name", "file_path"])
