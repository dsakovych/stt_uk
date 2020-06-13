import os
import shutil
from flask import Flask, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from config import FlaskConfig, TMP_DIR
from utils.decode_kaldi import kaldi_stt

app = Flask(__name__)
app.config.from_object(FlaskConfig)


# @app.route("/")
# def home():
#     return 'Hello world!'


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            tmp_path = os.path.join(TMP_DIR, filename)

            shutil.copy2(file_path, tmp_path)
            decoded_text = kaldi_stt(tmp_path)[0]

            return f"""<a href="{"http://127.0.0.1:5000" + url_for('uploaded_file', filename=filename)}">uploaded file</a><br>{decoded_text}"""
    # return '''
    # <!doctype html>
    # <title>Upload new File</title>
    # <h1>Upload new File</h1>
    # <form action="" method=post enctype=multipart/form-data>
    #   <p><input type=file name=file>
    #      <input type=submit value=Upload>
    # </form>
    # '''
    return """
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form enctype="multipart/form-data" action="" method="post" >
        <ul>
            <li>
                <label for="name">Name</label>
                <input type="text" name="name" placeholder="" required="required" id="name"/>
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
                <input type="submit" value="Upload"/>
            </li>
        </ul>
    </form>
    
    
    """


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


app.run(threaded=True)
