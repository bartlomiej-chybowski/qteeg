from datetime import timedelta
from typing import Dict, Optional

import pandas as pd
from PyQt5 import uic, QtWidgets

from src.MplCanvas import MplCanvas
from src.spike import WAVE_SIZE


class MplWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("ui/spike_detection.ui", self)
        self.colours = parent.colours
        self.values: pd.DataFrame = None
        self.canvas: MplCanvas = None
        self.coordinates = [(0, 0, 'TP9'), (0, 1, 'AF7'), (1, 0, 'AF8'),
                            (1, 1, 'TP10')]
        self.spikes = {}

    def set_values(self, values: pd.DataFrame, spikes: Dict) -> None:
        """
        Set new values and reinitialise canvas.

        Parameters
        ----------
        values: pandas.DataFrame
            DataFrame with eeg readings
        spikes: Dict
            Dictionary with Spike objects for each electrode.

        Returns
        -------
        None
        """
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.setCentralWidget(self.canvas)
        self.values = values
        self.spikes = spikes

    def _get_last_readings(self, last: Optional[int] = None) -> pd.DataFrame:
        """
        Get last x seconds of readings

        Parameters
        ----------
        last: int, optional
            Number of seconds to return data for.

        Returns
        -------
        pandas.DataFrame
            DataFrame with eeg recordings.
        """
        data = self.values
        if last:
            end = data.index[-1].to_pydatetime()
            data = data.loc[end - timedelta(seconds=last):end]
        return data

    def plot_spikes(self, last: Optional[int] = None) -> None:
        """
        Detect and plot spikes.

        Parameters
        ----------
        last: int, optional
            Analyse and plot last x seconds.

        Returns
        -------
        None
        """
        def _plot(axis_row: int, axis_col: int, column: str,
                  xy_data: pd.Series) -> None:
            # spike detection
            self.spikes[column].set_data(xy_data)
            detected_spikes = self.spikes[column].detect()
            self.canvas.axes[axis_row, axis_col].scatter(
                detected_spikes.index.to_numpy(), detected_spikes.values,
                s=0.5, c='white')
            # eeg data plot
            self.canvas.axes[axis_row, axis_col].plot(
                xy_data.index.to_numpy(), xy_data.to_numpy(),
                color=self.colours[column], linewidth=0.1)
            self.canvas.axes[axis_row, axis_col].set_title(
                f"{column} (thresh:{self.spikes[column].spike_threshold:.2f}, "
                f"noise:{self.spikes[column].noise_level:.2f})",
                color=self.colours[column])

        data = self._get_last_readings(last)

        for row, col, col_name in self.coordinates:
            _plot(row, col, col_name, data.loc[:, col_name])

        self.canvas.figure.subplots_adjust(wspace=0.3, hspace=0.3)

    def plot_sorted_spikes(self, last: Optional[int] = None) -> None:
        """
        Detect and plot spikes.

        Parameters
        ----------
        last: int, optional
            Analyse and plot last x seconds.

        Returns
        -------
        None
        """
        def _plot(axis_row: int, axis_col: int, column: str,
                  xy_data: pd.Series) -> None:
            self.spikes[column].set_data(xy_data)
            sorted_spikes = self.spikes[column].sort()
            for wave in sorted_spikes[0]:
                self.canvas.axes[axis_row, axis_col].plot(
                    range(-WAVE_SIZE, WAVE_SIZE), wave,
                    color='white', linewidth=0.1)
            if len(sorted_spikes[1]):
                self.canvas.axes[axis_row, axis_col].plot(
                    range(-WAVE_SIZE, WAVE_SIZE), sorted_spikes[1],
                    color='red', linewidth=0.5)

        data = self._get_last_readings(last)

        for row, col, col_name in self.coordinates:
            _plot(row, col, col_name, data.loc[:, col_name])

        self.canvas.figure.subplots_adjust(wspace=0.2, hspace=0.2)

    def plot_features(self) -> None:
        """
        Plot extracted feautres.

        Returns
        -------
        None
        """
        def _plot(axis_row: int, axis_col: int, column: str,
                  xy_data: pd.Series) -> None:
            self.spikes[column].set_data(xy_data)
            features = self.spikes[column].extract_features()
            self.canvas.axes[axis_row, axis_col].scatter(
                features[:, 0], features[:, 1],
                s=1.0, c='white')
            self.canvas.axes[axis_row, axis_col].set_title(
                "PC1 vs PC2", color=self.colours[column])

        for row, col, col_name in self.coordinates:
            _plot(row, col, col_name, self.values.loc[:, col_name])

        self.canvas.figure.subplots_adjust(wspace=0.2, hspace=0.2)

    def plot_clusters(self) -> None:
        """
        Plot clusters.

        Returns
        -------
        None
        """
        def _plot(axis_row: int, axis_col: int, column: str,
                  xy_data: pd.Series) -> None:
            self.spikes[column].set_data(xy_data)
            clusters, features = self.spikes[column].cluster()
            for i, c in zip(range(3), ['r', 'g', 'y']):
                cluster = clusters == i
                self.canvas.axes[axis_row, axis_col].scatter(
                    features[cluster, 0], features[cluster, 1], s=1.0, c=c)
            self.canvas.axes[axis_row, axis_col].set_title(
                "Clusters", color=self.colours[column])

        for row, col, col_name in self.coordinates:
            _plot(row, col, col_name, self.values.loc[:, col_name])

        self.canvas.figure.subplots_adjust(wspace=0.2, hspace=0.2)

    def plot_clustered_waves(self) -> None:
        """
        Plot clustered waves.

        Returns
        -------
        None
        """
        def _plot(axis_row: int, axis_col: int, column: str) -> None:
            clusters = self.spikes[column].clusters
            sorted_spikes = self.spikes[column].sorted_spikes
            for i, c in zip(range(3), ['r', 'g', 'y']):
                cluster = clusters == i
                for wave in sorted_spikes[cluster, :]:
                    self.canvas.axes[axis_row, axis_col].plot(
                        range(-WAVE_SIZE, WAVE_SIZE), wave,
                        color=c, linewidth=0.1)

        for row, col, col_name in self.coordinates:
            _plot(row, col, col_name)

        self.canvas.figure.subplots_adjust(wspace=0.2, hspace=0.2)
