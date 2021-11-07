import numpy as np

from src.frequency import Frequency
from src.transformer import Transformer


class TestTransformer:

    @classmethod
    def setup_class(cls):
        x = np.array(
            [0., 0.11111111, 0.22222222, 0.33333333, 0.44444444, 0.55555556,
             0.66666667, 0.77777778, 0.88888889, 1.])
        # y = np.sin(2 * np.pi * 250 * x)
        y = np.array(
            [0.00000000e+00, -9.84807753e-01, -3.42020143e-01, 8.66025404e-01,
             6.42787610e-01, -6.42787610e-01, -8.66025404e-01, 3.42020143e-01,
             9.84807753e-01, -1.60708323e-13])
        cls.transformer = Transformer(x, y, Frequency.BETA)

    def test_get_fft_freq(self):
        result = self.transformer.get_fft_freq()
        assert np.array_equal(result, np.array(
            [0., 25., 50., 75., 100., -125., -100., -75., -50., -25.]))

    def test_get_fft(self):
        result = self.transformer.get_fft()
        assert np.allclose(result[0], np.array(
            [-1.60704783e-13 - 0.j, -1.48009738e-01 + 0.45552713j,
             -2.51344969e+00 + 3.45946671j, 1.33542895e+00 - 0.97024592j,
             9.06480667e-01 - 0.29453342j, 8.39099632e-01 - 0.j,
             9.06480667e-01 + 0.29453342j, 1.33542895e+00 + 0.97024592j,
             -2.51344969e+00 - 3.45946671j, -1.48009738e-01 - 0.45552713j]))

    def test_get_fft_amplitude(self):
        result = self.transformer.get_fft()
        assert np.allclose(result[1], np.array(
            [1.60704783e-13, 4.78969573e-01, 4.27613602e+00, 1.65068096e+00,
             9.53130178e-01, 8.39099632e-01, 9.53130178e-01, 1.65068096e+00,
             4.27613602e+00, 4.78969573e-01]))

    def test_get_rftt(self):
        result = self.transformer.get_rfft()
        assert np.allclose(result, np.array(
            [-1.60704783e-13, -1.48009738e-01, 4.55527134e-01, -2.51344969e+00,
             3.45946671e+00, 1.33542895e+00, -9.70245923e-01, 9.06480667e-01,
             -2.94533423e-01, 8.39099632e-01]))

    def test_get_irfft(self):
        result = self.transformer.get_irfft()
        assert np.allclose(result, np.array(
            [-0.19696155, -0.15934524, -0.06086447, 0.06086447, 0.15934524,
             0.19696155, 0.15934524, 0.06086447, -0.06086447, -0.15934524]))
