from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox

class InstTypeWidget(QWidget):

    sig_activated = pyqtSignal(str)

    def __init__(self):
        QWidget.__init__(self)
        self.setObjectName('inst_type')
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0,0,0,0)

        self.inst_type_combo = QComboBox()
        self.inst_type_combo.addItems(
                ['d2.xlarge','d2.2xlarge','d2.4xlarge',
                 'd2.8xlarge','i3.16xlarge','i3.metal'])
        self.inst_type_combo.activated['QString'].connect(self.on_item_activated)
        self.main_layout.addWidget(self.inst_type_combo)
        self.setLayout(self.main_layout)

    def on_item_activated(self, item):
        self.sig_activated.emit(item)


