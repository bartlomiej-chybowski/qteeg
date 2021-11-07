import abc
import configparser
from typing import Optional, Dict
import pyqtgraph as pg

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QFileDialog, QCheckBox, QButtonGroup, QLabel

import ui.resources  # noqa: F401

from src.MplWindow import MplWindow
from src.about import AboutWindow
from src.frequency import Frequency
from src.help import HelpWindow
from src.settings import SettingsWindow
from src.stream_worker import StreamWorker


class UIMainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("ui/mainwindow.ui", self)

        self.config = configparser.ConfigParser()
        self.colours: Dict[str, str] = {}
        self._read_settings()
        self.current_file: str = ""
        self.electrodes_group: QButtonGroup = QButtonGroup(self)
        self.frequency_group: QButtonGroup = QButtonGroup(self)
        self.graphicsLayout: pg.GraphicsLayout = pg.GraphicsLayout()
        self.main_series: str = 'TP9'
        self.main_band: Frequency = None
        self.message: QLabel = QLabel()
        self.single_frequency: bool = False
        self.spike_detection_window = MplWindow(self)
        self.spike_sorting_window = MplWindow(self)
        self.feature_extraction_window = MplWindow(self)
        self.clustering_window = MplWindow(self)
        self.wave_clusters_window = MplWindow(self)
        self.stream_thread: QThread = QThread()
        self.stream_worker: StreamWorker = StreamWorker()

        self._connect_menu()
        self.graphicsView.setAntialiasing(True)
        self.graphicsView.setBackground('k')
        self.statusbar.addPermanentWidget(self.message)
        self.statusbar.showMessage("Ready")

    @abc.abstractmethod
    def _load_file(self):
        pass

    @abc.abstractmethod
    def _toggle_frequency(self, disabled: Optional[bool] = True,
                          exclusive: Optional[bool] = False) -> None:
        pass

    @abc.abstractmethod
    def _checkbox_state(self, checkbox: QCheckBox, label: str) -> None:
        pass

    @abc.abstractmethod
    def _spike_detection_window(self) -> None:
        pass

    @abc.abstractmethod
    def _spike_sorting_window(self) -> None:
        pass

    @abc.abstractmethod
    def _clustering_window(self) -> None:
        pass

    @abc.abstractmethod
    def _wave_clusters_window(self) -> None:
        pass

    @abc.abstractmethod
    def _feature_extraction_window(self) -> None:
        pass

    def _report_progress(self, message: str) -> None:
        """
        Slot to report message.

        Parameters
        ----------
        message: str

        Returns
        -------
        None
        """
        self.statusbar.showMessage(message)

    def _close_stream(self) -> None:
        """
        Close stream from device.

        Returns
        -------
        None
        """
        self.stream_worker.finish()
        self.stream_thread.quit()
        self.stream_thread.wait()
        self._report_progress('Disconnected')

        self.actionStream.setDisabled(False)
        self.actionDisconnect.setDisabled(True)

    def _stream_thread(self) -> None:
        """
        Create thread for streaming functionality.

        Returns
        -------
        None
        """
        self.stream_thread = QThread()
        self.stream_worker = StreamWorker()
        self.stream_worker.moveToThread(self.stream_thread)
        self.stream_thread.started.connect(self.stream_worker.run)
        self.stream_worker.finished.connect(self.stream_thread.quit)
        self.stream_worker.finished.connect(self.stream_worker.deleteLater)
        self.stream_thread.finished.connect(self.stream_thread.deleteLater)
        self.stream_worker.progress.connect(self._report_progress)
        self.stream_thread.start()

        self.actionStream.setDisabled(True)
        self.actionDisconnect.setDisabled(False)

        self.stream_thread.finished.connect(
            lambda: self._report_progress('Disconnected')
        )

    def _about_dialog(self) -> None:
        """
        Open about dialog.

        Returns
        -------
        None
        """
        dialog = AboutWindow(self)
        dialog.exec()

    def _help_dialog(self) -> None:
        """
        Open help dialog window.

        Returns
        -------
        None
        """
        dialog = HelpWindow(self)
        dialog.exec()

    def _read_settings(self):
        self.config.read('settings.ini')
        if len(self.config.sections()) == 0:
            self._create_default_settings()
        for key, value in self.config['electrodes'].items():
            self.colours[key.upper()] = value
        for key, value in self.config['bands'].items():
            self.colours[key.upper()] = value

    def _create_default_settings(self):
        """
        Create and save default settings file.

        Returns
        -------
        None
        """
        self.config['electrodes'] = {
            'TP9': '#2E2EFE',
            'AF7': '#00FF00',
            'AF8': '#FFFF00',
            'TP10': '#FF0000',
        }
        self.config['bands'] = {
            'Gamma': '#2E2EFE',
            'Beta': '#00FF00',
            'Alpha': '#FFFF00',
            'Theta': '#FF0000',
            'Delta': '#962A51'
        }
        with open('settings.ini', 'w') as configfile:
            self.config.write(configfile)

    def _settings_dialog(self) -> None:
        """
        Open about dialog.

        Returns
        -------
        None
        """
        dialog = SettingsWindow(self)
        dialog.settings(self.config)
        dialog.exec()

    def _connect_menu(self) -> None:
        """
        Connect all slots to menu positions.

        Returns
        -------
        None
        """
        self.actionSpike_detecting.triggered.connect(
            self._spike_detection_window)
        self.actionSpike_sorting.triggered.connect(
            self._spike_sorting_window)
        self.actionFeature_extraction.triggered.connect(
            self._feature_extraction_window)
        self.actionClustering.triggered.connect(
            self._clustering_window)
        self.actionClustering.triggered.connect(
            self._wave_clusters_window)
        self.actionClose.triggered.connect(self.close)
        self.actionOpen.triggered.connect(self._open_file_name_dialog)
        self.actionSettings.triggered.connect(self._settings_dialog)
        self.actionAbout.triggered.connect(self._about_dialog)
        self.actionHelp.triggered.connect(self._help_dialog)
        self.actionStream.triggered.connect(self._stream_thread)
        self.actionDisconnect.triggered.connect(self._close_stream)

    def _open_file_name_dialog(self) -> None:
        """
        Open file dialog.

        Returns
        -------
        None
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        self.current_file, _ = QFileDialog.getOpenFileName(
            self,
            caption="QFileDialog.getOpenFileName()",
            directory="./assets",
            filter="Comma Separated Values (*.csv)",
            options=options)

        self._load_file()

    def _reselect_checkboxes(self) -> None:
        """
        Reselect all checkboxes to default state.

        Returns
        -------
        None
        """
        for checkbox, state, disabled in [
            (self.checkboxTP9, True, False),
            (self.checkboxAF7, False, False),
            (self.checkboxAF8, False, False),
            (self.checkboxTP10, False, False),
            (self.checkboxGamma, False, True),
            (self.checkboxAlpha, False, True),
            (self.checkboxBeta, False, True),
            (self.checkboxTheta, False, True),
            (self.checkboxDelta, False, True),
        ]:
            checkbox.blockSignals(True)
            checkbox.setChecked(state)
            checkbox.setDisabled(disabled)
            checkbox.blockSignals(False)

    def _prepare_modes(self) -> None:
        """
        Prepare mode radio buttons.

        Returns
        -------
        None
        """
        self.radioTime.setDisabled(True)
        self.radioFrequencySingle.setDisabled(True)
        self.radioFrequencyMultiple.setDisabled(True)
        self.radioTime.setChecked(True)

        self.radioTime.toggled.connect(
            lambda: self._toggle_frequency(True, False))
        self.radioFrequencySingle.toggled.connect(
            lambda: self._toggle_frequency(False, True))
        self.radioFrequencyMultiple.toggled.connect(
            lambda: self._toggle_frequency(False, False))

    def _prepare_frequency_bands(self, disabled: bool = True,
                                 exclusive: bool = False) -> None:
        """
        Prepare frequency bands checkboxes.

        Parameters
        ----------
        disabled: bool
        exclusive: bool

        Returns
        -------
        None
        """
        self.frequency_group.addButton(self.checkboxGamma)
        self.frequency_group.addButton(self.checkboxBeta)
        self.frequency_group.addButton(self.checkboxAlpha)
        self.frequency_group.addButton(self.checkboxTheta)
        self.frequency_group.addButton(self.checkboxDelta)

        self._toggle_frequency(disabled, exclusive)

        self.checkboxGamma.toggled.connect(
            lambda: self._checkbox_state(self.checkboxGamma, self.active_series,
                                         [Frequency.GAMMA]))
        self.checkboxBeta.toggled.connect(
            lambda: self._checkbox_state(self.checkboxBeta, self.active_series,
                                         [Frequency.BETA]))
        self.checkboxAlpha.toggled.connect(
            lambda: self._checkbox_state(self.checkboxAlpha, self.active_series,
                                         [Frequency.ALPHA]))
        self.checkboxTheta.toggled.connect(
            lambda: self._checkbox_state(self.checkboxTheta, self.active_series,
                                         [Frequency.THETA]))
        self.checkboxDelta.toggled.connect(
            lambda: self._checkbox_state(self.checkboxDelta, self.active_series,
                                         [Frequency.DELTA]))

    def _prepare_electrodes(self) -> None:
        """
        Prepare electrodes checkboxes.

        Connect function (slot) to state change event of checkbox (signal).

        Returns
        -------
        None
        """
        self.electrodes_group.addButton(self.checkboxTP9)
        self.electrodes_group.addButton(self.checkboxAF7)
        self.electrodes_group.addButton(self.checkboxAF8)
        self.electrodes_group.addButton(self.checkboxTP10)
        self.electrodes_group.setExclusive(False)

        self.checkboxTP9.setChecked(True)
        self.checkboxTP9.toggled.connect(
            lambda: self._checkbox_state(self.checkboxTP9, ['TP9'],
                                         self.active_bands))
        self.checkboxTP9.setDisabled(True)

        self.checkboxAF7.setChecked(False)
        self.checkboxAF7.toggled.connect(
            lambda: self._checkbox_state(self.checkboxAF7, ['AF7'],
                                         self.active_bands))
        self.checkboxAF7.setDisabled(True)

        self.checkboxAF8.setChecked(False)
        self.checkboxAF8.toggled.connect(
            lambda: self._checkbox_state(self.checkboxAF8, ['AF8'],
                                         self.active_bands))
        self.checkboxAF8.setDisabled(True)

        self.checkboxTP10.setChecked(False)
        self.checkboxTP10.toggled.connect(
            lambda: self._checkbox_state(self.checkboxTP10, ['TP10'],
                                         self.active_bands))
        self.checkboxTP10.setDisabled(True)
