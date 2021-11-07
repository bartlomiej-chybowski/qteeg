import numpy as np

from src.frequency_filter import FrequencyFilter


class TestFrequencyFilter:

    @classmethod
    def setup_class(cls):
        cls.signal = np.array(
            [0., 0.20408163, 0.40816327, 0.6122449, 0.81632653, 1.02040816,
             1.2244898, 1.42857143, 1.63265306, 1.83673469, 2.04081633,
             2.24489796, 2.44897959, 2.65306122, 2.85714286, 3.06122449,
             3.26530612, 3.46938776, 3.67346939, 3.87755102, 4.08163265,
             4.28571429, 4.48979592, 4.69387755, 4.89795918])
        # fft_freq with frequency of 250Hz
        cls.fft_sample = np.array(
            [0., 5., 10., 15., 20., 25., 30., 35., 40., 45., 50., 55., 60., 65.,
             70., 75., 80., 85., 90., 95., 100., 105., 110., 115., 120.])

    def setup_method(self):
        self.frequency_filter = FrequencyFilter()
        self.frequency_filter.low = 10
        self.frequency_filter.high = 20

    def test_band_pass(self):
        result = self.frequency_filter.band_pass(self.signal, self.fft_sample)
        assert np.array_equal(result, np.array(
            [0., 0., 0.40816327, 0.6122449, 0., 0., 0., 0., 0., 0., 0., 0., 0.,
             0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
        ))

    def test_high_pass(self):
        result = self.frequency_filter.high_pass(self.signal, self.fft_sample)
        assert np.array_equal(result, np.array(
            [0., 0., 0., 0., 0., 1.02040816, 1.2244898, 1.42857143,
             1.63265306, 1.83673469, 2.04081633, 2.24489796, 2.44897959,
             2.65306122, 2.85714286, 3.06122449, 3.26530612, 3.46938776,
             3.67346939, 3.87755102, 4.08163265, 4.28571429, 4.48979592,
             4.69387755, 4.89795918]))

    def test_low_pass(self):
        result = self.frequency_filter.low_pass(self.signal, self.fft_sample)
        assert np.array_equal(result, np.array(
            [0., 0.20408163, 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
             0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
        ))

    def test_current_band_pass(self):
        self.frequency_filter.low = 20
        self.frequency_filter.high = 70
        result = self.frequency_filter.band_pass(np.array([1, 2, 3, 4]),
                                                 np.array([20, 50, 60, 70]))
        assert np.array_equal(result, np.array([1, 0, 3, 0]))
