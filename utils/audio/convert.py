import os
import sox
import shutil
import logging

import pandas as pd

from tqdm import tqdm

from utils.misc import recursive_search


def transform_wav(input_path, output_path=None):
    conf = {
        "rate": 8000,
        "bits": 16,
        "channels": 1
    }
    if output_path is None:
        output_path = input_path

    tfm = sox.Transformer()
    tfm.set_globals(dither=True, verbosity=0)
    tfm.set_output_format(rate=conf.get("rate"), bits=conf.get("bits"), channels=conf.get("channels"))

    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))
    try:
        tfm.build(input_path, output_path)
        return "Done!"
    except Exception as e:
        logging.error(f"Error occured for input_path={input_path}", exc_info=True)
        return "Failed!"


# def convert_to_wav(input_dir, output_dir, ext="*.wav", if_exists='replace', use_tqdm=True):
#
#     # def convert_func(file_, ext):
#     #     file_name, file_path = file_
#     #     new_file_name = file_name.rsplit(".", 1)[0] + ".wav"
#     #     new_file_path = os.path.join(output_dir, new_file_name)
#     #
#     #     res = transform_wav(file_path, new_file_path)
#     #     if res == 'Done!':
#     #         return (file_name, file_path, new_file_name, new_file_path)
#     #     else:
#     #         return (file_name, file_path, "", "")
#
#     if not os.path.exists(output_dir):
#         os.makedirs(output_dir)
#     elif len(os.listdir(output_dir)) > 0 and if_exists == 'replace':
#         shutil.rmtree(output_dir)
#         os.makedirs(output_dir)
#
#     input_files = recursive_search(input_dir, [ext]).values
#     iterator = tqdm(input_files) if use_tqdm else input_files
#     resutls = []
#     for file_ in iterator:
#         file_name, file_path = file_
#         new_file_name = file_name.rsplit(".", 1)[0] + ".wav"
#         new_file_path = os.path.join(output_dir, new_file_name)
#
#         res = transform_wav(file_path, new_file_path)
#         if res == 'Done!':
#             resutls.append((file_name, file_path, new_file_name, new_file_path))
#         else:
#             resutls.append((file_name, file_path, "", ""))
#
#     #     resutls = process_map(convert_func, input_files, max_workers=cpu_count())
#
#     return pd.DataFrame(resutls, columns=["file_name", "file_path", "new_file_name", "new_file_path"])