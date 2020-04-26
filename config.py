import os

ENV = os.environ.get('ENV', 'local')
APP_NAME = os.environ.get("APP_NAME", "stt_uk")
APP_DIR = os.path.dirname(os.path.abspath(__file__))
TMP_DIR = os.path.join(APP_DIR, "tmp")
KALDI_PATH = os.environ.get("KALDI_ROOT", "/home/dima/kaldi")

s5_path = os.path.join(KALDI_PATH, "egs", "babel", "s5d")