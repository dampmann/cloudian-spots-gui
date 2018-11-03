from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox
from PyQt5.QtWidgets import QCheckBox, QProgressBar, QLabel

class RegionWidget(QWidget):

    sig_update_price = pyqtSignal(float)
    sig_region_selected = pyqtSignal(str)
    sig_region_deselected = pyqtSignal(str)
    sig_dc_selected = pyqtSignal(str)
    sig_dc_deselected = pyqtSignal(str)
    sig_enforce_logical = pyqtSignal(int)

    def __init__(self,region_loader):
        QWidget.__init__(self)
        self.region_loader = region_loader
        self.main_layout = QVBoxLayout()
        self.layout_h = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Loading regions and availibility zones")
        self.progress_bar.setRange(0, 15)
        self.layout_h.addWidget(self.progress_bar)
        self.az_group_boxes = {}
        self.region_gb = QGroupBox("Loading regions and availibility zones")
        self.region_gb.setLayout(self.layout_h)
        self.layout_h2 = QHBoxLayout()
        self.enforce_logical = QCheckBox("Enforce logical separation")
        self.enforce_logical.setChecked(True)
        self.enforce_logical.clicked.connect(self.on_enforce_logical)
        self.price_label = QLabel("$ 0.00")
        self.price_label.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        self.sig_update_price.connect(self.on_price_update)
        self.layout_h2.addWidget(self.enforce_logical)
        self.layout_h2.addStretch()
        self.layout_h2.addWidget(self.price_label)
        self.main_layout.addWidget(self.region_gb)
        self.main_layout.addLayout(self.layout_h2)
        self.setLayout(self.main_layout)
        self.region_loader.sig_progress.connect(self.on_progress)
        self.region_loader.sig_done.connect(self.on_regions_loaded)

    def on_price_update(self, price):
        self.price_label.setText("$ {:0.2f}".format(price))

    def on_regions_loaded(self, regions):
        self.region_gb.setTitle("AWS regions")
        self.progress_bar.hide()
        self.regions = regions
        vbox_layouts = [ QVBoxLayout() for i in range(5) ]
        i = 0
        for region in self.regions:
            if 'Enabled' in region and region['Enabled']:
                self.az_group_boxes[region['RegionName']] = QGroupBox(
                        "Availability Zones for {}".format(
                        region['RegionName'])) 
                h = QHBoxLayout()
                for az in region['AvailabilityZones']:
                    dc_cb = QCheckBox(az)
                    dc_cb.clicked.connect(self.on_dc_clicked)
                    h.addWidget(dc_cb,0,Qt.AlignLeft)
                h.addStretch()
                self.az_group_boxes[region['RegionName']].setLayout(h)
                self.az_group_boxes[region['RegionName']].hide()
                self.main_layout.addWidget(
                        self.az_group_boxes[region['RegionName']])
                cb = QCheckBox(region['RegionName'])
                cb.clicked.connect(self.on_region_clicked)
                vbox_layouts[i % len(vbox_layouts)].addWidget(cb)
                i += 1
            
        for layout in vbox_layouts:
            self.layout_h.addLayout(layout)

    def on_enforce_logical(self):
        if self.sender().isChecked():
            self.sig_enforce_logical.emit(1)
        else:
            self.sig_enforce_logical.emit(0)

    def on_progress(self, step):
        self.progress_bar.setValue(step)

    def on_dc_clicked(self):
        if self.sender().isChecked():
            self.sig_dc_selected.emit(self.sender().text())
        else:
            self.sig_dc_deselected.emit(self.sender().text())

    def on_region_clicked(self):
        if self.sender().isChecked():
            self.az_group_boxes[self.sender().text()].show()
            self.sig_region_selected.emit(self.sender().text())
        else:
            c = self.az_group_boxes[self.sender().text()].findChildren(QCheckBox)
            for cld in c:
                if cld.isChecked():
                    cld.setChecked(False)
                    cld.clicked.emit()
            self.az_group_boxes[self.sender().text()].hide()
            self.sig_region_deselected.emit(self.sender().text())


