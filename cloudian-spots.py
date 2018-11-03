import sys
import subprocess
import boto3
import pathlib
import datetime
import string
import random
import base64
import argparse
from cloudian.awsdatastructures import block_device_mappings, launch_spec
from cloudian.awsdatastructures import request_config
from cloudian.handlers import ActionHandler
from cloudian.handlers import FleetRequestHandler
from cloudian.pricecalculator import PriceCalculator
from cloudian.updaters import InstanceUpdater
from cloudian.updaters import FleetUpdater
from cloudian.loaders import IdLoader, FleetRoleLoader, RegionLoader
from cloudian.loaders import S3ResourceLoader
from cloudian.widgets.settingswidget import SettingsWidget
from cloudian.widgets.cosbenchwidget import CosbenchWidget
from cloudian.widgets.insttypewidget import InstTypeWidget
from cloudian.widgets.remotecombo import RemoteCombo
from cloudian.widgets.regionwidget import RegionWidget
from cloudian.widgets.statuswidget import StatusWidget
from cloudian.widgets.fleetwidget import FleetWidget
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject, pyqtSignal, Qt, QProcess, QThread, QTimer
from PyQt5.QtCore import QUrl

class MainWindow(QWidget):
    sig_price_lookup = pyqtSignal(str)
    sig_price_update = pyqtSignal(float)
    sig_id_lookup = pyqtSignal(str)
    sig_request_fleet = pyqtSignal(dict)
    sig_start_updater = pyqtSignal()
    sig_start_fleet_updater = pyqtSignal()
    sig_start_requester = pyqtSignal()
    sig_start_id_thread = pyqtSignal()
    sig_start_calculator = pyqtSignal()
    sig_start_binary_loader = pyqtSignal()
    sig_start_storage_policy_loader = pyqtSignal()
    sig_start_cscript_loader = pyqtSignal()
    sig_start_workload_loader = pyqtSignal()
    sig_start_region_loader = pyqtSignal()
    sig_start_action_handler = pyqtSignal()
    sig_update_status = pyqtSignal(dict)
    sig_update_fleet_status = pyqtSignal(dict)
    sig_reboot_instance = pyqtSignal(dict)
    sig_cancel_fleet_request = pyqtSignal(dict)
    sig_terminate_instance = pyqtSignal(dict)

    def __init__(self, profile, default_region, slack):
        QWidget.__init__(self)
        self.table_headers = ['Region','data center', '# nodes', '# spares']
        amazon_session = boto3.Session(profile_name=profile, 
                region_name=default_region)
        self.access_key = amazon_session.get_credentials().access_key 
        self.secret_key = amazon_session.get_credentials().secret_key 
        self.slack = slack
        self.install_binary = 'None'
        self.storage_policy = 'None'
        self.cscript = 'None'
        self.cb_wl = 'None'
        self.cb_ssl = '0'
        self.cb_users = '1'
        self.fleet_configs = {}
        self.fleet_role_arn = ''
        self.id_table = {}
        self.price_table = {}
        self.external_procs = []
        self.enforce_logical = 1
        self.do_install = 1
        self.delete_volumes = True
        self.expires = 8

        self.action_handler_thread = QThread()
        self.action_handler_thread.started.connect(self.sig_start_action_handler) 
        self.action_handler = ActionHandler(profile)
        self.action_handler.sig_error.connect(self.on_error)
        self.sig_reboot_instance.connect(self.action_handler.enqueue_action)
        self.sig_terminate_instance.connect(self.action_handler.enqueue_action)
        self.sig_cancel_fleet_request.connect(self.action_handler.enqueue_action)
        QApplication.instance().aboutToQuit.connect(self.action_handler.stop)
        self.action_handler.moveToThread(self.action_handler_thread)
        self.sig_start_action_handler.connect(self.action_handler.start_thread)
        self.action_handler_thread.start()

        self.region_loader_thread = QThread()
        self.region_loader_thread.started.connect(self.sig_start_region_loader)
        self.region_loader = RegionLoader(profile,default_region)
        QApplication.instance().aboutToQuit.connect(self.region_loader.stop)
        self.region_loader.moveToThread(self.region_loader_thread)
        self.sig_start_region_loader.connect(self.region_loader.start_thread)
        self.region_widget = RegionWidget(self.region_loader)
        self.region_widget.sig_region_selected.connect(self.on_region_select)
        self.region_widget.sig_region_deselected.connect(self.on_region_deselect)
        self.region_widget.sig_dc_selected.connect(self.on_dc_select)
        self.region_widget.sig_dc_deselected.connect(self.on_dc_deselect)
        self.region_widget.sig_enforce_logical.connect(self.on_enforce_logical)
        self.sig_price_update.connect(self.region_widget.on_price_update)
        self.region_loader_thread.start()

        self.request_thread = QThread()
        self.request_thread.started.connect(self.sig_start_requester)

        self.id_thread = QThread()
        self.id_thread.started.connect(self.sig_start_id_thread)

        self.price_calculator_thread = QThread()
        self.price_calculator_thread.started.connect(self.sig_start_calculator)

        self.binary_widget = RemoteCombo("install binary")
        self.binary_widget.setObjectName('binary_widget')
        self.binary_widget.sig_error.connect(self.on_error)
        self.binary_widget.sig_item_activated.connect(self.on_remote_combo_change)
        self.binary_loader_thread = QThread()
        self.binary_loader_thread.started.connect(self.sig_start_binary_loader)
        self.binary_loader = S3ResourceLoader(profile,default_region,'installer/', '.bin')
        self.binary_loader.setObjectName('binary_loader')
        self.binary_loader.moveToThread(self.binary_loader_thread)
        QApplication.instance().aboutToQuit.connect(self.binary_loader.stop)
        self.sig_start_binary_loader.connect(self.binary_loader.start_thread)
        self.binary_loader.sig_progress.connect(self.binary_widget.on_progress)
        self.binary_loader.sig_update_finished.connect(self.binary_widget.on_finished_loading)
        self.binary_loader.sig_update_error.connect(self.binary_widget.on_error_loading)
        self.binary_widget.sig_reload_items.connect(self.binary_loader.request_update)
        self.binary_loader_thread.start()

        self.storage_policy_widget = RemoteCombo("storage policy")
        self.storage_policy_widget.setObjectName('storage_policy_widget')
        self.storage_policy_widget.sig_error.connect(self.on_error)
        self.storage_policy_widget.sig_item_activated.connect(self.on_remote_combo_change)
        self.storage_policy_loader_thread = QThread()
        self.storage_policy_loader_thread.started.connect(self.sig_start_storage_policy_loader)
        self.storage_policy_loader = S3ResourceLoader(profile,default_region,'stpo/')
        self.storage_policy_loader.setObjectName('storage_policy_loader')
        self.storage_policy_loader.moveToThread(self.storage_policy_loader_thread)
        QApplication.instance().aboutToQuit.connect(self.storage_policy_loader.stop)
        self.sig_start_storage_policy_loader.connect(self.storage_policy_loader.start_thread)
        self.storage_policy_loader.sig_progress.connect(self.storage_policy_widget.on_progress)
        self.storage_policy_loader.sig_update_finished.connect(self.storage_policy_widget.on_finished_loading)
        self.storage_policy_loader.sig_update_error.connect(self.storage_policy_widget.on_error_loading)
        self.storage_policy_widget.sig_reload_items.connect(self.storage_policy_loader.request_update)
        self.storage_policy_loader_thread.start()

        self.cscript_widget = RemoteCombo("custom script")
        self.cscript_widget.setObjectName('cscript_widget')
        self.cscript_widget.sig_error.connect(self.on_error)
        self.cscript_widget.sig_item_activated.connect(self.on_remote_combo_change)
        self.cscript_loader_thread = QThread()
        self.cscript_loader_thread.started.connect(self.sig_start_cscript_loader)
        self.cscript_loader = S3ResourceLoader(profile,default_region,'customscripts/')
        self.cscript_loader.setObjectName('cscript_loader')
        self.cscript_loader.moveToThread(self.cscript_loader_thread)
        QApplication.instance().aboutToQuit.connect(self.cscript_loader.stop)
        self.sig_start_cscript_loader.connect(self.cscript_loader.start_thread)
        self.cscript_loader.sig_progress.connect(self.cscript_widget.on_progress)
        self.cscript_loader.sig_update_finished.connect(self.cscript_widget.on_finished_loading)
        self.cscript_loader.sig_update_error.connect(self.cscript_widget.on_error_loading)
        self.cscript_widget.sig_reload_items.connect(self.cscript_loader.request_update)
        self.cscript_loader_thread.start()

        self.workload_combo = RemoteCombo("cosbench workload")
        self.workload_combo.setObjectName('workload_combo')
        self.workload_combo.sig_error.connect(self.on_error)
        self.workload_combo.sig_item_activated.connect(self.on_remote_combo_change)
        self.workload_loader_thread = QThread()
        self.workload_loader_thread.started.connect(self.sig_start_workload_loader)
        self.workload_loader = S3ResourceLoader(profile,default_region,'workloads/')
        self.workload_loader.setObjectName('workload_loader')
        self.workload_loader.moveToThread(self.workload_loader_thread)
        QApplication.instance().aboutToQuit.connect(self.workload_loader.stop)
        self.sig_start_workload_loader.connect(self.workload_loader.start_thread)
        self.workload_loader.sig_progress.connect(self.workload_combo.on_progress)
        self.workload_loader.sig_update_finished.connect(self.workload_combo.on_finished_loading)
        self.workload_loader.sig_update_error.connect(self.workload_combo.on_error_loading)
        self.workload_combo.sig_reload_items.connect(self.workload_loader.request_update)
        self.workload_loader_thread.start()

        self.updater_thread = QThread()
        self.updater_thread.started.connect(self.sig_start_updater)
        self.instance_updater = InstanceUpdater(profile)
        self.instance_updater.sig_error.connect(self.on_error)
        QApplication.instance().aboutToQuit.connect(self.instance_updater.stop)
        self.instance_updater.moveToThread(self.updater_thread)
        self.instance_updater.sig_update_status.connect(self.sig_update_status)
        self.sig_start_updater.connect(self.instance_updater.start_thread)
        self.updater_thread.start()

        self.fleet_updater_thread = QThread()
        self.fleet_updater_thread.started.connect(self.sig_start_fleet_updater)
        self.fleet_updater = FleetUpdater(profile,self.access_key)
        self.fleet_updater.sig_error.connect(self.on_error)
        QApplication.instance().aboutToQuit.connect(self.fleet_updater.stop)
        self.fleet_updater.moveToThread(self.fleet_updater_thread)
        self.fleet_updater.sig_update_status.connect(self.sig_update_fleet_status)
        self.fleet_updater.sig_update_instances.connect(self.instance_updater.on_update_instances)
        self.sig_start_fleet_updater.connect(self.fleet_updater.start_thread)
        self.fleet_updater_thread.start()

        self.fleet_requester = FleetRequestHandler(profile)
        self.fleet_requester.moveToThread(self.request_thread)
        QApplication.instance().aboutToQuit.connect(self.fleet_requester.stop)
        self.sig_start_requester.connect(self.fleet_requester.start_thread)
        self.sig_request_fleet.connect(self.fleet_requester.request_fleet)
        self.request_thread.start()

        self.price_calculator = PriceCalculator(profile)
        self.price_calculator.sig_error.connect(self.on_error)
        self.price_calculator.moveToThread(self.price_calculator_thread)
        QApplication.instance().aboutToQuit.connect(self.price_calculator.stop)
        self.sig_start_calculator.connect(self.price_calculator.start_thread)
        self.sig_price_lookup.connect(self.price_calculator.lookup_price)
        self.price_calculator.sig_update_price.connect(self.on_update_price)
        self.price_calculator_thread.start()

        self.id_loader = IdLoader(profile)
        self.id_loader.moveToThread(self.id_thread)
        self.sig_start_id_thread.connect(self.id_loader.start_thread)
        QApplication.instance().aboutToQuit.connect(self.id_loader.stop)
        self.id_loader.sig_update_ids.connect(self.on_update_id)
        self.sig_id_lookup.connect(self.id_loader.lookup_id)
        self.id_thread.start()

        self.inst_type_widget = InstTypeWidget()
        self.inst_type_widget.sig_activated.connect(self.on_recalculate_price)

        self.fleet_role_loader = FleetRoleLoader(profile,default_region)
        self.fleet_role_loader.sig_done.connect(self.on_set_fleet_role)
        self.fleet_role_loader.start()

        self.main_layout = QVBoxLayout()
        self.layout_h1 = QHBoxLayout()
        self.layout_h2 = QHBoxLayout()
        self.layout_v1 = QVBoxLayout()
        self.layout_v2 = QVBoxLayout()
        self.layout_h2.addLayout(self.layout_v1)
        self.layout_h2.addLayout(self.layout_v2)

        self.settings_dialog = QDialog()
        self.settings_dialog.setWindowTitle("Change general settings")
        self.settings_widget = SettingsWidget()
        self.settings_widget.sig_do_install.connect(self.on_do_install_clicked)
        self.settings_widget.sig_delete_volumes.connect(
                self.on_delete_volumes_clicked)
        self.settings_widget.setParent(self.settings_dialog)
        self.settings_button = QPushButton("General settings")
        self.settings_button.clicked.connect(self.on_settings_clicked)
        self.settings_widget.sig_expire_changed.connect(
                self.on_recalculate_price)
        self.cosbench_dialog = QDialog()
        self.cosbench_dialog.setWindowTitle("Adjust cosbench settings")
        self.cosbench_widget = CosbenchWidget(self.workload_combo)
        self.cosbench_widget.sig_cb_ssl_clicked.connect(self.on_cb_ssl_clicked)
        self.cosbench_widget.sig_cb_num_user_changed.connect(
                self.on_cb_users_changed)
        self.cosbench_widget.setParent(self.cosbench_dialog)
        self.cosbench_button = QPushButton("Cosbench settings")
        self.cosbench_button.setEnabled(False)
        self.run_cosbench_cb = QCheckBox("Yes, run cosbench")
        self.run_cosbench_cb.clicked.connect(self.on_cosbench_cb_clicked)
        self.cosbench_button.clicked.connect(self.on_cosbench_clicked)
        self.install_button = QPushButton("Install cluster")
        self.install_button.setEnabled(False)
        self.install_button.clicked.connect(self.on_install_clicked)
        self.layout_h1.addWidget(self.binary_widget)
        self.layout_h1.addWidget(self.storage_policy_widget)
        self.layout_h1.addWidget(self.cscript_widget)
        self.layout_h1.addStretch()
        self.layout_v1.addWidget(self.inst_type_widget)
        self.layout_v1.addWidget(self.run_cosbench_cb)
        self.layout_v1.addWidget(self.cosbench_button)
        self.layout_v1.addWidget(self.settings_button)
        self.layout_v1.addWidget(self.install_button)
        self.layout_v1.addStretch()
        self.layout_v1.setAlignment(Qt.AlignTop|Qt.AlignLeft)
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(len(self.table_headers))
        self.table_widget.setHorizontalHeaderLabels(self.table_headers)
        self.layout_v2.addWidget(self.table_widget)
        self.error_label = QLabel()
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet("font-weight: bold; color: red")
        self.main_layout.addWidget(self.error_label)
        self.main_layout.addWidget(self.region_widget)
        self.main_layout.addLayout(self.layout_h1)
        self.main_layout.addLayout(self.layout_h2)
        self.setLayout(self.main_layout)
        QApplication.instance().aboutToQuit.connect(self.about_to_quit)

    def on_error(self,m):
        self.error_label.setText(m)

    def on_cb_ssl_clicked(self,v):
        self.cb_ssl = str(v)

    def on_cb_users_changed(self,v):
        self.cb_users = str(v)

    def on_do_install_clicked(self,v):
        self.do_install = v

    def on_delete_volumes_clicked(self,v):
        if v == 0:
            self.delete_volumes = False
        else:
            self.delete_volumes = True

    def on_enforce_logical(self,v):
        self.enforce_logical = v
        self.on_recalculate_price('')

    def on_remote_combo_change(self,val):
        if self.sender().objectName() == 'binary_widget':
            if val['index'] == 0:
                self.install_button.setEnabled(False)
                self.install_binary = 'None'
            else:
                self.install_binary = val['value']
                self.install_button.setEnabled(True)
        elif self.sender().objectName() == 'storage_policy_widget':
            if val['index'] == 0:
                self.storage_policy = 'None'
            else:
                self.storage_policy = val['value']
        elif self.sender().objectName() == 'cscript_widget':
            if val['index'] == 0:
                self.cscript = 'None'
            else:
                self.cscript = val['value']
        elif self.sender().objectName() == 'workload_combo':
            if val['index'] == 0:
                self.cb_wl = 'None'
            else:
                self.cb_wl = val['value']

    def on_update_id(self,r, ids):
        self.id_table[r] = ids
        print("on_update_id")
        print(self.id_table)

    def on_region_select(self,r):
        self.sig_id_lookup.emit(r)

    def on_region_deselect(self,r):
        self.on_recalculate_price('')

    def on_set_fleet_role(self,r):
        self.fleet_role_arn = r
        print(self.fleet_role_arn)

    def on_open_ssh(self,ip):
        QDesktopServices.openUrl(
                QUrl('ssh://centos@{}'.format(
                ip)))

    def on_open_cmc(self,subdomain):
        QDesktopServices.openUrl(
                QUrl('http://cmc.{}.cloudian-spots.com:8888/'.format(
                subdomain)))

    def on_open_cosbench(self,subdomain):
        QDesktopServices.openUrl(
            QUrl(
            'http://cosbench.{}.cloudian-spots.com:19088/controller/'.format(
            subdomain)))

    def set_config_value(self, cfg, k, v):
        cfg[k] = v

    def set_launch_spec_value(self, cfg, k, v):
        cfg['launch_spec'][k] = v

    def set_request_config_value(self, cfg, k, v):
        cfg['request_config'][k] = v

    def replace_key_value(self, idata, k, v):
        idata['user_data'] = idata['user_data'].replace(k,v)

    def on_install_clicked(self):
        self.install_button.setEnabled(False)
        self.region_widget.setEnabled(False)
        config = ''
        regions = []
        for i in range(self.table_widget.rowCount()):
            region = self.table_widget.cellWidget(i,0).text()
