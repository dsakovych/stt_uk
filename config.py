import os

ENV = os.environ.get('ENV', 'local')
APP_NAME = os.environ.get("APP_NAME", "stt_uk")
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(APP_DIR, "data")
TMP_DIR = os.path.join(APP_DIR, "tmp")
KALDI_PATH = os.environ.get("KALDI_ROOT", "/home/dima/kaldi")
s5_path = os.path.join(KALDI_PATH, "egs", "stt_uk", "s5")

data = {
    "voxforge": os.path.join(DATA_DIR, "voxforge"),
    "youtube": os.path.join(DATA_DIR, "youtube")
}


ydl_opts = {
    'format': 'bestaudio',
    'listsubtitles': False,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '128'
    }],
    'postprocessor_args': [
        '-ar', '16000'
    ],
    'prefer_ffmpeg': True,
    'keepvideo': False,
    'outtmpl': data.get('youtube') + '/%(title)s.%(ext)s'
}

class FlaskConfig(object):
    ENV = ENV

    APP_NAME = APP_NAME
    APP_VERSION = "1.0"
    APP_HOST = os.environ.get('APP_HOST', '127.0.0.1')
    APP_PORT = os.environ.get('APP_PORT', 5000)

    SECRET_KEY = os.environ.get('SECRET_KEY', 'SECRET')
    DEBUG = False
    UPLOAD_FOLDER = os.path.join(DATA_DIR, 'upload')
