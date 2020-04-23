import os
from flask import Flask, render_template, flash, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

from docker_evaluation import setup_docker

UPLOAD_FOLDER = "algorithms"
if not os.path.exists(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'zip'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def root(name=None):
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            subdir = filename.rsplit('.')[0]
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], subdir)
            if not os.path.exists(file_path):
                os.mkdir(file_path)
            file.save(os.path.join(file_path, filename))
            setup_msg = setup_docker(file_path, filename)
            print(setup_msg)
            return redirect(url_for('uploaded_file', filename=filename))

    return render_template('root.html', name=name)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return "upload successful of " + filename
