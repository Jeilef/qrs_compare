import unittest

from data_handling.data_docker_setup import ECGData


class TestEcgData(unittest.TestCase):
    def setUp(self) -> None:
        self.ecg = ECGData("/home/Justus.Eilers/comparison_data/signal",
                           "/home/Justus.Eilers/comparison_data/annotations", 0, 0, 1)

    def test_summarize_data(self):
        self.ecg.test_samples = {'L_0.0_em_bw_1': [1, 2],
                                 'J_0.0_em_bw_1': [3, 4]}
        self.ecg.test_fields = {'L_0.0_em_bw_1': [1, 2],
                                 'J_0.0_em_bw_1': [3, 4]}
        self.ecg.test_annotations = {'L_0.0_em_bw_1': [1, 2],
                                 'J_0.0_em_bw_1': [3, 4]}
        self.ecg.summarize_data_of_underrepresented_types()
        print(self.ecg.test_samples, self.ecg.test_fields, self.ecg.test_annotations)
        self.assertEqual(4, len(self.ecg.test_samples['L_0.0_em_bw_1']))