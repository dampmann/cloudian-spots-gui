import boto3
import json
from cloudian.awsdatastructures import boto_config
from socket import gaierror
from urllib3.exceptions import NewConnectionError
from botocore.exceptions import ClientError
from botocore.exceptions import EndpointConnectionError
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread

class FleetUpdater(QObject):
    sig_update_status = pyqtSignal(dict)
    sig_update_instances = pyqtSignal(dict)
    sig_error = pyqtSignal(str)

    def __init__(self, profile, access_key):
        super().__init__()
        self.profile = profile
        self.access_key = access_key
        self.stop_exec = False

    def update_status(self):
        if self.stop_exec:
            self.timer.stop()
            QThread.currentThread().quit()
            return

        fleets = []
        regions = None
        try:
            with open('regions.json', mode='r') as fh:
                region_json = fh.read()
                regions = json.loads(region_json)
        except:
            return
        for r in regions:
            if self.stop_exec:
                self.timer.stop()
                QThread.currentThread().quit()
                return

            if r['Enabled']:
                try:
                    s = boto3.Session(
                            profile_name=self.profile, 
                            region_name=r['RegionName'])
                    ec2 = s.resource('ec2')
                    ec2sc = s.client('ec2')
                    if self.stop_exec:
                        self.timer.stop()
                        QThread.currentThread().quit()
                        return
                    fleets = ec2sc.describe_spot_fleet_requests()
                    if 'SpotFleetRequestConfigs' in fleets:
                        f = self.get_fleets(fleets['SpotFleetRequestConfigs'])
                        if not f is None:
                            for fr in f:
                                fleet_item = {
                                        'region': r['RegionName'],
                                        'request_id': fr['SpotFleetRequestId'],
                                        'status': fr['ActivityStatus'],
                                        'state': fr['SpotFleetRequestState'],
                                        'valid_until': fr['SpotFleetRequestConfig']['ValidUntil'],
                                        'capacity': str(fr['SpotFleetRequestConfig']['TargetCapacity']),
                                        'fulfilled': str(fr['SpotFleetRequestConfig']['FulfilledCapacity']),
                                        'token': fr['SpotFleetRequestConfig']['ClientToken'],
                                        'delete': False
                                }
                                if fr['SpotFleetRequestState'] == 'cancelled':
                                    fleet_item['delete'] = True
                                self.sig_update_status.emit(
                                        fleet_item)
                                self.sig_update_instances.emit(
                                    {
                                        'region': r['RegionName'],
                                        'id': fr['SpotFleetRequestId'],
                                        'delete': fleet_item['delete']
                                    }
                                )

                except ClientError as e:
                    print(e)
                    self.sig_error.emit(str(e))
                    pass
                except gaierror as e:
                    print(e)
                    self.sig_error.emit(str(e))
                    pass
                except NewConnectionError as e:
                    print(e)
                    self.sig_error.emit(str(e))
                    pass
                except EndpointConnectionError as e:
                    print(e)
                    self.sig_error.emit(str(e))
                    pass

    def get_fleets(self,fleets):
        fleet_list = []
        for f in fleets:
            if 'ActivityStatus' in f:
                if 'SpotFleetRequestConfig' in f:
                    fr = f['SpotFleetRequestConfig']
                    if 'ClientToken' in fr:
                        if fr['ClientToken'].startswith(self.access_key):
                            fleet_list.append(f) 
            elif 'SpotFleetRequestState' in f:
                if f['SpotFleetRequestState'] != 'active':
                    if 'SpotFleetRequestConfig' in f:
                        fr = f['SpotFleetRequestConfig']
                        if 'ClientToken' in fr:
                            if fr['ClientToken'].startswith(self.access_key):
                                f['ActivityStatus'] = '-'
                                fleet_list.append(f) 

        if len(fleet_list) == 0:
            return None
        else:
            return fleet_list

    def start_thread(self):
        print("Fleet Updater started")
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)

    def stop(self):
        self.stop_exec = True


class InstanceUpdater(QObject):
    sig_update_status = pyqtSignal(dict)
    sig_error = pyqtSignal(str)

    def __init__(self, profile):
        super().__init__()
        self.profile = profile
        self.stop_exec = False
        self.fleet_list = []

    def update_status(self):
        if self.stop_exec:
            self.timer.stop()
            QThread.currentThread().quit()
            return
        for item in self.fleet_list:
            try:
                s = boto3.Session(
                        profile_name=self.profile,
                        region_name=item['region']
                )
                ec2 = s.resource('ec2')

                if self.stop_exec:
                    self.timer.stop()
                    QThread.currentThread().quit()
                    return
                instances = ec2.instances.filter(
                        Filters=[
                            {
                                'Name': 'tag:aws:ec2spot:fleet-request-id', 
                                'Values': [ item['id'] ]
                            }
                ])

                for i in instances:
                    if not i is None:
                        update_item = {
                            'id': item['id'],
                            'sfr': item['id'],
                            'region': item['region'],
                            'tag': '',
                            'sri': i.spot_instance_request_id, 
                            'instance_id':i.instance_id,
                            'private_ip': i.private_ip_address,
                            'public_ip': i.public_ip_address,
                            'delete': item['delete']
                        }
            
                        for t in i.tags:
                            if t['Key'] == 'cloudian-spots':
                                update_item['tag'] = t['Value']

                        if i.subnet and i.subnet.availability_zone:
                            update_item['az'] = i.subnet.availability_zone
                        else:
                            update_item['az'] = 'None'
                        self.sig_update_status.emit(update_item)

            except ClientError as e:
                print(e)
                self.sig_error.emit(str(e))
                pass
            except gaierror as e:
                print(e)
                self.sig_error.emit(str(e))
                pass
            except NewConnectionError as e:
                print(e)
                self.sig_error.emit(str(e))
                pass
            except EndpointConnectionError as e:
                print(e)
                self.sig_error.emit(str(e))
                pass

    def start_thread(self):
        print("Instance Updater started")
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)

    def on_update_instances(self, item):
        self.fleet_list.append(item)

    def stop(self):
        self.stop_exec = True

