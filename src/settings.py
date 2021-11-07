import configparser

from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QLineEdit
from PyQt5.QtWidgets import QDialogButtonBox


class SettingsWindow(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("ui/settings.ui", self)
        self.config = None
        self.buttonBox.button(
            QDialogButtonBox.Cancel).clicked.connect(self.close)
        self.buttonBox.button(
            QDialogButtonBox.Save).clicked.connect(self._save_settings)

    def _save_setting(self, section: str, key: str, value: QLineEdit):
        if value.text() != '' and len(value.text()) == 7:
            self.config[section][key] = value.text()

    def _save_settings(self):
        self._save_setting('electrodes', 'tp9', self.tp9_colour)
        self._save_setting('electrodes', 'af7', self.af7_colour)
        self._save_setting('electrodes', 'af8', self.af8_colour)
        self._save_setting('electrodes', 'tp10', self.tp10_colour)
        self._save_setting('bands', 'gamma', self.gamma_colour)
        self._save_setting('bands', 'beta', self.beta_colour)
        self._save_setting('bands', 'alpha', self.alpha_colour)
        self._save_setting('bands', 'theta', self.theta_colour)
        self._save_setting('bands', 'delta', self.delta_colour)
        with open('settings.ini', 'w') as configfile:
            self.config.write(configfile)

    def settings(self, settings):
        self.config = settings
        self.tp9_colour.setText(settings['electrodes']['tp9'])
        self.af7_colour.setText(settings['electrodes']['af7'])
        self.af8_colour.setText(settings['electrodes']['af8'])
        self.tp10_colour.setText(settings['electrodes']['tp10'])

        self.gamma_colour.setText(settings['bands']['gamma'])
        self.beta_colour.setText(settings['bands']['beta'])
        self.alpha_colour.setText(settings['bands']['alpha'])
        self.theta_colour.setText(settings['bands']['theta'])
        self.delta_colour.setText(settings['bands']['delta'])
