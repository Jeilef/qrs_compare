import datetime
import os
import re
import shutil
import subprocess

from data_handling.data_docker_setup import ECGData


def setup_docker(alg_store):
    """
    A zip file is expected to contain a setup.sh which prepares the VM for code execution. One can assume that
    :return:
    """

    prepare_setup_for_execution_in_docker(alg_store.setup_file_path())

    docker_name = datetime.datetime.now().microsecond

    docker_names = execute_algorithm(alg_store.algorithm_dir(), docker_name, alg_store.groundtruth_dir(),
                                     alg_store.input_dir(), alg_store.prediction_dir())
    # for docker_name in docker_names:
    #    p = finalize_docker(alg_store, docker_name)
    #    print(p.returncode)
    return "Fine."


def finalize_docker(alg_store, docker_name):
    extract_predictions(docker_name, alg_store.prediction_dir())
    p = subprocess.run(["docker", "rm", str(docker_name)], check=True)
    return p


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


def execute_algorithm(alg_dir, docker_name, gt_data_path, input_data_path, prediction_path):
    test_data_manager = ECGData(input_data_path, gt_data_path)
    input_data_path = test_data_manager.setup_evaluation_data()
    rt = subprocess.run(["systemctl", "--user", "start", "docker"], check=True).returncode
    print("Docker deamon start exited with: ", rt)
    docker_names = []
    docker_container = []
    pattern = re.compile('.*[a-zA-Z]_[0-9].[0-9]_[0-9]+.*')
    for input_data_folder in os.listdir(input_data_path):
        if pattern.match(input_data_folder):
            continue
        extended_name = str(docker_name) + input_data_folder
        docker_names.append(extended_name)
        # has to not exceed the memory - especially important for the eval data
        start_docker = ["docker", "run", "--name={}".format(extended_name), "--network", "host", "--rm",
                        "-v", "{}:/alg".format(alg_dir),
                        "-v", "{}:/data".format(os.path.join(input_data_path, input_data_folder)),
                        "-v", "{}:/pred".format(os.path.join(prediction_path)),
                        "ubuntu", "bash", "/alg/setup.sh", ]
        print("preparation complete. starting docker with: ", " ".join(start_docker))
        proc = subprocess.Popen(start_docker)
        docker_container.append(proc)

    for proc in docker_container:
        proc.wait()

    return docker_names

