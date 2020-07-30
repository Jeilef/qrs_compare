import sys
sys.path.append('../src')

import math
import unittest

from data_handling.data_docker_setup import ECGData
from matplotlib import pyplot as plt
import numpy as np

from data_handling.signal_to_noise_ratio_helper import transform_signals_to_msa


class TestSignalToNoise(unittest.TestCase):
    def setUp(self) -> None:
        self.ecg = ECGData("../comparison_data_noise/signal",
                           "../comparison_data_noise/annotations", 0, 2, 5)

        self.ecg.read_noise_data()
        print("finished setup")

    def test_unaltered_signal_to_noise_ratio(self):
        self.ecg.__records_per_beat_type__ = 10
        self.ecg.read_data_for_single_type("N")
        normal_beat = self.ecg.test_samples["N"][0]
        plt.plot(normal_beat)
        plt.title("Normal")

        plt.show()

        bl_amp = sum(np.power(self.ecg.baseline_wander_noise[:len(normal_beat)], 2))
        pl_amp = sum(np.power(self.ecg.powerline_noise[:len(normal_beat)], 2))
        em_amp = sum(np.power(self.ecg.electrode_movement_noise[:len(normal_beat)], 2))
        ma_amp = sum(np.power(self.ecg.muscle_artifact_noise[:len(normal_beat)], 2))

        bl_amp2 = sum(np.power(self.ecg.baseline_wander_noise, 2))
        pl_amp2 = sum(np.power(self.ecg.powerline_noise, 2))
        em_amp2 = sum(np.power(self.ecg.electrode_movement_noise, 2))
        ma_amp2 = sum(np.power(self.ecg.muscle_artifact_noise, 2))
        signal_amp = sum(np.power(normal_beat, 2))

        print("normal", signal_amp)
        print("baseline", bl_amp, bl_amp2, signal_amp/bl_amp)
        print("powerline", pl_amp, pl_amp2, signal_amp/pl_amp)
        print("electrode", em_amp, em_amp2, signal_amp/em_amp)
        print("muscle", ma_amp, ma_amp2, signal_amp/ma_amp)

        bw_beat = normal_beat + self.ecg.baseline_wander_noise[:len(normal_beat)]
        pl_beat = normal_beat + self.ecg.powerline_noise[:len(normal_beat)]
        em_beat = normal_beat + self.ecg.electrode_movement_noise[:len(normal_beat)]
        ma_beat = normal_beat + self.ecg.muscle_artifact_noise[:len(normal_beat)]

        plt.plot(bw_beat)
        plt.title("Baseline wander")
        # plt.show()
        plt.plot(pl_beat)
        plt.title("powerline noise")
        # plt.show()
        plt.plot(em_beat)
        plt.title("electrode motion")
        # plt.show()
        plt.plot(ma_beat)
        plt.title("muscle artifacts")
        # plt.show()

    def test_mean_amplitude(self):
        self.ecg.__records_per_beat_type__ = 10000
        self.ecg.read_noise_data()
        self.ecg.read_all_available_data()
        avg_per_type = {}
        for beat_type, splices in self.ecg.test_samples.items():
            avg_per_type[beat_type] = np.mean(np.array(list(map(lambda spli: np.mean(np.power(spli, 2)), splices))))
        print(avg_per_type)
        # {'N': 0.12673581035421988, 'S': 0.31545741044512615, 'V': 0.4212018863140578, 'F': nan, 'Q': nan,
        # 'a': 0.24120892888963802, 'B': 0.08378836546409826, 'J': 0.09012306323387834, 'A': 3.8836342166313202,
        # 'f': 5.853927793682913, 'j': 5.886814070223518, 'L': 4.078953395509646, 'R': 10.753649457019332,
        # 'E': 0.07081220958263441, 'e': 1.3101815667481576, 'n': nan, 'r': nan}

    def test_mean_noise_amplitude(self):
        print("pl", np.mean(np.square(self.ecg.powerline_noise)))
        print("ma", np.mean(np.square(self.ecg.muscle_artifact_noise)))
        print("em", np.mean(np.square(self.ecg.electrode_movement_noise)))
        print("bw", np.mean(np.square(self.ecg.baseline_wander_noise)))

    def test_equal_length_of_noise(self):
        bw_len = len(self.ecg.baseline_wander_noise)
        ma_len = len(self.ecg.muscle_artifact_noise)
        em_len = len(self.ecg.electrode_movement_noise)

        self.assertEqual(bw_len, ma_len)
        self.assertEqual(bw_len, em_len)

    def test_combine_noise_at_level_1(self):
        # all the combined noise shall have a mean squared amplitude of 1
        individual_level = math.sqrt(0.5)  # if two signals are combined, each has to have a level of 0.5 after squaring

        ma_level = np.mean(np.square(self.ecg.muscle_artifact_noise))
        em_level = np.mean(np.square(self.ecg.electrode_movement_noise))
        ma_modified_signal = self.ecg.muscle_artifact_noise / math.sqrt(ma_level) * individual_level
        em_modified_signal = self.ecg.electrode_movement_noise / math.sqrt(em_level) * individual_level
        self.assertAlmostEqual(1, float(np.mean(np.square(ma_modified_signal + em_modified_signal))), 1)

    def test_combine_noise(self):
        comb_sig = transform_signals_to_msa([self.ecg.muscle_artifact_noise, self.ecg.electrode_movement_noise], 1)
        individual_level = math.sqrt(0.5)  # if two signals are combined, each has to have a level of 0.5 after squaring

        ma_level = np.mean(np.square(self.ecg.muscle_artifact_noise))
        em_level = np.mean(np.square(self.ecg.electrode_movement_noise))
        ma_modified_signal = self.ecg.muscle_artifact_noise / math.sqrt(ma_level) * individual_level
        em_modified_signal = self.ecg.electrode_movement_noise / math.sqrt(em_level) * individual_level
        added_sig = ma_modified_signal + em_modified_signal
        print(comb_sig)
        print(added_sig)
        self.assertAlmostEqual(1, float(np.mean(np.square(added_sig))), 1)
        self.assertAlmostEqual(1, float(np.mean(np.square(comb_sig))), 1)
        self.assertEqual(len(added_sig), len(comb_sig))
        for idx in range(len(comb_sig)):
            self.assertEqual(comb_sig[idx][0], added_sig[idx][0])

    def test_get_noise_data(self):
        noise_data = self.ecg.get_noise_samples(200)
        self.assertIsNotNone(noise_data)

    def test_create_all_noise_versions(self):
        self.ecg.__records_per_beat_type__ = 10000
        self.ecg.read_data_for_single_type("N")

    def test_read_all_data(self):
        self.ecg.__records_per_beat_type__ = 5000

        self.ecg.setup_evaluation_data()


if __name__ == '__main__':
    TestSignalToNoise().test_read_all_data()
