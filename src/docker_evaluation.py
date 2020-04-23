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
    alg_dir = os.path.join(folder_path, "alg")
    print(alg_dir)
    if not os.path.exists(alg_dir):
        os.mkdir(alg_dir)
    with zipfile.ZipFile(os.path.join(folder_path, zip_file_name), 'r') as zip_ref:
        print("Extracting")
        zip_ref.extractall(alg_dir)

    setup_file_path = os.path.join(alg_dir, "setup.sh")
    if not os.path.exists(setup_file_path):
        if not os.path.join(alg_dir, zip_file_name.rsplit(".")[0], "setup.sh"):
            return "Setup.sh missing. Cannot setup container."
        else:
            setup_file_path = os.path.join(alg_dir, zip_file_name.rsplit(".")[0], "setup.sh")
            alg_dir = os.path.join(alg_dir, zip_file_name.rsplit(".")[0])

    with open(setup_file_path, 'r+') as setup_file:
        contents = setup_file.readlines()

    contents = ["apt update && apt upgrade -y\n"] + contents
    with open(setup_file_path, 'w') as setup_file:
        setup_file.writelines(contents)

    with open(setup_file_path, "r") as sf:
        print(sf.readlines())

    docker_name = datetime.datetime.now().microsecond
    data_folder_path = os.path.join(folder_path, "data")
    result_folder_path = os.path.join(folder_path, "results")
    if not os.path.exists(result_folder_path):
        os.mkdir(result_folder_path)
    print(setup_file_path)
    setup_evaluation_data(data_folder_path)
    start_docker = ["docker", "run", "--name={}".format(docker_name), "--network host",
                    "-v {}:/ ubuntu bash /setup.sh".format(alg_dir),
                    "-v {}:/data".format(data_folder_path)]
    print("preparation complete. starting docker with: ", start_docker)
    p = subprocess.run(start_docker, capture_output=True, check=True)
    print(p.returncode, p.stdout)
    p = subprocess.run(["docker", "cp", str(docker_name) + ":/data", result_folder_path], capture_output=True,
                       check=True)
    print(p.returncode, p.stdout)
    p = subprocess.run(["docker", "rm", str(docker_name)], capture_output=True, check=True)
    print(p.returncode, p.stdout)
    return "Fine."


def setup_evaluation_data(folder_data_path):
    src = "/mnt/dsets/physionet/mitdb/1.0.0"
    try:
        shutil.copytree(src, folder_data_path)
    except FileExistsError:
        pass
    except OSError as exc:
        if exc.errno == errno.ENOTDIR:
            shutil.copy(src, folder_data_path)
        else:
            raise
