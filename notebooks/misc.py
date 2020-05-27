import youtube_dl
import requests
from bs4 import BeautifulSoup
from config import ydl_opts

# ydl_opts = {
#     'format': 'bestaudio/best',
#     'postprocessors': [{
#         'key': 'FFmpegExtractAudio',
#         'preferredcodec': 'mp3',
#         'preferredquality': '192',
#     }],
#     'outtmpl': '%(title)s.%(etx)s',
#     'quiet': False
# }



# with youtube_dl.YoutubeDL(ydl_opts) as ydl:
#     ydl.download([url])  # Download into the current working directory




url1 = "https://www.youtube.com/watch?v=BaW_jenozKc"
url2 = 'https://www.youtube.com/watch?v=cP34VrrKp-s'


def get_yt_subtitles(url, lang='uk'):
    opts = ydl_opts
    opts['listsubtitles'] = True
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False, process=False)
    subtitles = info.get("subtitles", {lang: []}).get(lang)
    return subtitles


def get_yt_audio(url):
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def parse_subtitles(url, sub_type='srv1'):
    if sub_type == 'srv1':
        soup = BeautifulSoup(requests.get(url).content, 'lxml')
        res = [(item.attrs['start'], item.attrs['dur'], item.text) for item in soup.find_all('text')]
        return res
    else:
        raise ValueError


# with youtube_dl.YoutubeDL(ydl_opts) as ydl:
#     info = ydl.extract_info(url2, download=False, process=False)
#     # print(info)
#     print(info['subtitles'])
#     # print(json.dumps(info, indent=4).encode().decode())

# ydl = youtube_dl.YoutubeDL(ydl_opts)
# ydl.extract_info(url2, download=False)
#
# print(ydl.ie_result)


if __name__ == "__main__":

    # srv1_url = ([""] + [item['url'] for item in get_yt_subtitles(url2) if item.get('ext') == 'srv1'])[-1]
    # res1 = parse_subtitles(srv1_url)
    # print(res1)
    get_yt_audio(url2)
