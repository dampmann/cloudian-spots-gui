import boto3
import json
from socket import gaierror
from urllib3.exceptions import NewConnectionError
from botocore.exceptions import ClientError
from botocore.exceptions import EndpointConnectionError
import pathlib
from cloudian.awsdatastructures import boto_config
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread

class S3ResourceLoader(QObject):
    sig_progress = pyqtSignal(str)
    sig_update_finished = pyqtSignal(list)
    sig_update_error = pyqtSignal(str)

    def __init__(self, profile, region, prefix, rfilter=''):
        super().__init__()
        self.profile = profile
        self.region = region
        self.prefix = prefix
        self.rfilter = rfilter
        self.items = []
        self.do_update = True
        self.stop_exec = False

    def start_thread(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timeout)
        self.timer.start(1000)

    def on_timeout(self):
        if self.stop_exec:
            self.timer.stop()
            QThread.currentThread().quit()

        if self.do_update:
            self.do_update = False
            self.items.clear()
            try:
                s = boto3.Session(
                        profile_name=self.profile, 
                        region_name=self.region)
                s3 = s.client('s3')
                response = s3.list_objects(
                        Bucket='cloudian-qtspots',
                        Prefix=self.prefix)
                if 'Contents' in response:
                    for o in response['Contents']:
                        if self.rfilter != '':
                            if pathlib.PurePosixPath(o['Key']).name.endswith(self.rfilter):
                                self.items.append(pathlib.PurePosixPath(o['Key']).name)
                                self.sig_progress.emit("Loaded {}".format(
                                            pathlib.PurePosixPath(o['Key']).name))
                        else:
                            self.items.append(pathlib.PurePosixPath(o['Key']).name)
                            self.sig_progress.emit("Loaded {}".format(
                                        pathlib.PurePosixPath(o['Key']).name))
                self.sig_update_finished.emit(self.items)
                if len(self.items) == 0:
                    self.sig_update_error.emit(
                            "Loader returned an empty result.")

            except ClientError as e:
                print(e)
                self.sig_update_error.emit(str(e))
                pass
            except gaierror as e:
                print(e)
                self.sig_update_error.emit(str(e))
                pass
            except NewConnectionError as e:
                print(e)
                self.sig_update_error.emit(str(e))
                pass
            except EndpointConnectionError as e:
                print(e)
                self.sig_update_error.emit(str(e))
                pass

    def request_update(self):
        self.do_update = True

    def stop(self):
        self.stop_exec = True

class IdLoader(QObject):
    sig_update_ids = pyqtSignal(str,dict)
    sig_update_error = pyqtSignal(str)

    def __init__(self, profile):
        super().__init__()
        self.profile = profile
        self.ids = {} 
        self.lookup_list = []
        self.stop_exec = False

    def start_thread(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ids)
        self.timer.start(1000)

    def update_ids(self):
        if self.stop_exec:
            self.timer.stop()
            QThread.currentThread().quit()
            return
        for item in self.lookup_list:
            try:
                s = boto3.Session(
                    profile_name=self.profile, 
                    region_name=item)
                result = {}
                ec2 = s.resource('ec2')
                for sg in ec2.security_groups.all():
                    if sg.tags and sg.tags[0]['Value'].startswith(
                            'cloudian-spots'):
                        result['sg'] = sg.group_id

                for sn in ec2.subnets.all():
                    if sn.tags and sn.tags[0]['Value'].startswith(
                            'cloudian-spots'):
                        result[sn.availability_zone] = sn.subnet_id

                for ami in ec2.images.filter(Owners=['241130545286']):
                    if ami.tags and ami.tags[0]['Value'].startswith(
                            'cloudian-spots'):
                        result[ami.tags[0]['Value']] = ami.image_id

                self.ids[item] = result
                self.sig_update_ids.emit(item, result)
                self.lookup_list.remove(item)

            except ClientError as e:
                print(e)
                self.sig_update_error.emit(str(e))
                pass
            except gaierror as e:
                print(e)
                self.sig_update_error.emit(str(e))
                pass
            except NewConnectionError as e:
                print(e)
                self.sig_update_error.emit(str(e))
                pass
            except EndpointConnectionError as e:
                print(e)
                self.sig_update_error.emit(str(e))
                pass

    def lookup_id(self,k):
        if k in self.ids:
            self.sig_update_ids.emit(k, self.ids[k])
        else:
            if not k in self.lookup_list:
                self.lookup_list.append(k)

    def stop(self):
        self.stop_exec = True

class FleetRoleLoader(QThread):
    sig_done = pyqtSignal(str)
    sig_error = pyqtSignal(str)

    def __init__(self, profile, region):
        super().__init__()
        self.finished.connect(self.quit)
        self.profile = profile
        self.region = region
        self.fleet_role = ''

    def run(self):
        print("FleetRole loader started")
        self.load_fleet_role()

    def load_fleet_role(self):
        try:
            s = boto3.Session(
                    profile_name=self.profile, 
                    region_name=self.region)
            iam = s.resource('iam')
            for role in iam.roles.all():
                if role.name == 'cloudian-spots-fleet-role':
                    self.sig_done.emit(role.arn)

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

class RegionLoader(QObject):
    sig_done = pyqtSignal(list)
    sig_error = pyqtSignal(str)
    sig_progress = pyqtSignal(int)

    def __init__(self, profile, region):
        super().__init__()
        self.profile = profile
        self.region = region
        self.regions = None 
        self.stop_exec = False


    def start_thread(self):
        print("Region loader started")
        self.load_regions()

    def load_regions(self):
        try:
            with open('regions.json', mode='r') as fh:
                region_json = fh.read()
                self.regions = json.loads(region_json)
                self.sig_done.emit(self.regions)
                QThread.currentThread().quit()
        except:
            try:
                step = 0
                s = boto3.Session(
                        profile_name=self.profile, 
                        region_name=self.region)
                ec2 = s.client('ec2')
                response = ec2.describe_regions()
                region_list = []
                for r in response['Regions']:
                    if self.stop_exec:
                        QThread.currentThread().quit()
                        return
                    e = {}
                    e['RegionName'] = r['RegionName']
                    e['Endpoint'] = r['Endpoint']
                    e['Enabled'] = True
                    e['AvailabilityZones'] = []
                    s = boto3.Session(
                            profile_name='default', 
                            region_name=r['RegionName'])
                    ec2 = s.client('ec2')
                    azs = ec2.describe_availability_zones()
                    for a in azs['AvailabilityZones']:
                        e['AvailabilityZones'].append(a['ZoneName'])
                    step += 1
                    self.sig_progress.emit(step)
                    region_list.append(e)

                    with open('regions.json', mode='w') as fh:
                        fh.write(json.dumps(region_list))

                with open('regions.json', mode='r') as fh:
                    region_json = fh.read()
                    self.regions = json.loads(region_json)

                self.sig_done.emit(self.regions)
                QThread.currentThread().quit()

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
            pass

    def stop(self):
        self.stop_exec = True

