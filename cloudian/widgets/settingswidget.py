
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget, QLabel, QSpinBox, QCheckBox, QGridLayout
from PyQt5.QtWidgets import QPushButton, QHBoxLayout

class SettingsWidget(QWidget):
    sig_expire_changed = pyqtSignal(str)
    sig_delete_volumes = pyqtSignal(int)
    sig_do_install = pyqtSignal(int)
    sig_ok_clicked = pyqtSignal()

    def __init__(self):
        QWidget.__init__(self)
        self.main_layout = QGridLayout()
        self.install_cb = QCheckBox()
        self.install_label = QLabel("Do not install Hyperstore")
        self.install_cb.clicked.connect(self.on_install_clicked)
        self.main_layout.addWidget(self.install_cb, 0, 0)
        self.main_layout.addWidget(self.install_label, 0, 1)
        self.del_volumes_cb = QCheckBox()
        self.del_volumes_cb.setChecked(True)
        self.del_volumes_label = QLabel("Yes, delete amazon volumes")
        self.del_volumes_cb.clicked.connect(self.on_del_volumes_clicked)
        self.main_layout.addWidget(self.del_volumes_cb, 1, 0)
        self.main_layout.addWidget(self.del_volumes_label, 1, 1)
        self.expires_spinner = QSpinBox()
        self.expires_spinner.setMinimum(1)
        self.expires_spinner.setMaximum(168)
        self.expires_spinner.setValue(8)
        self.expires_spinner.valueChanged['QString'].connect(self.on_expire_change)
        self.spinner_label = QLabel("Cluster expires after x hours")
        self.main_layout.addWidget(self.expires_spinner, 2, 0)
        self.main_layout.addWidget(self.spinner_label, 2, 1)
        self.layout_h = QHBoxLayout()
        self.layout_h.addStretch()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.sig_ok_clicked)
        self.layout_h.addWidget(self.ok_button)
        self.main_layout.addLayout(self.layout_h, 3, 1, 1, 2)
        self.setLayout(self.main_layout)

    def on_expire_change(self,unused):
        self.sig_expire_changed.emit(unused)

    def on_del_volumes_clicked(self):
        if self.sender().isChecked():
            self.sig_delete_volumes.emit(1)
        else:
            self.sig_delete_volumes.emit(0)

    def on_install_clicked(self):
        if self.sender().isChecked():
            self.sig_do_install.emit(0)
        else:
            self.sig_do_install.emit(1)