#           region,az,num_nodes,spares
            config += '{}:{}:{}:{}\n'.format(
                            self.table_widget.cellWidget(i,0).text(),
                            self.table_widget.cellWidget(i,1).text(),
                            self.table_widget.cellWidget(i,2).value(),
                            self.table_widget.cellWidget(i,3).value()
                      )
            if not region in regions:
                regions.append(region)

        stag = ''.join(
                    random.choices(
                        string.ascii_lowercase + string.digits, k=16
        ))
        instance_type = self.inst_type_widget.inst_type_combo.currentText()
        run_cosbench = self.run_cosbench_cb.isChecked() 
        if run_cosbench:
            run_cosbench = '1'
        else:
            run_cosbench = '0'

        cloudian_version = '7'
        nvme_type = ''
        if instance_type.startswith('i'):
            nvme_type = '-nvme'
            if self.install_binary.startswith('CloudianHyperStore-6'):
                print("Error nvme works only with 7")
        if self.install_binary.startswith('CloudianHyperStore-6'):
           cloudian_version = '6' 
        amitag = 'cloudian-spots-ami{}{}'.format(cloudian_version,nvme_type)
        valid_until = (
                datetime.datetime.utcnow()+datetime.timedelta(
                hours=self.expires)
        ).replace(microsecond=0).isoformat() + ' Z'
        target_capacity = 0
        num_nodes = 0
        num_spares = 0
        if self.enforce_logical == 1:
            req = {
                'status': 'pending',
                'region': '',
                'az': '',
                'client_token': self.access_key,
                'access_key': self.access_key,
                'secret_key': self.secret_key,
                'tag': stag,
                'security_group_id': '',
                'subnet_id': '',
                'instance_type': instance_type,
                'ami': '',
                'fleet_role': self.fleet_role_arn, 
                'valid_until': valid_until,
                'target_capacity': 0,
                'num_nodes': '0',
                'num_spares': '0',
                'enforce_logical': str(self.enforce_logical),
                'config': config,
                'do_install': str(self.do_install),
                'version': cloudian_version,
                'regions': ' '.join(map(str, regions)),
                'install_binary': self.install_binary,
                'storage_policy': self.storage_policy,
                'custom_script': self.cscript,
                'run_cosbench': run_cosbench,
                'cosbench_ssl': self.cb_ssl,
                'cosbench_wl': self.cb_wl,
                'cosbench_users': self.cb_users,
                'delete_volumes': self.delete_volumes,
                'slack': self.slack,
                'leader_election': '0'
            }

            for i in reversed(range(self.table_widget.rowCount())):
                target_capacity += self.table_widget.cellWidget(i,2).value() 
                num_nodes += self.table_widget.cellWidget(i,2).value()
                target_capacity += self.table_widget.cellWidget(i,3).value() 
                num_spares += self.table_widget.cellWidget(i,3).value()
                if i == 0:
                    region = self.table_widget.cellWidget(i,0).text()
                    az = self.table_widget.cellWidget(i,1).text()
                    req['region'] = region
                    req['az'] = az
                    req['security_group_id'] = self.id_table[region]['sg']
                    req['subnet_id'] = self.id_table[region][az]
                    req['ami'] = self.id_table[region][amitag]
                    req['target_capacity'] = target_capacity
                    req['num_nodes'] = str(num_nodes)
                    req['num_spares'] = str(num_spares)
                    req['leader_election'] = '1'
                    self.sig_request_fleet.emit(req)
        else:
            for i in reversed(range(self.table_widget.rowCount())):
                region = self.table_widget.cellWidget(i,0).text()
                az = self.table_widget.cellWidget(i,1).text()
                num_nodes = self.table_widget.cellWidget(i,2).value()
                num_spares = self.table_widget.cellWidget(i,3).value()
                target_capacity = num_nodes + num_spares 
                req = {
                    'status': 'pending',
                    'region': region,
                    'az': az,
                    'client_token': self.access_key,
                    'access_key': self.access_key,
                    'secret_key': self.secret_key,
                    'tag': stag,
                    'security_group_id': self.id_table[region]['sg'],
                    'subnet_id': self.id_table[region][az],
                    'instance_type': instance_type,
                    'ami': self.id_table[region][amitag],
                    'fleet_role': self.fleet_role_arn, 
                    'valid_until': valid_until,
                    'target_capacity': target_capacity,
                    'num_nodes': str(num_nodes),
                    'num_spares': str(num_spares),
                    'enforce_logical': str(self.enforce_logical),
                    'config': config,
                    'do_install': str(self.do_install),
                    'version': cloudian_version,
                    'regions': ' '.join(map(str, regions)),
                    'install_binary': self.install_binary,
                    'storage_policy': self.storage_policy,
                    'custom_script': self.cscript,
                    'run_cosbench': run_cosbench,
                    'cosbench_ssl': self.cb_ssl,
                    'cosbench_wl': self.cb_wl,
                    'cosbench_users': self.cb_users,
                    'delete_volumes': self.delete_volumes,
                    'slack': self.slack,
                    'leader_election': '0'
                }
                if i == 0:
                    req['leader_election'] = '1'
                self.sig_request_fleet.emit(req)
        self.install_button.setEnabled(True)
        self.region_widget.setEnabled(True)

    def on_update_price(self, k, v):
        self.price_table[k] = v
        price = 0.0
        if self.enforce_logical == 1:
            if self.table_widget.rowCount() > 0:
                region_name = self.table_widget.cellWidget(0,0).text()
                az_name = self.table_widget.cellWidget(0,1).text()
                rk = "{}:{}:{}".format(
                            self.inst_type_widget.inst_type_combo.currentText(),
                            region_name,az_name)
                for i in range(self.table_widget.rowCount()):
                    if rk in self.price_table:
                        nodes = self.table_widget.cellWidget(i,2).value()
                        spares = self.table_widget.cellWidget(i,3).value()
                        price += (((nodes+spares)*self.expires)*self.price_table[rk])
                    else:
                        self.on_recalculate_price('')
                        return
        else:
            for i in range(self.table_widget.rowCount()):
                region_name = self.table_widget.cellWidget(i,0).text()
                az_name = self.table_widget.cellWidget(i,1).text()
                rk = "{}:{}:{}".format(
                            self.inst_type_widget.inst_type_combo.currentText(),
                            region_name,az_name)
                if rk in self.price_table:
                    nodes = self.table_widget.cellWidget(i,2).value()
                    spares = self.table_widget.cellWidget(i,3).value()
                    price += (((nodes+spares)*self.expires)*self.price_table[rk])
                else:
                    self.on_recalculate_price('')
                    return
        self.sig_price_update.emit(price)

    def on_recalculate_price(self,s):
        if self.table_widget.rowCount() == 0:
            self.sig_price_update.emit(0.00)
        if self.enforce_logical == 1 and self.table_widget.rowCount() > 0:
            region_name = self.table_widget.cellWidget(0,0).text()
            az_name = self.table_widget.cellWidget(0,1).text()
            self.sig_price_lookup.emit("{}:{}:{}".format(
                        self.inst_type_widget.inst_type_combo.currentText(),
                        region_name,az_name))
        else:
            for i in range(self.table_widget.rowCount()):
                region_name = self.table_widget.cellWidget(i,0).text()
                az_name = self.table_widget.cellWidget(i,1).text()
                self.sig_price_lookup.emit("{}:{}:{}".format(
                            self.inst_type_widget.inst_type_combo.currentText(),
                            region_name,az_name))

    def on_settings_clicked(self):
        self.settings_dialog.show()
        self.settings_dialog.adjustSize()

    def on_cosbench_clicked(self):
        self.cosbench_dialog.show()
        self.cosbench_dialog.adjustSize()

    def on_cosbench_cb_clicked(self):
        self.cosbench_button.setEnabled(self.run_cosbench_cb.isChecked())

    def on_reboot_instance(self, action_item):
        self.sig_reboot_instance.emit(action_item)

    def on_terminate_instance(self, action_item):
        self.sig_terminate_instance.emit(action_item)

    def on_cancel_fleet(self, action_item):
        self.sig_cancel_fleet_request.emit(action_item)

    def on_dc_select(self, r):
        self.table_widget.insertRow(0)
        l1 = QLabel(r[:-1])
        l1.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        l2 = QLabel(r)
        l2.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        s1 = QSpinBox()
        s1.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        s1.setValue(1)
        s1.setRange(1,32)
        s1.valueChanged['QString'].connect(self.on_recalculate_price)
        s2 = QSpinBox()
        s2.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        s2.setValue(0)
        s2.setRange(0,32)
        s2.valueChanged['QString'].connect(self.on_recalculate_price)
        self.table_widget.setCellWidget(0, 0, l1)
        self.table_widget.setCellWidget(0, 1, l2)
        self.table_widget.setCellWidget(0, 2, s1)
        self.table_widget.setCellWidget(0, 3, s2)
        self.on_recalculate_price('')

    def on_dc_deselect(self, r):
        del_row = -1
        for i in range(self.table_widget.rowCount()):
            if self.table_widget.cellWidget(i,1).text() == r:
                del_row = i
                break
        if del_row >= 0:
            self.table_widget.removeRow(del_row)
        self.on_recalculate_price('')

    def about_to_quit(self):
        self.action_handler_thread.wait()
        self.region_loader_thread.wait()
        self.binary_loader_thread.wait()
        self.storage_policy_loader_thread.wait()
        self.cscript_loader_thread.wait()
        self.workload_loader_thread.wait()
        self.updater_thread.wait()
        self.fleet_updater_thread.wait()
        self.request_thread.wait()
        self.price_calculator_thread.wait()
        self.id_thread.wait()

