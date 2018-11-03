

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QComboBox, QGridLayout

class RemoteCombo(QWidget):

    sig_reload_items = pyqtSignal()
    sig_item_activated = pyqtSignal(dict)
    sig_error = pyqtSignal(str)

    def __init__(self, kind):
        QWidget.__init__(self)
        self.kind = kind
        self.items = []
        self.main_layout = QGridLayout()
        self.combo_box = QComboBox()
        self.combo_box.addItem("Select {}".format(self.kind))
        self.reload_button = QPushButton("reload")
        self.reload_button.clicked.connect(self.on_reload_clicked)
        self.main_layout.addWidget(self.combo_box, 0 ,0)
        self.main_layout.addWidget(self.reload_button, 0 ,1)
        self.setLayout(self.main_layout)
        self.combo_box.activated['QString'].connect(self.on_item_activated)

    def on_item_activated(self,unused):
        self.sig_item_activated.emit({'index': self.combo_box.currentIndex(),
                'value': self.combo_box.currentText()})

    def on_reload_clicked(self):
        self.combo_box.setEnabled(False)
        self.reload_button.setText("Loading ...")
        self.sig_reload_items.emit()

    def on_progress(self, status):
        self.reload_button.setText(status)

    def on_finished_loading(self, items):
        self.reload_button.setText("reload")
        self.items.clear()
        self.items = items 
        self.combo_box.clear()
        self.combo_box.addItem("Select {}".format(self.kind))
        self.combo_box.addItems(self.items)
        self.combo_box.setEnabled(True)

    def on_error_loading(self, msg):
        self.reload_button.setText("reload")
        self.sig_error.emit(msg)

