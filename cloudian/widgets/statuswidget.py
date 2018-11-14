from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtWidgets import QTableWidget, QLabel, QApplication, QMenu, QAction
from PyQt5.QtWidgets import QAbstractItemView

class StatusWidget(QWidget):
    sig_reboot_instance = pyqtSignal(dict)
    sig_terminate_instance = pyqtSignal(dict)
    sig_open_cmc = pyqtSignal(str)
    sig_open_cosbench = pyqtSignal(str)
    sig_open_ssh = pyqtSignal(str)

    def __init__(self):
        QWidget.__init__(self)
        self.table_headers = [
                                'Region',
                                'Data Center',
                                'Public IP',
                                'Private IP',
                                'Instance ID',
                                'Tag',
                                'SRI',
                                'SFR']
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
        reboot_action = QAction('Reboot instance')
        terminate_action = QAction('Terminate instance')
        cmc_action = QAction('Open CMC')
        cosbench_action = QAction('Open cosbench')
        open_ssh_action = QAction('Open ssh')

        menu.addAction(open_ssh_action)
        menu.addAction(cmc_action)
        menu.addAction(cosbench_action)
        menu.addAction(reboot_action)
        menu.addAction(terminate_action)
        selected_action = menu.exec(self.table_widget.viewport().mapToGlobal(p))
        if selected_action == reboot_action:
            s = self.table_widget.selectionModel().selectedRows()
            if len(s) > 0:
                region = self.table_widget.cellWidget(s[0].row(),0).text()
                iid = self.table_widget.cellWidget(s[0].row(),4).text()
                self.sig_reboot_instance.emit(
                    {
                        'region': region,
                        'instance_id': iid,
                        'action': 'reboot_instance'
                    }         
                )
        elif selected_action == terminate_action:
            s = self.table_widget.selectionModel().selectedRows()
            if len(s) > 0:
                region = self.table_widget.cellWidget(s[0].row(),0).text()
                iid = self.table_widget.cellWidget(s[0].row(),4).text()
                self.sig_terminate_instance.emit(
                    {
                        'region': region,
                        'instance_id': iid,
                        'action': 'terminate_instance'
                    }         
                )
        elif selected_action == open_ssh_action:
            s = self.table_widget.selectionModel().selectedRows()
            if len(s) > 0:
                public_ip = self.table_widget.cellWidget(s[0].row(),2).text()
                self.sig_open_ssh.emit(public_ip)
        elif selected_action == cmc_action:
            s = self.table_widget.selectionModel().selectedRows()
            if len(s) > 0:
                subdomain = self.table_widget.cellWidget(s[0].row(),5).text()
                self.sig_open_cmc.emit(subdomain)
        elif selected_action == cosbench_action:
            s = self.table_widget.selectionModel().selectedRows()
            if len(s) > 0:
                subdomain = self.table_widget.cellWidget(s[0].row(),5).text()
                self.sig_open_cosbench.emit(subdomain)

    def on_cell_clicked(self, r, c):
        txt = self.table_widget.cellWidget(r,c).text()
        clipboard = QApplication.instance().clipboard()
        clipboard.setText(txt)

    def on_status_update(self, item):
        rows = []
        if item['delete']:
            for i in range(self.table_widget.rowCount()):
                if self.table_widget.cellWidget(i,7).text() == item['id']:
                    rows.append(i)
            for r in rows:
                if r < self.table_widget.rowCount():
                    self.table_widget.removeRow(r)
            return

        found = False
        for i in range(self.table_widget.rowCount()):
            if self.table_widget.cellWidget(i,4).text() == item['instance_id']:
                self.table_widget.cellWidget(i,2).setText(item['public_ip'])                
                self.table_widget.cellWidget(i,3).setText(item['private_ip'])                
                self.table_widget.cellWidget(i,7).setText(item['sfr'])                
                self.table_widget.resizeColumnsToContents()
                self.table_widget.resizeRowsToContents()
                found = True
                if item['master'] == True:
                    for c in range(len(self.table_headers)):
                        self.table_widget.cellWidget(i,c).setStyleSheet(
                                "font-weight: bold; color: green")
                else:
                    for c in range(len(self.table_headers)):
                        self.table_widget.cellWidget(i,c).setStyleSheet(
                                "font-weight: normal; color: black")

        if not found:
            self.table_widget.insertRow(0)
            self.table_widget.setCellWidget(0, 0, QLabel(item['region']))
            self.table_widget.cellWidget(0,0).setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
            self.table_widget.cellWidget(0,0).setMargin(10)
            self.table_widget.setCellWidget(0, 1, QLabel(item['az']))
            self.table_widget.cellWidget(0,1).setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
            self.table_widget.cellWidget(0,1).setMargin(10)
            self.table_widget.setCellWidget(0, 2, QLabel(item['public_ip']))
            self.table_widget.cellWidget(0,2).setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
            self.table_widget.cellWidget(0,2).setMargin(10)
            self.table_widget.setCellWidget(0, 3, QLabel(item['private_ip']))
            self.table_widget.cellWidget(0,3).setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
            self.table_widget.cellWidget(0,3).setMargin(10)
            self.table_widget.setCellWidget(0, 4, QLabel(item['instance_id']))
            self.table_widget.cellWidget(0,4).setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
            self.table_widget.cellWidget(0,4).setMargin(10)
            self.table_widget.setCellWidget(0, 5, QLabel(item['tag']))
            self.table_widget.cellWidget(0,5).setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
            self.table_widget.cellWidget(0,5).setMargin(10)
            self.table_widget.setCellWidget(0, 6, QLabel(item['sri']))
            self.table_widget.cellWidget(0,6).setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
            self.table_widget.cellWidget(0,6).setMargin(10)
            self.table_widget.setCellWidget(0, 7, QLabel(item['sfr']))
            self.table_widget.cellWidget(0,7).setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
            self.table_widget.cellWidget(0,7).setMargin(10)
            self.table_widget.resizeColumnsToContents()
            self.table_widget.resizeRowsToContents()

            if item['master'] == True:
                for c in range(len(self.table_headers)):
                    self.table_widget.cellWidget(0,c).setStyleSheet(
                            "font-weight: bold; color: green")
            else:
                for c in range(len(self.table_headers)):
                    self.table_widget.cellWidget(0,c).setStyleSheet(
                            "font-weight: normal; color: black")

