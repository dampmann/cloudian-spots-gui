import datetime
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtWidgets import QTableWidget, QLabel, QApplication, QMenu, QAction
from PyQt5.QtWidgets import QAbstractItemView

class FleetWidget(QWidget):
    sig_cancel_fleet_request = pyqtSignal(dict)

    def __init__(self):
        QWidget.__init__(self)
        self.table_headers = [
                                'Region',
                                'Request Id',
                                'Status',
                                'State',
                                'Capacity',
                                'Fulfilled',
                                'Valid Until',
                                'Error']
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.table_widget = QTableWidget()
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_widget.setColumnCount(len(self.table_headers))
        self.table_widget.setHorizontalHeaderLabels(self.table_headers)
        self.table_widget.cellClicked.connect(self.on_cell_clicked)
        self.table_widget.customContextMenuRequested.connect(self.on_context_menu)
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.main_layout.addWidget(self.table_widget)

    def on_context_menu(self, p):
        menu = QMenu()
        terminate_action = QAction('Terminate request')

        menu.addAction(terminate_action)
        selected_action = menu.exec(self.table_widget.viewport().mapToGlobal(p))
        if selected_action == terminate_action:
            s = self.table_widget.selectionModel().selectedRows()
            if len(s) > 0:
                region = self.table_widget.cellWidget(s[0].row(),0).text()
                rid = self.table_widget.cellWidget(s[0].row(),1).text()
                self.sig_cancel_fleet_request.emit(
                    {
                        'region': region,
                        'fleet_id': rid,
                        'action': 'cancel_fleet'
                    }         
                )

    def on_cell_clicked(self, r, c):
        txt = self.table_widget.cellWidget(r,c).text()
        clipboard = QApplication.instance().clipboard()
        clipboard.setText(txt)

    def on_error_update(self,item):
        print("=== on error update ===")
        for i in range(self.table_widget.rowCount()):
            if self.table_widget.cellWidget(i,1).text() == item['id']:
                self.table_widget.cellWidget(0,7).setText(item['error'])
                self.table_widget.resizeColumnsToContents()
                self.table_widget.resizeRowsToContents()

    def on_status_update(self, item):
        if item['delete']:
            rows = []
            for i in range(self.table_widget.rowCount()):
                if self.table_widget.cellWidget(i,1).text() == item['request_id']:
                    rows.append(i)
            for r in rows:
                if r < self.table_widget.rowCount():
                    self.table_widget.removeRow(r)
            return

        found = False
        item['valid_until'] = item['valid_until'].replace(
                tzinfo=datetime.timezone.utc).astimezone(tz=None).isoformat()
        for i in range(self.table_widget.rowCount()):
            if self.table_widget.cellWidget(i,1).text() == item['request_id']:
                self.table_widget.cellWidget(i,2).setText(item['status'])                
                self.table_widget.cellWidget(i,3).setText(item['state'])                
                self.table_widget.cellWidget(i,4).setText(item['capacity'])                
                self.table_widget.cellWidget(i,5).setText(item['fulfilled'])                
                self.table_widget.resizeColumnsToContents()
                self.table_widget.resizeRowsToContents()
                found = True

        if not found:
            self.table_widget.insertRow(0)
            self.table_widget.setCellWidget(0, 0, QLabel(item['region']))
            self.table_widget.cellWidget(0,0).setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
            self.table_widget.cellWidget(0,0).setMargin(10)
            self.table_widget.setCellWidget(0, 1, QLabel(item['request_id']))
            self.table_widget.cellWidget(0,1).setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
            self.table_widget.cellWidget(0,1).setMargin(10)
            self.table_widget.setCellWidget(0, 2, QLabel(item['status']))
            self.table_widget.cellWidget(0,2).setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
            self.table_widget.cellWidget(0,2).setMargin(10)
            self.table_widget.setCellWidget(0, 3, QLabel(item['state']))
            self.table_widget.cellWidget(0,3).setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
            self.table_widget.cellWidget(0,3).setMargin(10)
            self.table_widget.setCellWidget(0, 4, QLabel(item['capacity']))
            self.table_widget.cellWidget(0,4).setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
            self.table_widget.cellWidget(0,4).setMargin(10)
            self.table_widget.setCellWidget(0, 5, QLabel(item['fulfilled']))
            self.table_widget.cellWidget(0,5).setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
            self.table_widget.cellWidget(0,5).setMargin(10)
            self.table_widget.setCellWidget(0, 6, QLabel(item['valid_until']))
            self.table_widget.cellWidget(0,6).setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
            self.table_widget.cellWidget(0,6).setMargin(10)
            self.table_widget.setCellWidget(0, 7, QLabel('-'))
            self.table_widget.cellWidget(0,7).setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
            self.table_widget.cellWidget(0,7).setMargin(10)
            self.table_widget.cellWidget(0,7).setWordWrap(True)
            self.table_widget.resizeColumnsToContents()
            self.table_widget.resizeRowsToContents()

