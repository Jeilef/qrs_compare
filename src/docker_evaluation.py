import errno
import os
import datetime
import subprocess
import zipfile
import shutil


def setup_docker(folder_path, zip_file_name):
    """
    A zip file is expected to contain a setup.sh which prepares the VM for code execution. One can assume that
    apt update && apt upgrade has already been done.
    :param folder_path: folder path of the uploaded zip file
    :param zip_file_name: name of the zip file
    :return:
    """
    alg_dir = os.path.abspath(os.path.join(folder_path, "alg"))
    if not os.path.exists(alg_dir):
        os.mkdir(alg_dir)
    with zipfile.ZipFile(os.path.join(folder_path, zip_file_name), 'r') as zip_ref:
        zip_ref.extractall(alg_dir)

    setup_file_path = os.path.join(alg_dir, "setup.sh")
    if not os.path.exists(setup_file_path):
        if not os.path.join(alg_dir, zip_file_name.rsplit(".")[0], "setup.sh"):
            return "Setup.sh missing. Cannot setup container."
        else:
            setup_file_path = os.path.join(alg_dir, zip_file_name.rsplit(".")[0], "setup.sh")
            alg_dir = os.path.abspath(os.path.join(alg_dir, zip_file_name.rsplit(".")[0]))

    with open(setup_file_path, 'r+') as setup_file:
        contents = setup_file.readlines()

    contents = ["apt update && apt upgrade -y\n cd /alg\n"] + contents
    with open(setup_file_path, 'w') as setup_file:
        setup_file.writelines(contents)

    with open(setup_file_path, "r") as sf:
        print(sf.readlines())

    docker_name = datetime.datetime.now().microsecond
    input_data_path = os.path.abspath(os.path.join(folder_path, "data", "in"))
    gt_data_path = os.path.join(folder_path, "data", "gt")
    result_folder_path = os.path.join(folder_path, "data", "pred")

    os.makedirs(input_data_path, exist_ok=True)
    os.makedirs(gt_data_path, exist_ok=True)
    os.makedirs(result_folder_path, exist_ok=True)

    setup_evaluation_data(input_data_path, gt_data_path)
    subprocess.run(["systemctl", "--user", "start", "docker"], check=True)
    start_docker = ["docker", "run", "--name={}".format(docker_name), "--network", "host",
                    "-v", "{}:/alg".format(alg_dir),
                    "-v", "{}:/data".format(input_data_path),
                    "ubuntu", "bash", "/alg/setup.sh",]
    print("preparation complete. starting docker with: ", " ".join(start_docker))
    p = subprocess.run(start_docker, check=True)
    print(p.returncode, p.stdout)
    p = subprocess.run(["docker", "cp", str(docker_name) + ":/data", result_folder_path], check=True)
    print(p.returncode, p.stdout)
    p = subprocess.run(["docker", "rm", str(docker_name)], check=True)
    print(p.returncode, p.stdout)
    return "Fine."


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
