import os
import shutil
import zipfile

from werkzeug.utils import secure_filename


class AlgorithmStore:
    __base_path__ = os.path.abspath("algorithms")
    __general_data_path__ = os.path.abspath("comparison_data")

    def __init__(self, alg_name, base_path=__base_path__, general_data_path=__general_data_path__):
        """
        :param alg_name: name of the algorithm
        """

        self.alg_name = alg_name
        self.__base_path__ = os.path.abspath(base_path)
        self.__general_data_path__ = general_data_path

    @classmethod
    def for_new_alg(cls, zip_file, base_path=__base_path__):
        filename = secure_filename(zip_file.filename)
        alg_name = filename.rsplit('.')[0]
        alg_store = cls(alg_name, base_path)
        alg_store.create_hierarchy()
        zip_file.save(os.path.join(alg_store.root_path(), filename))
        alg_store.extract_alg()
        alg_store.check_for_setup_file()
        return alg_store

    @classmethod
    def for_all_existing(cls, base_path=__base_path__, general_data_path=__general_data_path__):
        alg_stores = []
        for alg_dir in os.listdir(base_path):
            alg_stores.append(cls(alg_dir, base_path, general_data_path))
        return alg_stores

    def create_hierarchy(self):
        os.makedirs(self.root_path(), exist_ok=True)
        os.makedirs(self.algorithm_dir(), exist_ok=True)
        os.makedirs(self.groundtruth_dir(), exist_ok=True)
        os.makedirs(self.input_dir(), exist_ok=True)
        os.makedirs(self.prediction_dir(), exist_ok=True)
        os.makedirs(self.evaluation_dir(), exist_ok=True)

    def extract_alg(self):
        if os.path.exists(self.algorithm_dir()):
            shutil.rmtree(self.algorithm_dir(), ignore_errors=True)
            os.makedirs(self.algorithm_dir(), exist_ok=True)
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

    def groundtruth_dir(self):
        return os.path.join(self.__general_data_path__, "annotations")

    def input_dir(self):
        # contains data for docker container
        return os.path.join(self.__general_data_path__, "signal")

    def prediction_dir(self):
        # output data from docker
        return os.path.join(self.root_path(), "pred")

    def evaluation_dir(self):
        return os.path.join(self.root_path(), "evaluation")
