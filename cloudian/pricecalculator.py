import boto3
import datetime
from socket import gaierror
from urllib3.exceptions import NewConnectionError
from botocore.exceptions import ClientError
from botocore.exceptions import EndpointConnectionError
from cloudian.awsdatastructures import boto_config

from PyQt5.QtCore import QObject, QTimer, pyqtSignal, QThread

class PriceCalculator(QObject):
    sig_update_price = pyqtSignal(str,float)
    sig_error = pyqtSignal(str)

    def __init__(self, profile):
        super().__init__()
        self.profile = profile
        self.prices = {}
        self.lookup_list = []
        self.stop_exec = False

    def start_thread(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_prices)
        self.timer.start(1000)

    def update_prices(self):
        if self.stop_exec:
            self.timer.stop()
            QThread.currentThread().quit()
            return

        for item in self.lookup_list:
            insn, rn, azn = item.split(':')
            try:
                s = boto3.Session(
                    profile_name=self.profile, 
                    region_name=rn)
                ec2 = s.client('ec2')
                response = ec2.describe_spot_price_history(
                        AvailabilityZone=azn,
                        InstanceTypes=[insn],
                        ProductDescriptions=["Linux/UNIX"],
                        StartTime=datetime.datetime.utcnow()-datetime.timedelta(seconds=5),
                        EndTime=datetime.datetime.utcnow()
                )

                if response and 'SpotPriceHistory' in response:
                    if len(response['SpotPriceHistory']) >= 1:
                        if 'SpotPrice' in response['SpotPriceHistory'][0]:
                            self.prices[item] = float(
                                    response['SpotPriceHistory'][0]['SpotPrice'])
                            self.lookup_list.remove(item)
                            self.sig_update_price.emit(item, self.prices[item])
                        else:
                            print("Price request response invalid for {} nop".format(
                                        item))
                            self.sig_update_price.emit(item, 0.00)
                            self.lookup_list.remove(item)
                    else:
                        print("Price request response invalid for {} (len)".format(
                                    item))
                        self.sig_update_price.emit(item, 0.00)
                        self.lookup_list.remove(item)
                else:
                    print("Price request response invalid for {}".format(item))
                    self.sig_update_price.emit(item, 0.00)
                    self.lookup_list.remove(item)
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

    def lookup_price(self,k):
        if k in self.prices:
            self.sig_update_price.emit(k, self.prices[k])
        else:
            if not k in self.lookup_list:
                self.lookup_list.append(k)

    def stop(self):
        self.stop_exec = True

