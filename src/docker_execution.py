import datetime
import os
import shutil
import subprocess


def setup_docker(alg_store):
    """
    A zip file is expected to contain a setup.sh which prepares the VM for code execution. One can assume that
    :return:
    """

    prepare_setup_for_execution_in_docker(alg_store.setup_file_path())

    docker_name = datetime.datetime.now().microsecond

    execute_algorithm(alg_store.algorithm_dir(), docker_name, alg_store.groundtruth_dir(), alg_store.input_dir())

    extract_predictions(docker_name, alg_store.prediction_dir())
    p = subprocess.run(["docker", "rm", str(docker_name)], check=True)
    print(p.returncode)
    return "Fine."


def extract_predictions(docker_name, result_folder_path):
    p = subprocess.run(["docker", "cp", str(docker_name) + ":/data", result_folder_path], check=True)
    print(p.returncode, p)
    for filename in os.listdir(os.path.join(result_folder_path, "data")):
        if '.' in filename and filename.rsplit('.')[1] == "atr":
            shutil.copy2(os.path.join(result_folder_path, "data", filename), os.path.join(result_folder_path))


def prepare_setup_for_execution_in_docker(setup_file_path):
    with open(setup_file_path, 'r+') as setup_file:
        contents = setup_file.readlines()
    contents = ["apt update && apt upgrade -y\n cd /alg\n"] + contents
    with open(setup_file_path, 'w') as setup_file:
        setup_file.writelines(contents)
    with open(setup_file_path, "r") as sf:
        print(sf.readlines())


def execute_algorithm(alg_dir, docker_name, gt_data_path, input_data_path):
    setup_evaluation_data(input_data_path, gt_data_path)
    p = subprocess.run(["systemctl", "--user", "start", "docker"], check=True)
    start_docker = ["docker", "run", "--name={}".format(docker_name), "--network", "host",
                    "-v", "{}:/alg".format(alg_dir),
                    "-v", "{}:/data".format(input_data_path),
                    "ubuntu", "bash", "/alg/setup.sh", ]
    print("preparation complete. starting docker with: ", " ".join(start_docker))
    p = subprocess.run(start_docker, check=True)
    print(p.returncode)


def setup_evaluation_data(data_folder_path, ann_data_path):
    src = "/mnt/dsets/physionet/mitdb/1.0.0"
    for data_file in os.listdir(src):
        if os.path.isdir(os.path.join(src, data_file)):
            continue
        if '.' in data_file and data_file.rsplit(".")[1] == 'atr':
            ann_file_path = os.path.join(ann_data_path, data_file)
            if not os.path.exists(ann_file_path):
                shutil.copy2(os.path.join(src, data_file), ann_data_path)
        else:
            data_file_path = os.path.join(data_folder_path, data_file)
            if not os.path.exists(data_file_path):
                shutil.copy2(os.path.join(src, data_file), data_folder_path)
