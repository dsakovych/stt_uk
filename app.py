import os
import re
import shutil
from flask import Flask, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from config import FlaskConfig, TMP_DIR
from utils.decode_kaldi import kaldi_stt

app = Flask(__name__)
app.config.from_object(FlaskConfig)


def regex_tokenize(x):
    x = " ".join(re.findall(r'\w+', x)).lower()
    return x


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        text = request.form['text']
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            tmp_path = os.path.join(TMP_DIR, filename)

            shutil.copy2(file_path, tmp_path)
            wer = ''
            wer_details = ''
            if text:
                text = regex_tokenize(text)
                decoded_text, wer, wer_details = kaldi_stt(tmp_path, text)
                # decoded_text = decoded_text[0]
            else:
                decoded_text = kaldi_stt(tmp_path)

            return """
            <!doctype html>
            <title>Decoding results</title>
            <style>
               p {
                text-align: justify;
               }
              </style>
            <a href="{file_link}">uploaded file</a>
            <br>
            <h3>Decoded text: </h3><p>{decoded_text}</p>
            <br>
            <h3>Word Error Rate result: </h3><p>{wer}</p>
            <br>
            <h3>WER details: </h3><p>{wer_details}</p>
            <br>
            <a href="http://127.0.0.1:5000">Home</a>
            """.replace('{file_link}', f"""{"http://127.0.0.1:5000" + url_for('uploaded_file', filename=filename)}""").replace('{decoded_text}', decoded_text).replace('{wer}', wer).replace('{wer_details}', wer_details)

    return """
    <!doctype html>
    <title>speech-to-text for ukrainian -- prj-nlp-2020 demo</title>
    <h1>speech-to-text for ukrainian -- prj-nlp-2020 demo</h1>
    <form enctype="multipart/form-data" action="" method="post" >
        <ul>
            <li>
                <label for="text">text</label>
                <input type="text" name="text" placeholder="" id="text"/>
            </li>
        </ul>
        <ul>
            <li>
                <label for="file">File</label>
                <input type="file" name="file" id="file" />
            </li>
        </ul>
        <ul>
            <li>
                <input type="submit" value="RUN!"/>
            </li>
        </ul>
    </form>   
    """


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


app.run(threaded=True)
