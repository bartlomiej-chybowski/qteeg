import numpy as np

from src.frequency import Frequency


class FrequencyFilter:
    def __init__(self, current: int = 50):
        self.current = current

    def band_pass(self, signal: np.array, fft_sample: np.array) -> np.array:
        """
        Band-pass filter.

        Parameters
        ----------
        signal: np.array
        fft_sample: np.array

        Returns
        -------
        np.array
        """
        signal = signal.copy()
        signal[
            (fft_sample < self.low)
            | (fft_sample >= self.high)
            | (fft_sample == self.current)
        ] = 0
        return signal

    def low_pass(self, signal: np.array, fft_sample: np.array) -> np.array:
        """
        Low-pass filter.

        Parameters
        ----------
        signal: np.array
        fft_sample: np.array

        Returns
        -------
        np.array
        """
        signal = signal.copy()
        signal[(fft_sample >= self.low)] = 0
        return signal

    def high_pass(self, signal: np.array, fft_sample: np.array) -> np.array:
        """
        High-pass filter.

        Parameters
        ----------
        signal: np.array
        fft_sample: np.array

        Returns
        -------
        np.array
        """
        signal = signal.copy()
        signal[(fft_sample <= self.high)] = 0
        return signal


class GammaFilter(FrequencyFilter):
    def __init__(self, current: int):
        super().__init__(current)
        self.low = 35
        self.high = 70


class BetaFilter(FrequencyFilter):
    def __init__(self, current: int):
        super().__init__(current)
        self.low = 12
        self.high = 35


class AlphaFilter(FrequencyFilter):
    def __init__(self, current: int):
        super().__init__(current)
        self.low = 8
        self.high = 12


class ThetaFilter(FrequencyFilter):
    def __init__(self, current: int):
        super().__init__(current)
        self.low = 4
        self.high = 8


class DeltaFilter(FrequencyFilter):
    def __init__(self, current: int):
        super().__init__(current)
        self.low = 0.5
        self.high = 4


class FilterFactory:
    def __init__(self, frequency: Frequency) -> None:
        self.frequency = frequency

    def get_filter(self, current: int) -> FrequencyFilter:
        """
        Return FrequencyFilter child for band.

        Parameters
        ----------
        current: int

        Returns
        -------
        FrequencyFilter
        """
        if self.frequency == Frequency.GAMMA:
            return GammaFilter(current)
        elif self.frequency == Frequency.BETA:
            return BetaFilter(current)
        elif self.frequency == Frequency.ALPHA:
            return AlphaFilter(current)
        elif self.frequency == Frequency.THETA:
            return ThetaFilter(current)
        elif self.frequency == Frequency.DELTA:
            return DeltaFilter(current)
