from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QCheckBox
from PyQt5.QtWidgets import QSpinBox, QHBoxLayout, QPushButton

class CosbenchWidget(QWidget):
    sig_cb_ssl_clicked = pyqtSignal(int)
    sig_cb_num_user_changed = pyqtSignal(int)
    sig_ok_clicked = pyqtSignal()

    def __init__(self, workload_combo):
        QWidget.__init__(self)
        self.main_layout = QVBoxLayout()
        self.cosbench_group_box_layout = QVBoxLayout()
        self.cosbench_group_box = QGroupBox("Cosbench settings")
        self.cosbench_group_box.setLayout(self.cosbench_group_box_layout)
        self.cosbench_ssl_cb = QCheckBox("Use SSL")
        self.cosbench_ssl_cb.clicked.connect(self.on_ssl_clicked)
        self.cosbench_group_box_layout.addWidget(self.cosbench_ssl_cb)
        self.cosbench_mu_cb = QCheckBox("Yes, do multi-user performance tests")
        self.cosbench_group_box_layout.addWidget(self.cosbench_mu_cb)
        self.cosbench_mu_spinner = QSpinBox()
        self.cosbench_mu_spinner.setMinimum(1)
        self.cosbench_mu_spinner.setMaximum(1000)
        self.cosbench_mu_spinner.setValue(1)
        self.cosbench_mu_spinner.setEnabled(False)
        self.cosbench_group_box_layout.addWidget(self.cosbench_mu_spinner)
        self.workload_combo = workload_combo
        self.cosbench_group_box_layout.addWidget(self.workload_combo)
        self.layout_h = QHBoxLayout()
        self.layout_h.addStretch()
        self.ok_button = QPushButton("OK")
        self.ok_button.setDefault(True)
        self.layout_h.addWidget(self.ok_button)
        self.ok_button.clicked.connect(self.sig_ok_clicked)
        self.cosbench_group_box_layout.addLayout(self.layout_h)
        self.main_layout.addWidget(self.cosbench_group_box)
        self.setLayout(self.main_layout)

    def on_ssl_clicked(self):
        if self.sender().isChecked():
            self.sig_cb_ssl_clicked.emit(1)
        else:
            self.sig_cb_ssl_clicked.emit(0)

    def on_user_change(self):
        self.sig_cb_num_user_changed(self.cosbench_mu_spinner.value())

