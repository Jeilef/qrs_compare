import os
import shutil
import zipfile

from werkzeug.utils import secure_filename


class AlgorithmStore:
    __base_path__ = os.path.abspath("algorithms")

    def __init__(self, zip_file, base_path=__base_path__):
        """
        :param alg_name: name of the algorithm
        """
        filename = secure_filename(zip_file.filename)
        alg_name = filename.rsplit('.')[0]
        self.alg_name = alg_name
        self.__base_path__ = os.path.abspath(base_path)
        self.create_hierarchy()
        zip_file.save(os.path.join(self.root_path(), filename))
        self.extract_alg()
        self.check_for_setup_file()

    def create_hierarchy(self):
        os.makedirs(self.root_path(), exist_ok=True)
        os.makedirs(self.algorithm_dir(), exist_ok=True)
        os.makedirs(self.data_dir(), exist_ok=True)
        os.makedirs(self.groundtruth_dir(), exist_ok=True)
        os.makedirs(self.input_dir(), exist_ok=True)
        os.makedirs(self.prediction_dir(), exist_ok=True)
        os.makedirs(self.evaluation_dir(), exist_ok=True)

    def extract_alg(self):
        # fixes issue with zipped folder of files vs. zipped files
        with zipfile.ZipFile(os.path.join(self.root_path(), self.alg_name + ".zip"), 'r') as zip_ref:
            zip_ref.extractall(self.algorithm_dir())
        if len(os.listdir(self.algorithm_dir())) == 1:
            zip_folder = os.path.join(self.algorithm_dir(), os.listdir(self.algorithm_dir())[0])
            if os.path.isdir(zip_folder):
                for ob in os.listdir(zip_folder):
                    shutil.copy2(os.path.join(zip_folder, ob), self.algorithm_dir())

                shutil.rmtree(zip_folder)

    def check_for_setup_file(self):
        if not os.path.exists(self.setup_file_path()):
            raise FileNotFoundError("Could not find setup.sh!")

    def setup_file_path(self):
        return os.path.join(self.algorithm_dir(), "setup.sh")

    def root_path(self):
        return os.path.join(self.__base_path__, self.alg_name)

    def algorithm_dir(self):
        return os.path.join(self.root_path(), "alg")

    def data_dir(self):
        return os.path.join(self.root_path(), "data")

    def groundtruth_dir(self):
        return os.path.join(self.data_dir(), "gt")

    def input_dir(self):
        # contains data for docker container
        return os.path.join(self.data_dir(), "in")

    def prediction_dir(self):
        # output data from docker
        return os.path.join(self.data_dir(), "pred")

    def prediction_dir_copy(self):
        # folder copied out of docker
        return os.path.join(self.prediction_dir(), "data")

    def evaluation_dir(self):
        return os.path.join(self.root_path(), "evaluation")
