from typing import Optional, List, Tuple, Any
import matplotlib
import pyqtgraph as pg
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import QCheckBox
import ui.resources  # noqa: F401
from src.UIMainWindow import UIMainWindow
from src.TimeAxisItem import TimeAxisItem
from src.ViewBoxCustom import ViewBoxCustom
from src.frequency import Frequency
from src.helpers import extend_unique, difference
from src.spike import Spike
from src.transformer import Transformer
import logging
import sys

matplotlib.use('Qt5Agg')
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class MainWindow(UIMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.active_bands: List[Frequency] = []
        self.active_series: List[str] = []
        self.axis_items: List[Tuple[str, Frequency, pg.AxisItem]] = []
        self.data: pd.DataFrame = None
        self.plotItem: pg.PlotItem = None
        self.viewBox1: pg.ViewBox = None
        self.view_boxes: List[pg.ViewBox] = []

        self.spikes = {
            'TP9': Spike('TP9'),
            'AF7': Spike('AF7'),
            'AF8': Spike('AF8'),
            'TP10': Spike('TP10')
        }

        self._prepare_frequency_bands()
        self._prepare_modes()
        self._prepare_electrodes()

    @staticmethod
    def zip_longer(labels: List[Any],
                   bands: Optional[List[Any]]) -> zip:
        """
        Zip unequal lists.

        Parameters
        ----------
        labels: List[Any]
        bands: List[Any]

        Returns
        -------
        zip
        """
        if bands is None or len(bands) == 0:
            bands = [None]

        if len(labels) == 1:
            labels = labels * len(bands)
        else:
            bands = bands * len(labels)
        return zip(labels, bands)

    @staticmethod
    def _axis_view_box_name(electrode: str,
                            band: Optional[Frequency] = None) -> str:
        """
        Create name composed from electrode and band.

        Parameters
        ----------
        electrode: str
        band: Frequency

        Returns
        -------
        str
        """
        return "{}{}".format(electrode, f"_{band.name}" if band else '')

    def _name_permutations(self, labels: List[str],
                           bands: Optional[List[Frequency]]) -> List[str]:
        """
        Returns list of all names composed from labels and bands.

        Parameters
        ----------
        labels: List[str]
        bands: List[Frequency], optional

        Returns
        -------
        List[str]
        """
        names = []
        for label in labels:
            for band in bands or [None]:
                names.append(self._axis_view_box_name(label, band))

        return names

    def _default_electrode(self) -> None:
        """
        Select TP9 as main and active series.

        Returns
        -------
        None
        """
        self.active_series.append('TP9')
        self.main_series = 'TP9'
        self.checkboxTP9.blockSignals(True)
        self.checkboxTP9.setChecked(True)
        self.checkboxTP9.blockSignals(False)

    def _default_band(self) -> None:
        """
        Select Frequency.GAMMA as main and active band.

        Returns
        -------
        None
        """
        self.active_bands.append(Frequency.GAMMA)
        self.main_band = Frequency.GAMMA
        self.checkboxGamma.blockSignals(True)
        self.checkboxGamma.setChecked(True)
        self.checkboxGamma.blockSignals(False)

    def _set_limits(self):
        """
        Set limits of view box.

        Returns
        -------
        None
        """
        limits = self.viewBox1.childrenBounds()
        y_min = min([x.childrenBounds()[1][0]
                     for x in self.view_boxes + [self.viewBox1]])
        y_max = max([x.childrenBounds()[1][1]
                     for x in self.view_boxes + [self.viewBox1]])

        for viewBox in self.view_boxes + [self.viewBox1]:
            viewBox.setLimits(xMin=limits[0][0],
                              xMax=limits[0][1],
                              yMin=y_min + y_min / 100,
                              yMax=y_max + y_min / 100)

    def _update_geometry(self) -> None:
        """
        Update geometry of views.

        Returns
        -------
        None
        """
        for viewBox in self.view_boxes:
            viewBox.setGeometry(self.viewBox1.sceneBoundingRect())

    def _get_colour(self, electrode: str,
                    band: Optional[Frequency] = None) -> str:
        """
        Return colour for series from settings.

        Parameters
        ----------
        electrode: str
        band: Frequency, optional

        Returns
        -------
        str
        """
        if (self.electrodes_group.exclusive()
                and not self.frequency_group.exclusive()):
            return self.colours[band.name.upper()]
        else:
            return self.colours[electrode.upper()]

    def _set_main_axis(self) -> None:
        """
        Set main axis.

        Returns
        -------
        None
        """
        if self.main_series not in self.active_series:
            self.active_series.append(self.main_series)
        if self.plotItem in self.graphicsLayout.scene().items():
            self.graphicsLayout.removeItem(self.plotItem)
        self.graphicsLayout.addItem(item=self.plotItem, row=2, col=1, rowspan=1,
                                    colspan=1)
        axis = self.plotItem.getAxis("left")
        axis.setPen(self._get_colour(self.main_series, self.main_band))
        axis.setLabel(color=self._get_colour(self.main_series, self.main_band),
                      text=self._axis_view_box_name(self.main_series,
                                                    self.main_band))

    def _prepare_canvas(self) -> None:
        """
        Prepare canvas.

        Reinitialise central widget and main components.

        Returns
        -------
        None
        """
        self.plotItem = pg.PlotItem(viewBox=ViewBoxCustom(
                name=self._axis_view_box_name(self.main_series, self.main_band)))
        self.plotItem.showGrid(False, False)
        self.viewBox1 = self.plotItem.vb

        self._set_main_axis()
        self.plotItem.setAxisItems(
            {'bottom': TimeAxisItem(orientation='bottom')})

    def _clean(self):
        """
        Clean all viewBoxes from scene.

        Returns
        -------
        None
        """
        if self.graphicsLayout.scene():
            for vb in self.view_boxes:
                self.graphicsLayout.scene().removeItem(vb)
        self.active_series = []
        self.axis_items = []
        self.view_boxes = []

    def _plot(self) -> None:
        """
        Plot the first series.

        Add to view box a corresponding series, set boundaries and limits.

        Returns
        -------
        None
        """
        self.viewBox1.addItem(self._get_plot_item(self.active_series[0],
                                                  self.main_band))
        self._set_limits()
        self.viewBox1.sigResized.connect(self._update_geometry)

    def _autorange(self) -> None:
        """
        Autorange.

        For each viewBox enable auto range.

        Returns
        -------
        None
        """
        for viewBox in self.view_boxes:
            viewBox.enableAutoRange(axis=pg.ViewBox.XYAxes, enable=True)

    def _set_single_series(self, override: Optional[bool] = False) -> None:
        """
        Set single series.

        Parameters
        ----------
        override: bool, optional
            Set main_series to first from active_series

        Returns
        -------
        None
        """
        if self.data is None:
            self.data = self._read_data()
        if override:
            if len(self.active_series) > 0:
                self.main_series = self.active_series[0]
            if self.active_bands and self.main_band not in self.active_bands:
                self.main_band = self.active_bands[0]
        self._prepare_canvas()
        self._plot()

    def _read_data(self) -> pd.DataFrame:
        """
        Read csv file with recordings.

        Returns
        -------
        Pandas.DataFrame
        """
        eeg = pd.read_csv(self.current_file, index_col=0)
        eeg.index = pd.to_datetime((eeg.index * 1000000000).astype(np.int64))
        return eeg

    def _draw_readings(self) -> None:
        """
        Draw readings from csv file.

        Returns
        -------
        None
        """
        self.graphicsLayout = pg.GraphicsLayout()
        self.graphicsView.setCentralWidget(self.graphicsLayout)
        self._set_single_series()
        self.graphicsLayout.nextColumn()

        self.viewBox1.setMouseEnabled(x=True, y=True)
        self.viewBox1.setMenuEnabled(False)
        self._autorange()
        self._update_geometry()

    def _load_file(self):
        """
        Draw main axis output from file.

        Returns
        -------
        None
        """
        self.data = None
        if self.graphicsLayout:
            self._clean()
        self._draw_readings()
        self.message.setText(f"Current file: {self.current_file}")
        self._reselect_checkboxes()
        self.radioTime.setDisabled(False)
        self.radioTime.setChecked(True)
        self.radioFrequencySingle.setDisabled(False)
        self.radioFrequencyMultiple.setDisabled(False)

        self.actionSpike_detecting.setDisabled(False)
        self.actionSpike_sorting.setDisabled(False)
        self.actionFeature_extraction.setDisabled(False)
        self.actionClustering.setDisabled(False)

    def _toggle_frequency(self, disabled: Optional[bool] = True,
                          exclusive: Optional[bool] = False) -> None:
        """
        Toggle frequency bands checkboxes.

        disabled && !exclusive == time domain
        !disabled && exclusive == single frequency
        !disabled && !exclusive == multiple frequencies

        Parameters
        ----------
        disabled: bool, optional
        exclusive: bool, optional

        Returns
        -------
        None
        """
        self.frequency_group.setExclusive(exclusive)
        self.single_frequency = False
        self.main_series = 'TP9'

        if not disabled and not exclusive:
            self.electrodes_group.setExclusive(True)
        else:
            self.single_frequency = True
            self.electrodes_group.setExclusive(False)

        self._clean()
        self._reselect_checkboxes()

        if disabled:
            self.main_band = None
            self.active_bands = []
            self.checkboxGamma.blockSignals(True)
            self.checkboxGamma.setChecked(False)
            self.checkboxGamma.blockSignals(False)
        else:
            self.main_band = Frequency.GAMMA
            self.active_bands = [Frequency.GAMMA]
            self.checkboxGamma.blockSignals(True)
            self.checkboxGamma.setChecked(True)
            self.checkboxGamma.blockSignals(False)

        self.checkboxGamma.setDisabled(disabled)
        self.checkboxAlpha.setDisabled(disabled)
        self.checkboxBeta.setDisabled(disabled)
        self.checkboxTheta.setDisabled(disabled)
        self.checkboxDelta.setDisabled(disabled)

        if self.current_file != '':
            self._draw_readings()

    def _get_plot_item(self, electrode: str,
                       frequency: Optional[Frequency] = None
                       ) -> pg.PlotCurveItem:
        """
        Return PlotCurveItem with reading.

        Parameters
        ----------
        electrode: str
        frequency: Frequency, optional

        Returns
        -------
        pg.PlotCurveItem
        """
        x = list(self.data.index.astype(np.int64))
        y = list(self.data[electrode])
        if frequency:
            transformer = Transformer(np.array(x), np.array(y), frequency)
            x = x
            y = transformer.get_irfft()
        # pen=QPen(QColor(*hex2rgb(self.colours[electrode], 100)))
        pen = self._get_colour(electrode, frequency)
        return pg.PlotCurveItem(x=x, y=y, pen=pen, antialias=True)

    def _checkbox_state(self, checkbox: QCheckBox, label: List[str],
                        band: Optional[List[Frequency]] = None) -> None:
        """
        Slot for checkbox changeState signal.

        If checkbox is checked new axis should be added in other case axis
        should be removed.

        Parameters
        ----------
        checkbox: QCheckBox
        label: List[str]
        band: List[Frequency], optional

        Returns
        -------
        None
        """
        if checkbox.isChecked():
            self._add_series(label, band, checkbox)
        else:
            self._remove_series(label, band, checkbox)

    def _is_last_band(self, checkbox) -> bool:
        """
        Check if last band was selected in multiple frequency mode.

        Parameters
        ----------
        checkbox: QCheckBox

        Returns
        -------
        bool
        """
        return self.radioFrequencyMultiple.isChecked() and (
                len(self.active_bands) > 1
                or checkbox.parent() == self.groupBox_2)

    def _is_last_single_electrode(self, checkbox) -> bool:
        """
        Check if last electrode was selected in single frequency mode.

        Parameters
        ----------
        checkbox: QCheckBox

        Returns
        -------
        bool
        """
        return self.radioFrequencySingle.isChecked() and (
                len(self.active_series) > 1
                or checkbox.parent() == self.groupBox_3)

    def _is_last_electrode(self) -> bool:
        """
        Check if last electrode was selected in time mode.

        Returns
        -------
        bool
        """
        return self.radioTime.isChecked() and len(self.active_series) > 1

    def _is_set_new_main_series(self) -> bool:
        """
        Check if new main series should be set.

        Returns
        -------
        bool
        """
        return (self.main_series not in self.active_series
                and len(self.active_series) > 0) or (
                self.main_band not in self.active_bands
                and len(self.active_bands) > 0)

    def _is_unset_main_series(self, checkbox, labels) -> bool:
        """
        Check if new main series should be set.

        Parameters
        ----------
        checkbox: QCheckBox
        labels: List[str]

        Returns
        -------
        bool
        """
        return (len(labels) == 1 and self.main_series in labels
                and checkbox.parent() == self.groupBox_2)

    def _is_toggle_electrode(self, bands: Optional[List[Frequency]],
                             labels: List[str]) -> bool:
        """
        Check if new main series should be set.

        Parameters
        ----------
        bands: List[Frequency], optional
        labels: List[str]

        Returns
        -------
        bool
        """
        return (len(labels) == 1 and self.main_band in bands
                and self.electrodes_group.exclusive())

    def _is_toggle_band(self, checkbox) -> bool:
        """
        Check if new main series should be set.

        Parameters
        ----------
        checkbox: QCheckBox

        Returns
        -------
        bool
        """
        return (checkbox.parent() == self.groupBox_3
                and self.frequency_group.exclusive())

    def _remove_series(self, labels: List[str],
                       bands: Optional[List[Frequency]] = None,
                       checkbox: Optional[QCheckBox] = None) -> None:
        """
        Remove axis.

        if electrodes_group.exclusive() and not frequency_group.exclusive()
            multiple or time
            remove(label, [band])
        if not electrodes_group.exclusive() and frequency_group.exclusive()
            single
            remove([label], band)

        Parameters
        ----------
        labels: List[str]
        bands: List[Frequency], optional
        checkbox: CheckBox, optional

        Returns
        -------
        None
        """
        if self._is_last_electrode() \
                or self._is_last_single_electrode(checkbox) \
                or self._is_last_band(checkbox):

            if checkbox.parent() == self.groupBox_2:
                self.active_series = difference(self.active_series, labels)
            if checkbox.parent() == self.groupBox_3:
                self.active_bands = difference(self.active_bands, bands)

            if self._is_unset_main_series(checkbox, labels) \
                    or self._is_toggle_band(checkbox) \
                    or self._is_toggle_electrode(bands, labels):

                if self.plotItem in self.graphicsLayout.scene().items():
                    self.graphicsLayout.removeItem(self.plotItem)

                if self._is_set_new_main_series():
                    self._set_single_series(True)
                    if checkbox.parent() == self.groupBox_2:
                        labels = [self.main_series]
                    if checkbox.parent() == self.groupBox_3:
                        bands = [self.main_band]

            axis_items = [x for x in self.axis_items if x[0] in labels]
            if len(bands) > 0:
                axis_items = [x for x in axis_items if x[1] in bands]
            elif self._is_toggle_band(checkbox):
                axis_items = [x for x in self.axis_items]

            for axis_item in axis_items:
                self.axis_items.remove(axis_item)
                self.graphicsLayout.scene().removeItem(axis_item[2])
                self.graphicsLayout.layout.removeItem(axis_item[2])

            view_boxes = [view_box
                          for view_box in self.view_boxes
                          if view_box.name in self._name_permutations(labels,
                                                                      bands)]
            if self._is_toggle_band(checkbox):
                view_boxes = [x for x in self.view_boxes]

            for view_box in view_boxes:
                self.view_boxes.remove(view_box)
                self.graphicsLayout.scene().removeItem(view_box)

            if len(self.view_boxes) > 0:
                self.view_boxes[0].setXLink(self.viewBox1)
                for i in range(1, len(self.view_boxes)):
                    self.view_boxes[i].setXLink(self.view_boxes[i - 1])
        else:
            checkbox.blockSignals(True)
            checkbox.setChecked(True)
            checkbox.blockSignals(False)

    def _add_series(self, labels: List[str],
                    bands: Optional[List[Frequency]] = None,
                    checkbox: Optional[QCheckBox] = None) -> None:
        """
        Add axis.

        When checkbox is selected new series should be added to chart along
        with new axis. New limits and geometry have to be set.

        Parameters
        ----------
        labels: List[str]
        bands: List[Frequency], optional
        checkbox: CheckBox, optional

        Returns
        -------
        None
        """
        extend_unique(self.active_bands, bands)
        extend_unique(self.active_series, labels)
        if len(self.active_series) == 0:
            self._default_electrode()

        if (len(self.active_series) == 1 and
                not self.electrodes_group.exclusive()):
            self._set_single_series(True)
        else:
            if ((self.frequency_group.exclusive()
                and checkbox.parent() == self.groupBox_3)
                    or (self.electrodes_group.exclusive()
                        and (checkbox.parent() == self.groupBox_2
                             or len(self.active_bands) == 1))):
                self._set_single_series(True)

                if (self.frequency_group.exclusive()
                        and checkbox.parent() == self.groupBox_3):
                    labels = [x for x in labels if x != self.main_series]

                if (self.electrodes_group.exclusive()
                        and (checkbox.parent() == self.groupBox_2
                             or len(self.active_bands) == 1)):
                    bands = [x for x in bands if x != self.main_band]
                    if len(bands) == 0:
                        labels = []

            for label, band in self.zip_longer(labels, bands):
                view_box = ViewBoxCustom(
                    name=self._axis_view_box_name(label, band))
                self.view_boxes.append(view_box)
                self.axis_items.append(
                    (label, band, pg.AxisItem(
                        "left", pen=self._get_colour(label, band))))
                index = len(self.axis_items) - 1

                self.graphicsLayout.addItem(
                    item=self.axis_items[index][2], row=2, rowspan=1, colspan=1)
                self.graphicsLayout.scene().addItem(view_box)

                view_box.addItem(self._get_plot_item(label, band))

                self.axis_items[index][2].linkToView(self.view_boxes[index])

                self.view_boxes[0].setXLink(self.viewBox1)
                for i in range(1, len(self.view_boxes)):
                    self.view_boxes[i].setXLink(self.view_boxes[i - 1])

                self.axis_items[index][2].setLabel(
                    self._axis_view_box_name(label, band),
                    pen=self._get_colour(label, band),
                    color=self._get_colour(label, band))

                self._set_limits()

    def _spike_detection_window(self):
        """
        Open Spike Detection window.

        Returns
        -------
        None
        """
        self.spike_detection_window.set_values(self.data, self.spikes)
        self.spike_detection_window.plot_spikes(last=None)
        self.spike_detection_window.show()

    def _spike_sorting_window(self):
        """
        Open Spike Sorting window.

        Returns
        -------
        None
        """
        self.spike_sorting_window.set_values(self.data, self.spikes)
        self.spike_sorting_window.plot_sorted_spikes(last=None)
        self.spike_sorting_window.show()

    def _feature_extraction_window(self):
        """
        Open Feature Extraction window.

        Returns
        -------
        None
        """
        self.feature_extraction_window.set_values(self.data, self.spikes)
        self.feature_extraction_window.plot_features()
        self.feature_extraction_window.show()

    def _clustering_window(self):
        """
        Open Clustering window.

        Returns
        -------
        None
        """
        self.clustering_window.set_values(self.data, self.spikes)
        self.clustering_window.plot_clusters()
        self.clustering_window.show()

    def _wave_clusters_window(self) -> None:
        """
        Open Clustered wave window.

        Returns
        -------
        None
        """
        self.wave_clusters_window.set_values(self.data, self.spikes)
        self.wave_clusters_window.plot_clustered_waves()
        self.wave_clusters_window.show()

    @staticmethod
    def _find_minimum_index(data: np.array, start: int, end: int) -> int:
        """
        Find index of minimum element in array.

        Parameters
        ----------
        data: np.array
        start: int
        end: int

        Returns
        -------
        int
        """
        return np.where(data == np.amin(data[start:end]))[0]
