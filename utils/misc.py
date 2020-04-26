import os
import shutil
import logging
import traceback
import soundfile
import pandas as pd

from pathlib import Path


def recursive_search(search_path, file_ext=("*.mp3", "*.wav")):
    res = []
    for ext in file_ext:
        for file_path in Path(search_path).rglob(ext):
            file_path = str(file_path)
            res.append((os.path.basename(file_path), file_path))
    return pd.DataFrame(res, columns=["file_name", "file_path"])


def create_dir(path, stderr=False):
    if not os.path.exists(path):
        os.makedirs(path)
    elif stderr:
        logging.warning(f"Can't create dir. Path exists: {path}")
    else:
        pass


def delete_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    else:
        logging.warning(f"Can't delete dir. Path not exists: {path}")


def get_file_duration(file_path):
    try:
        f = soundfile.SoundFile(file_path)
        res = {
            "samples": len(f),
            "sample_rate": f.samplerate,
        }
        return res["samples"]/res['sample_rate']
    except Exception as e:
        tb = str(traceback.format_exc())
        logging.error(f"Error occurred with file={file_path}. Traceback:\n{tb}")
        return 0
