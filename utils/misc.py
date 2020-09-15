import os
import shutil
import logging
import requests
import tarfile
import traceback
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


def delete(path):
    if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)  # remove the file
    elif os.path.isdir(path):
        shutil.rmtree(path)  # remove dir and all contains
    else:
        logging.warning(f"Can't delete dir. Path not exists: {path}")


def download_file(url, save_path):
    try:
        res = requests.get(url)
        create_dir(os.path.dirname(save_path))
        if res.status_code == 200:
            if os.path.exists(save_path):
                shutil.rmtree(save_path)
            with open(save_path, 'wb') as f:
                f.write(res.content)
            return "Success!", res.status_code
        else:
            return "Failed!", res.status_code
    except Exception as e:
        tb = str(traceback.format_exc())
        logging.error(f"Error occurred with url={url}. Traceback:\n{tb}")
        return "Failed!", None


def untar_file(fname, path):
    if fname.endswith("tgz"):
        tar = tarfile.open(fname, "r:gz")
        tar.extractall(path)
        tar.close()
    elif fname.endswith("tar"):
        tar = tarfile.open(fname, "r:")
        tar.extractall(path)
        tar.close()
