from functools import partial
from time import time, sleep
from PyQt5.QtCore import QObject, pyqtSignal
import pygatt
from muselsl.constants import (AUTO_DISCONNECT_DELAY, MUSE_NB_EEG_CHANNELS,
                               MUSE_SAMPLING_EEG_RATE, LSL_EEG_CHUNK,
                               MUSE_NB_PPG_CHANNELS, MUSE_SAMPLING_PPG_RATE,
                               LSL_PPG_CHUNK, MUSE_NB_ACC_CHANNELS,
                               MUSE_SAMPLING_ACC_RATE, LSL_ACC_CHUNK,
                               MUSE_NB_GYRO_CHANNELS, MUSE_SAMPLING_GYRO_RATE,
                               LSL_GYRO_CHUNK)
from muselsl.muse import Muse
from muselsl.stream import find_muse
from pylsl import StreamInfo, StreamOutlet


class StreamWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        self.progress.emit("Connecting...")
        adapter = pygatt.GATTToolBackend()
        adapter.reset()
        self.progress.emit("Searching device...")
        devices = adapter.filtered_scan("MuseS")
        if len(devices) < 1:
            self.progress.emit("Device not found")
            self.finished.emit()
        else:
            self.progress.emit(f"Device {devices[0]['name']} found")
            sleep(1)
            self.stream(address=devices[0]['address'],
                        ppg_enabled=True,
                        acc_enabled=True,
                        gyro_enabled=True,
                        backend='gatt')
        self.finished.emit()

    def finish(self):
        self.running = False

    def stream(
            self,
            address,
            backend='auto',
            interface=None,
            name=None,
            ppg_enabled=False,
            acc_enabled=False,
            gyro_enabled=False,
            eeg_disabled=False,
            preset=None,
            timeout=AUTO_DISCONNECT_DELAY,
    ):
        """
        Stream.

        All credits to https://github.com/alexandrebarachant/muse-lsl.
        Overridden function to emit progress and programmatically close stream.

        Parameters
        ----------
        address
        backend
        interface
        name
        ppg_enabled
        acc_enabled
        gyro_enabled
        eeg_disabled
        preset
        timeout

        Returns
        -------
        None
        """
        # If no data types are enabled, we warn the user and return immediately.
        if eeg_disabled and not ppg_enabled and not acc_enabled \
                and not gyro_enabled:
            self.progress.emit("Stream initiation failed: "
                               "At least one data source must be enabled.")
            return

        # For any backend except bluemuse, we will start LSL streams hooked up
        # to the muse callbacks.
        if backend != 'bluemuse':
            if not address:
                found_muse = find_muse(name, backend)
                if not found_muse:
                    return
                else:
                    address = found_muse['address']
                    name = found_muse['name']

            if not eeg_disabled:
                eeg_info = StreamInfo('Muse',
                                      'EEG',
                                      MUSE_NB_EEG_CHANNELS,
                                      MUSE_SAMPLING_EEG_RATE,
                                      'float32',
                                      'Muse%s' % address)
                eeg_info.desc().append_child_value("manufacturer", "Muse")
                eeg_channels = eeg_info.desc().append_child("channels")

                for c in ['TP9', 'AF7', 'AF8', 'TP10', 'Right AUX']:
                    eeg_channels.append_child("channel") \
                        .append_child_value("label", c) \
                        .append_child_value("unit", "microvolts") \
                        .append_child_value("type", "EEG")

                eeg_outlet = StreamOutlet(eeg_info, LSL_EEG_CHUNK)

            if ppg_enabled:
                ppg_info = StreamInfo('Muse',
                                      'PPG',
                                      MUSE_NB_PPG_CHANNELS,
                                      MUSE_SAMPLING_PPG_RATE,
                                      'float32',
                                      'Muse%s' % address)
                ppg_info.desc().append_child_value("manufacturer", "Muse")
                ppg_channels = ppg_info.desc().append_child("channels")

                for c in ['PPG1', 'PPG2', 'PPG3']:
                    ppg_channels.append_child("channel") \
                        .append_child_value("label", c) \
                        .append_child_value("unit", "mmHg") \
                        .append_child_value("type", "PPG")

                ppg_outlet = StreamOutlet(ppg_info, LSL_PPG_CHUNK)

            if acc_enabled:
                acc_info = StreamInfo('Muse',
                                      'ACC',
                                      MUSE_NB_ACC_CHANNELS,
                                      MUSE_SAMPLING_ACC_RATE,
                                      'float32',
                                      'Muse%s' % address)
                acc_info.desc().append_child_value("manufacturer", "Muse")
                acc_channels = acc_info.desc().append_child("channels")

                for c in ['X', 'Y', 'Z']:
                    acc_channels.append_child("channel") \
                        .append_child_value("label", c) \
                        .append_child_value("unit", "g") \
                        .append_child_value("type", "accelerometer")

                acc_outlet = StreamOutlet(acc_info, LSL_ACC_CHUNK)

            if gyro_enabled:
                gyro_info = StreamInfo('Muse',
                                       'GYRO',
                                       MUSE_NB_GYRO_CHANNELS,
                                       MUSE_SAMPLING_GYRO_RATE,
                                       'float32',
                                       'Muse%s' % address)
                gyro_info.desc().append_child_value("manufacturer", "Muse")
                gyro_channels = gyro_info.desc().append_child("channels")

                for c in ['X', 'Y', 'Z']:
                    gyro_channels.append_child("channel") \
                        .append_child_value("label", c) \
                        .append_child_value("unit", "dps") \
                        .append_child_value("type", "gyroscope")

                gyro_outlet = StreamOutlet(gyro_info, LSL_GYRO_CHUNK)

            def push(data, timestamps, outlet):
                for ii in range(data.shape[1]):
                    outlet.push_sample(data[:, ii], timestamps[ii])

            push_eeg = partial(push,
                               outlet=eeg_outlet) if not eeg_disabled else None
            push_ppg = partial(push,
                               outlet=ppg_outlet) if ppg_enabled else None
            push_acc = partial(push,
                               outlet=acc_outlet) if acc_enabled else None
            push_gyro = partial(push,
                                outlet=gyro_outlet) if gyro_enabled else None

            muse = Muse(address=address,
                        callback_eeg=push_eeg,
                        callback_ppg=push_ppg,
                        callback_acc=push_acc,
                        callback_gyro=push_gyro,
                        backend=backend,
                        interface=interface,
                        name=name,
                        preset=preset)

            didConnect = muse.connect()

            if didConnect:
                self.progress.emit("Connected")
                muse.start()

                eeg_string = " EEG" if not eeg_disabled else ""
                ppg_string = " PPG" if ppg_enabled else ""
                acc_string = " ACC" if acc_enabled else ""
                gyro_string = " GYRO" if gyro_enabled else ""

                self.progress.emit(f"Streaming {eeg_string}, {ppg_string}, "
                                   f"{acc_string}, {gyro_string}...")

                while time() - muse.last_timestamp < timeout:
                    try:
                        sleep(1)
                        if not self.running:
                            raise KeyboardInterrupt
                    except KeyboardInterrupt:
                        muse.stop()
                        muse.disconnect()
                        break

                self.progress.emit("Disconnected")
