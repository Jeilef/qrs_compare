import json
import os
from flask import Flask, render_template, flash, request, redirect, url_for, Blueprint, jsonify
from werkzeug.utils import secure_filename
from multiprocessing import Pool

from algorithm_evaluation import evaluate_algorithm, read_evaluated_algorithms, read_single_algorithm_results
from algorithm_store import AlgorithmStore
from docker_execution import setup_docker
from util.util import BEAT_CODE_DESCRIPTIONS

UPLOAD_FOLDER = "algorithms"
if not os.path.exists(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'zip'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = b'sj8345(Z)5%(HQ(O'


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def root(metrics=None):
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            alg_store = AlgorithmStore.for_new_alg(file, app.config['UPLOAD_FOLDER'])

            setup_msg = setup_docker(alg_store)
            evaluate_algorithm(alg_store)
            print(setup_msg)
            # return redirect(url_for('uploaded_file', filename="filename"))
    ms = read_evaluated_algorithms()
    print(ms)
    return render_template('root.html', metrics=json.dumps(ms).replace("'", '"'))


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return "upload successful of " + filename


@app.route('/reeval')
def reeval(metrics=None):
    alg_stores = AlgorithmStore.for_all_existing(app.config['UPLOAD_FOLDER'])
    for alg_store in alg_stores:
        evaluate_algorithm(alg_store)

    ms = read_evaluated_algorithms()
    print(ms)
    return render_template('root.html', metrics=json.dumps(ms).replace("'", '"'))


@app.route('/details/<algname>')
def details(algname, metrics=None, code_mapping=None):
    metric_values = read_single_algorithm_results(algname)
    return render_template('details.html', metrics=json.dumps(metric_values).replace("'", '"'),
                           code_mapping=json.dumps(BEAT_CODE_DESCRIPTIONS).replace("'", '"'))