def main():
    parser = argparse.ArgumentParser(
            description = 'Start Cloudian clusters on AWS'
    )

    parser.add_argument("-p", "--profile", default='default', help="Amazon profile name (default)")
    parser.add_argument("-s", "--slack", default='', help="Slack name")
    parser.add_argument("-r", "--region", default='us-east-2', help="Default region (us-east-2)")
    parser.add_argument("-n", "--nogui", default=False, action='store_true', help="Use command line")
    argv = parser.parse_args()
    if argv.slack == '':
        print("You have to provide your slack name using -s")
        sys.exit(1)
    # Load spots.sh
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle(
            "Cloudian tool to launch clusters using AWS spot instances")
    tab_widget = QTabWidget()
    w = MainWindow(argv.profile, argv.region, argv.slack)
    status_widget = StatusWidget()
    fleet_widget = FleetWidget()
    fleet_widget.sig_cancel_fleet_request.connect(w.on_cancel_fleet)
    status_widget.sig_open_cmc.connect(w.on_open_cmc)
    status_widget.sig_open_ssh.connect(w.on_open_ssh)
    status_widget.sig_open_cosbench.connect(w.on_open_cosbench)
    status_widget.sig_reboot_instance.connect(w.on_reboot_instance)
    status_widget.sig_terminate_instance.connect(w.on_terminate_instance)
    tab_widget.addTab(w, "Launch Settings")
    tab_widget.addTab(fleet_widget, "Fleet Requests")
    tab_widget.addTab(status_widget, "Instance Status")
    w.sig_update_status.connect(status_widget.on_status_update)
    w.sig_update_fleet_status.connect(fleet_widget.on_status_update)
    window.setCentralWidget(tab_widget)
    window.move(0, 0)
    window.resize(900,700)
    window.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

