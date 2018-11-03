import boto3
import base64
import pathlib
import copy
import string
import random
from cloudian.awsdatastructures import boto_config
from cloudian.awsdatastructures import block_device_mappings, launch_spec
from cloudian.awsdatastructures import request_config
from socket import gaierror
from urllib3.exceptions import NewConnectionError
from botocore.exceptions import ClientError
from botocore.exceptions import EndpointConnectionError
from collections import deque
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread

class ActionHandler(QObject):

    sig_error = pyqtSignal(str)
    sig_remove_fleet = pyqtSignal(dict)

    def __init__(self, profile):
        super().__init__()
        self.profile = profile
        self.stop_exec = False
        self.action_queue = deque()

    def start_thread(self):
        print("Action handler started")
        self.timer = QTimer()
        self.timer.timeout.connect(self.handle_action)
        self.timer.start(1000)

    def stop(self):
        self.stop_exec = True

    def handle_action(self):
        if self.stop_exec:
            self.timer.stop()
            QThread.currentThread().quit()
            return

        if len(self.action_queue) > 0:
            item = self.action_queue.popleft()
            s = boto3.Session(
                    profile_name=self.profile,
                    region_name=item['region']
            )

            try:

                if item['action'] == 'reboot_instance':
                    ec2 = s.client('ec2')
                    ec2.reboot_instances(
                        InstanceIds=[item['instance_id']]
                    )
                elif item['action'] == 'terminate_instance':
                    ec2 = s.client('ec2')
                    ec2.terminate_instances(
                        InstanceIds=[item['instance_id']]
                    )
                elif item['action'] == 'cancel_fleet':
                    ec2 = s.client('ec2')
                    ec2.cancel_spot_fleet_requests(
                        SpotFleetRequestIds=[item['fleet_id']],
                        TerminateInstances=True
                    )
                    self.sig_remove_fleet.emit({
                        'id': item['fleet_id']
                    })
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

    def enqueue_action(self, item):
        self.action_queue.append(item)

class FleetRequestHandler(QObject):
    sig_watch_request = pyqtSignal(dict)

    def __init__(self, profile):
        super().__init__()
        self.profile = profile
        self.requests = []
        self.stop_exec = False

    def request_pending_fleets(self):
        if self.stop_exec:
            self.timer.stop()
            QThread.currentThread().quit()
            return
        for spec in self.requests:
            if self.stop_exec:
                self.timer.stop()
                QThread.currentThread().quit()
                return
            if spec['status'] == 'pending':
                token_postfix = ''.join(
                            random.choices(
                                string.ascii_lowercase + string.digits, k=5
                ))

                spec['status'] = 'requesting'
                rc = copy.deepcopy(request_config)
                rc['IamFleetRole'] = spec['fleet_role']
                spec['client_token'] = spec['client_token'] + token_postfix
                spec['client_token'] = spec['client_token'] + spec['tag'] 
                rc['ClientToken'] = spec['client_token']
                rc['ValidUntil'] = spec['valid_until']
                rc['TargetCapacity'] = spec['target_capacity']
                ls = copy.deepcopy(launch_spec)
                ls['SecurityGroups'].append(
                    {'GroupName': '', 'GroupId': spec['security_group_id']})
                ls['SubnetId'] = spec['subnet_id']
                ls['InstanceType'] = spec['instance_type']
                ls['ImageId'] = spec['ami']
                ls['TagSpecifications'].append(
                        {'ResourceType': 'instance', 'Tags':[
                        {'Key': 'cloudian-spots', 'Value': spec['tag']},
                        {'Key': 'slack', 'Value': spec['slack']}]})

                for v in ls['BlockDeviceMappings']:
                    if 'DeleteOnTermination' in v:
                        v['DeleteOnTermination'] = spec['delete_volumes']

                ud = ''.join( map(str,pathlib.Path('spots.sh').read_text()))
                ud = ud.replace('___ENFORCE_LOGICAL___', 
                        spec['enforce_logical'])
                ud = ud.replace('___AK___', spec['access_key'])
                ud = ud.replace('___SK___', spec['secret_key'])
                ud = ud.replace('___CONFIG___', spec['config'])
                ud = ud.replace('___DO_INSTALL___', spec['do_install'])
                ud = ud.replace('___VERSION___', spec['version'])
                ud = ud.replace('___SETUP_TAG___', spec['tag'])
                ud = ud.replace('___CLIENT_TOKEN___', spec['client_token'])
                ud = ud.replace('___NUM_NODES___', spec['num_nodes'])
                ud = ud.replace('___NUM_SPARES___', spec['num_spares'])
                ud = ud.replace('___INSTALL_BINARY___', 
                        spec['install_binary'])
                ud = ud.replace('___INSTALL_REGIONS___', spec['regions'])
                ud = ud.replace('___CUSTOM_SCRIPT___', 
                        spec['custom_script'])
                ud = ud.replace('___STORAGE_POLICY___', 
                        spec['storage_policy'])
                ud = ud.replace('___RUN_COSBENCH___', spec['run_cosbench'])
                ud = ud.replace('___COSBENCH_WL___', spec['cosbench_wl'])
                ud = ud.replace('___COSBENCH_SSL___', spec['cosbench_ssl'])
                ud = ud.replace('___COSBENCH_NUMUSER___', 
                        spec['cosbench_users'])
                ud = ud.replace('___LEADER_ELECTION___', 
                        spec['leader_election'])
                ls['UserData'] = base64.b64encode( 
                        bytearray(ud, 'utf-8')).decode('utf-8')
                rc['LaunchSpecifications'].append(ls)
                s = boto3.Session(
                        profile_name=self.profile,
                        region_name=spec['region'])
                ec2 = s.client('ec2')
                response = ec2.request_spot_fleet(SpotFleetRequestConfig=rc)

    def start_thread(self):
        print("FleetRequestHandler started")
        self.timer = QTimer()
        self.timer.timeout.connect(self.request_pending_fleets)
        self.timer.start(1000)

    def request_fleet(self, r):
        self.requests.append(r)

    def stop(self):
        self.stop_exec = True

