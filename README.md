
## Cloudian-Spots

## Requirements

 - Python >= 3.7
 - boto3
 - pyqt5
 - access key and secret key for your AWS IAM user
 - Your github credentials to access cloudian repositories

## Setup

 1. Install Python >= 3.7 [python.org](https://www.python.org/)
 2. pip3.7 install boto3
 3. pip3.7 install pyqt5
 4. Setup your AWS profile
 5. Clone this repository

## Setup your AWS profile

    mkdir ~/.aws
    cd ~/.aws
    cat config <<EOF
    [default]
    output = json
    region = us-east-2
    
    EOF
    
    cat credentials <<EOF
    [default]                                                                          
    aws_access_key_id = YOUR_ACCESS_KEY                                                
    aws_secret_access_key = YOUR_SECRET_KEY                                            
    region = us-east-2
    
    EOF

## Start the application

Inside the cloned repository directory use the following command to start the application:

    python3.7 cloudian-spots.py

## The Application

![Your main window](https://s3.us-east-2.amazonaws.com/cloudian-qtspots/images/ClusterSpotsNew.jpeg)
![The Fleet request status](https://s3.us-east-2.amazonaws.com/cloudian-qtspots/images/ClusterSpotsNew2.jpeg)
![All your instances](https://s3.us-east-2.amazonaws.com/cloudian-qtspots/images/ClusterSpotsNew3.jpeg)

## Getting started
The first tab allows you to configure your setup. Start by selecting a region and a data center. A new table entry will appear to allow you to set the number of nodes you want to have inside the selected region and data center. In case you want to try to add nodes later you want to set the number of spares accordingly. Continue until your desired setup is configured. By default 

> Enforce logical separation

is enabled. That means that your cloudian cluster looks like it is in different regions and data centers but to make your setup less expensive it will be started in one region and one data center at Amazon. If you uncheck this checkbox **be aware that traffic between nodes is NOT free of charge**. It can become quite expensive quickly. If you need the latency impact then it is still a valid option but you should get an approval of your manager first.
Select an instance type that matches your requirements:

     - d2.2xlarge - 8 cores, 61 GB RAM, 6 x 1.8TB disks 1GBit
     - d2.4xlarge - 16 cores, 122 GB RAM, 12 x 1.8TB disks 1GBit
     - d2.8xlarge - 36 cores, 244 GB RAM, 24 x 1.8 TB disks 10GBit

Select an install binary (even if you don't want the setup to run automatically). Select a storage policy that matches your cluster size and cloudian version (this is optional). Select a custom script you want to be executed after the cluster is up and running. This script will run on the master node. Click general settings, a popup will appear to allow you to adjust the number of hours your cluster will be up and running and opt out to install Hyperstore. Furthermore you can decide to keep the root volume (**additional charges will apply**). Close the popup. At the bottom of the window you can decide to run cosbench automatically on your cluster. After you check the checkbox you can select a workload and decide if you want cosbench to use SSL in the popup window that appears after clicking "Cosbench settings". 

At the top right you can see the price for the compute power you decided to launch not including data transfer charges. Click Install Cluster.

> The expiration time of the cluster can't be changed after you clicked install cluster!

After a few seconds your fleet request(s) should show up in the "Fleet Requests" tab window. It will go through different states like submitted, pending fulfillment and so on. If it fails it will display an error. You need to terminate failed requests by right clicking it and selecting "Terminate". If everything works well instances will appear in the "Instance Status" tab. You can left click each item in the table to copy  it's contents to your clipboard. Right clicking a row displays a context menu to reboot instances, terminate instances, open cmc and open cosbench. Instances don't need to be terminated separately if the fleet request was terminated.

## The deployment

The cluster will always we launched in the region and availability zone you find in the first row of the table **if** enforce logical separation is checked. The master node is the one with the lowest ip address in this region and availability zone.

## How to connect

The ssh keys to access your instances will be downloaded to your home directory. You can connect to an instance using the public ip like this:

    ssh -i AWS-SPOTS-KEY root@<public_ip>
You can check the status of the automatic installation by looking at 

    /root/cloudian-spots/startup.log
By default the setup procedure will add a group performance and a user cosbench. The password is @Cloudian2.
    
## Tools
The master node has two binaries called all and all_wait

You can use it like this:

    all bash -c ‘echo $(hostname) > /etc/hostname’
    all cat /etc/hostname
    all hostname

You can change the way it works using environment variables.

    all - executes args in parallel on all nodes
    all_wait - executes args one by one on all nodes
    set RPCSH_DEBUG to get more verbose output
    set RPCSH_DC_FILTER (comma seperated list of DC names to exclude)
    set RPCSH_REGION_FILTER (comma seperated list of regions to exclude)
    set RPCSH_IP_EXCLUDE (comma seperated list of ip addresses to exclude)
    set RPCSH_IP_ONLY to run only on the host with this ip address
    
 
## Budgets

All accounts have a monthly budget. If your request will exceed the budget you have to
contact your manager. The message will look something like this:

![Budget exceeded](https://s3.us-east-2.amazonaws.com/cloudian-qtspots/images/ClusterSpotsNew4.jpeg)

You will not be able to start a cluster.

## The instances structure

The root home directory of all instances will have the following structure:

    ├── CloudianPackages
    │   ├── 10.112.2.16_fslist.txt
    │   ├── 10.112.2.254_fslist.txt
    │   ├── 10.112.2.55_fslist.txt
    │   ├── 10.112.2.74_fslist.txt
    │   ├── 10.112.2.84_fslist.txt
    │   ├── 10.112.2.9_fslist.txt
    │   ├── ch-us-east-1-us-east-1c-2-254_fslist.txt
    │   ├── ch-us-east-1-us-east-1c-2-74_fslist.txt
    │   ├── ch-us-east-1-us-east-1c-2-84_fslist.txt
    │   ├── ch-us-east-2-us-east-2b-2-16_fslist.txt
    │   ├── ch-us-east-2-us-east-2b-2-55_fslist.txt
    │   ├── ch-us-east-2-us-east-2b-2-9_fslist.txt
    │   ├── cloudian_12345.lic
    │   ├── CloudianHyperStore-7.1.1RC7.bin
    │   ├── cloudian-installation.log
    │   ├── CloudianInstallConfiguration.txt
    │   ├── CloudianInstallConfiguration.txt.installbk
    │   ├── cloudianInstall.sh
    │   ├── cloudian.jks
    │   ├── cloudianpkg-7.1.1.tar.gz
    │   ├── cloudianService.sh
    │   ├── cloudian-upgrade-7.1.1.tar.gz
    │   ├── facter
    │   │   └── cloudian_ipaddress.py
    │   ├── fslist.txt
    │   ├── hosts.cloudian
    │   ├── jetty-http-9.3.23.v20180228.jar
    │   ├── jetty-util-9.3.23.v20180228.jar
    │   ├── jffi-1.2.0-native.jar
    │   ├── lib
    │   │   ├── Cassandra.inc.sh
    │   │   ├── ClusterDesign.inc.sh
    │   │   ├── CSVConfig.inc.sh
    │   │   ├── EnvCheck.inc.sh
    │   │   ├── Host.inc.sh
    │   │   ├── Menu.inc.sh
    │   │   ├── Network.inc.sh
    │   │   ├── Puppet.inc.sh
    │   │   ├── ServiceMap.inc.sh
    │   │   ├── Services.inc.sh
    │   │   ├── SSLCert.inc.sh
    │   │   ├── Survey.inc.sh
    │   │   ├── Uninstall.inc.sh
    │   │   ├── UpdateDC.txt
    │   │   ├── Upgrade.inc.sh
    │   │   ├── upgradeutils
    │   │   ├── upgradeutils70To71
    │   │   ├── upgradeutils71To711
    │   │   └── Utils.inc.sh
    │   ├── manifests.20181107003959
    │   │   ├── extdata
    │   │   │   ├── adminsslconfigs.csv
    │   │   │   ├── common.csv
    │   │   │   ├── dynsettings.csv
    │   │   │   ├── fileupdates.csv
    │   │   │   ├── iamsslconfigs.csv
    │   │   │   ├── s3fs.csv
    │   │   │   └── s3sslconfigs.csv
    │   │   └── site.pp
    │   ├── orig_csvs
    │   │   ├── cloudian-6.2-puppet-csvs.tar.gz
    │   │   ├── cloudian-7.0-puppet-csvs.tar.gz
    │   │   ├── cloudian-7.1.1-puppet-csvs.tar.gz
    │   │   └── cloudian-7.1-puppet-csvs.tar.gz
    │   ├── orig_templates
    │   │   ├── cloudian-6.2.1.1-puppet.tar.gz
    │   │   ├── cloudian-6.2.1-puppet.tar.gz
    │   │   ├── cloudian-6.2.2-puppet.tar.gz
    │   │   ├── cloudian-6.2.3-puppet.tar.gz
    │   │   ├── cloudian-6.2-puppet.tar.gz
    │   │   ├── cloudian-7.0.2-puppet.tar.gz
    │   │   ├── cloudian-7.0-puppet.tar.gz
    │   │   └── cloudian-7.1.1-puppet.tar.gz
    │   ├── preInstallCheck.sh
    │   ├── puppet-manifests-7.1.1.tar.gz
    │   ├── README
    │   ├── RELEASENOTES
    │   ├── sample-survey.csv
    │   ├── selfextract_prereq_el7.bin
    │   ├── survey.csv
    │   ├── system_setup.sh
    │   │   ├── log4j-test.xml
    │   │   ├── preCheck.sh
    │   │   ├── README.txt
    │   │   ├── regions.xml
    │   │   └── run_basictests.sh
    │   ├── token-gen
    │   │   ├── 10.112.2.16.txt
    │   │   ├── 10.112.2.254.txt
    │   │   ├── 10.112.2.55.txt
    │   │   ├── 10.112.2.74.txt
    │   │   ├── 10.112.2.84.txt
    │   │   ├── 10.112.2.9.txt
    │   │   ├── cloudian-token-gen
    │   │   ├── cloudian-token.log
    │   │   ├── conf
    │   │   │   └── log4j-token-gen.xml
    │   │   ├── lib
    │   │   │   ├── apache-cassandra-2.2.9.jar
    │   │   │   ├── cloudian-token-gen-7.1.1.jar
    │   │   │   ├── commons-lang3-3.5.jar
    │   │   │   ├── log4j-api-2.9.1.jar
    │   │   │   ├── log4j-core-2.9.1.jar
    │   │   │   ├── log4j-jcl-2.9.1.jar
    │   │   │   ├── log4j-slf4j-impl-2.9.1.jar
    │   │   │   └── slf4j-api-1.7.21.jar
    │   │   ├── us-east-1-all-tokens.txt
    │   │   └── us-east-2-all-tokens.txt
    │   └── UPGRADE
    ├── cloudian-spots
    │   ├── awscli-bundle
    │   │   ├── install
    │   │   └── packages
    │   │       ├── argparse-1.2.1.tar.gz
    │   │       ├── awscli-1.16.49.tar.gz
    │   │       ├── botocore-1.12.39.tar.gz
    │   │       ├── colorama-0.3.9.tar.gz
    │   │       ├── docutils-0.14.tar.gz
    │   │       ├── futures-3.2.0.tar.gz
    │   │       ├── jmespath-0.9.3.tar.gz
    │   │       ├── ordereddict-1.1.tar.gz
    │   │       ├── pyasn1-0.4.4.tar.gz
    │   │       ├── python-dateutil-2.6.1.tar.gz
    │   │       ├── python-dateutil-2.7.5.tar.gz
    │   │       ├── PyYAML-3.13.tar.gz
    │   │       ├── rsa-3.4.2.tar.gz
    │   │       ├── s3transfer-0.1.13.tar.gz
    │   │       ├── setup
    │   │       │   └── setuptools_scm-1.15.7.tar.gz
    │   │       ├── simplejson-3.3.0.tar.gz
    │   │       ├── six-1.11.0.tar.gz
    │   │       ├── urllib3-1.22.tar.gz
    │   │       ├── urllib3-1.24.1.tar.gz
    │   │       └── virtualenv-15.1.0.tar.gz
    │   ├── awscli-bundle.zip
    │   ├── cfg_cloudian_ports.sh
    │   ├── client_token
    │   ├── config
    │   ├── cosbench
    │   │   ├── archive
    │   │   ├── build.xml
    │   │   ├── conf
    │   │   │   ├── driver.conf
    │   │   │   ├── driver.conf.default
    │   │   │   ├── driver-tomcat-server_1.xml
    │   │   │   ├── driver-tomcat-server.xml
    │   │   │   ├── driver-tomcat-server.xml.default
    │   │   │   ├── filewriter-config-explanation.txt
    │   │   │   ├── hashcheck.xml
    │   │   │   ├── librados-config-sample.xml
    │   │   │   ├── librados-sample-annotated.xml
    │   │   │   ├── model_driver.conf
    │   │   │   ├── model_driver-tomcat-server.xml
    │   │   │   ├── noop-config.xml
    │   │   │   ├── noop-read-config.xml
    │   │   │   ├── noop-write-config.xml
    │   │   │   ├── reusedata.xml
    │   │   │   ├── s3-config-sample.xml
    │   │   │   ├── splitrw.xml
    │   │   │   ├── sproxyd-config-sample.xml
    │   │   │   ├── swift-config-sample.xml
    │   │   │   └── workload-config.xml
    │   │   ├── scripts
    │   │   │   ├── cosbench-start.sh
    │   │   │   ├── cosbench-stop.sh
    │   │   │   ├── start-controller.sh
    │   │   │   └── start-driver.sh
    │   │   ├── start-cosbench.sh
    │   │   ├── start-driver.sh
    │   │   ├── stop-cosbench.sh
    │   │   ├── stop-driver.sh
    │   │   ├── work
    │   │   │   └── Standalone
    │   │   │       ├── _
    │   │   │       │   ├── controller
    │   │   │       │   └── driver
    │   │   │       └── 0.0.0.0
    │   │   │           ├── controller
    │   │   │           └── driver
    │   │   ├── workloads
    │   │   │   └── asus.xml
    │   │   └── workspace
    │   ├── cosbenchcfg.sh
    │   ├── cosbench_numuser
    │   ├── cosbench_ssl
    │   ├── cosbench_wl
    │   ├── cosbench.zip
    │   ├── custom_script
    │   ├── dns
    │   ├── do_install
    │   ├── download_resources.py
    │   ├── driver.conf
    │   ├── enforce_logical
    │   ├── install_binary
    │   ├── install_regions
    │   ├── is_done
    │   ├── leader
    │   ├── leader_election
    │   ├── num_nodes
    │   ├── num_spares
    │   ├── parallel2
    │   ├── parallel4
    │   ├── prepare_setup.py
    │   ├── public_ip
    │   ├── random_domain
    │   ├── run_cosbench
    │   ├── scripts
    │   ├── setup_disks.sh
    │   ├── setup_node.py
    │   ├── setup_ssl.sh
    │   ├── setup_storage_policy.sh
    │   ├── setup_tag
    │   ├── setup_user_group.sh
    │   ├── startup.log
    │   ├── storage_policy
    │   ├── templates
    │   │   ├── group_tpl_6.1.2.json
    │   │   ├── group_tpl.json
    │   │   ├── user_tpl_6.1.2.json
    │   │   └── user_tpl.json
    │   ├── this_az
    │   ├── this_ip
    │   ├── this_region
    │   └── version
    └── CloudianTools
        └── fslist.txt
