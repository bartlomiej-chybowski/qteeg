from typing import Tuple

from scipy.fftpack import fft, rfft, irfft, fftfreq
import numpy as np

from src.frequency import Frequency
from src.frequency_filter import FilterFactory


class Transformer:
    def __init__(self,
                 x: np.array,
                 y: np.array,
                 frequency: Frequency) -> None:
        self.x = x
        self.y = y
        self.freq = frequency

    def get_fft_freq(self, sampling: int = 0.004) -> np.array:
        """
        Get Discrete Fourier Transform sample frequencies.

        MuseS sampling is 250Hz

        Parameters
        ----------
        sampling: int

        Returns
        -------
        np.array
            frequencies spectrum
            # TODO: check if spectrum is the correct word
        """
        return fftfreq(self.x.size, sampling)

    def get_fft(self) -> Tuple[np.array, np.array]:
        """
        Get discrete Fourier Transform and amplitude spectrum.

        Returns
        -------
        Tuple[np.array, np.array]
            discrete Fourier Transform, amplitude spectrum
        """
        y_fft = fft(self.y, self.x.size)
        return y_fft, np.abs(y_fft)

    def get_rfft(self) -> np.array:
        """
        Get one-dimensional discrete Fourier Transform for real input.

        Returns
        -------
        np.array
        """
        return rfft(self.y)

    def get_irfft(self, current: int = 50) -> np.array:
        """
        Get inverted Fourier Transform.

        Filter out frequencies for band.

        Parameters
        ----------
        current: int

        Returns
        -------
        np.array
        """
        freq_filter = FilterFactory(self.freq).get_filter(current)
        return irfft(freq_filter.band_pass(self.y, self.get_fft_freq()))
