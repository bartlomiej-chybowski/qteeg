from scipy.stats import zscore
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from scipy.stats import median_absolute_deviation
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

MIN_TIME_BETWEEN_SPIKES = 0.03  # 30ms
SEARCH_PERIOD = 0.02  # 20ms
SAMPLING = 256  # 256Hz => 1 sample every ~4ms
SEARCH_SAMPLES = int(SEARCH_PERIOD * SAMPLING)
WAVE_SIZE = int(MIN_TIME_BETWEEN_SPIKES * SAMPLING)


class Spike:
    def __init__(self, name: str):
        self.name = name

        self.spike_threshold: float = 0.
        self.noise_level: float = 0.
        self.data: pd.Series = None
        self.spikes: np.array = None
        self.sorted_spikes: np.array = None
        self.features: np.array = None
        self.clusters: np.array = None

        self.scaler = StandardScaler()
        self.pca = PCA(n_components=2)
        self.kmeans = KMeans(n_clusters=3)

    def set_data(self, data: pd.Series) -> None:
        """
        Set new data.

        Parameters
        ----------
        data: pandas.Series
            Data series with readings from single electrode.

        Returns
        -------
        None
        """
        self.data = data
        self.spike_threshold: float = 0.
        self.noise_level: float = 0.
        self.spikes: np.array = None
        self.sorted_spikes: np.array = None
        self.features: np.array = None

    def _estimate_noise_level(self) -> None:
        """
        Estimate noise level and determine spike threshold.

        Noise level is obtained with usage of median absolute deviation.
        Spike threshold equals noise level multiplied by threshold multiplier.

        Returns
        -------
        None
        """
        self.noise_level = median_absolute_deviation(self.data)
        threshold_mul = -5 if self.noise_level <= (max(self.data) / 5) else -2
        self.spike_threshold = self.noise_level * threshold_mul

    def _find_potential_spikes(self) -> np.array:
        """
        Find potential spikes.

        The first step is to extract only recordings that exceed threshold.
        The second step is to remove potential spikes that are too close
        to each other.

        Returns
        -------
        numpy.array
            Numpy array with indexes of potential spikes.
        """
        data = self.data
        # q1 = data.quantile(0.01)
        # q3 = data.quantile(0.99)
        # data = data[~((data < q1) | (data > q3))]

        potential_spikes = np.diff(
            ((data <= self.spike_threshold) |
             (data >= -self.spike_threshold)).astype(int) > 0).nonzero()[0]
        potential_spikes = potential_spikes[
            (potential_spikes > WAVE_SIZE) &
            (potential_spikes < (len(self.data) - WAVE_SIZE))]

        def _insert_potential_spike():
            return np.insert(np.diff(potential_spikes) >= WAVE_SIZE, 0, True)

        min_spacing = _insert_potential_spike()
        while not np.all(min_spacing):
            potential_spikes = potential_spikes[min_spacing]
            min_spacing = _insert_potential_spike()

        return potential_spikes

    def detect(self) -> pd.Series:
        """
        Detect spikes for data series.

        Save spike indexes.

        Returns
        -------
        pandas.Series
            Pandas series with timestamps of spikes
        """
        self._estimate_noise_level()
        self.spikes = np.array([
            index + np.argmin(self.data[index:index + SEARCH_SAMPLES])
            for index in self._find_potential_spikes()])

        data = self.data * np.nan
        data.iloc[self.spikes] = self.spike_threshold
        return data.dropna()

    def sort(self) -> Tuple[np.array, np.array]:
        """
        Spike sorting.

        Returns
        -------
        Tuple[numpy.array, numpy.array]
            The first element is array with data of all spikes
            The second element is array with mean values of spikes
        """
        if self.spikes is None:
            _ = self.detect()
        waves = []
        for index in self.spikes:
            waves.append(self.data.iloc[
                         (index - WAVE_SIZE):(index + WAVE_SIZE)])

        if len(waves):
            self.sorted_spikes = np.stack(waves)
            return self.sorted_spikes, self.sorted_spikes.mean(axis=0)
        return np.array([]), np.array([])

    def extract_features(self) -> np.array:
        """
        Extract features using PCA.

        Returns
        -------
        numpy.array

        """
        if self.sorted_spikes is None:
            _ = self.sort()
        scaled_spikes = self.scaler.fit_transform(self.sorted_spikes)
        self.features = self.pca.fit_transform(scaled_spikes)
        return self.features

    def cluster(self) -> np.array:
        """
        Return clusters.

        Returns
        -------
        numpy.array
            Array with clusters.
        """
        if self.features is None:
            _ = self.extract_features()
        self.clusters = self.kmeans.fit_predict(self.features)
        return self.clusters, self.features
