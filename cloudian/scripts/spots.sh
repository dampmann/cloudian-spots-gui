#!/bin/bash

/usr/bin/passwd root <<EOF
___SETUP_TAG___
___SETUP_TAG___
EOF
echo "cloudian soft nproc 32768" > /etc/security/limits.d/90-nproc.conf
echo "cloudian hard nproc 32768" >> /etc/security/limits.d/90-nproc.conf
mkdir -p /root/.aws
touch /root/.aws/config
touch /root/.aws/credentials
cat > /root/.aws/config <<EOF
[default]
output = json
region = us-east-2
EOF
cat > /root/.aws/credentials <<EOF
[default]
aws_access_key_id = ___AK___
aws_secret_access_key = ___SK___
region = us-east-2 
EOF
mkdir -p /root/cloudian-spots/scripts
cat > /root/cloudian-spots/config <<EOF
___CONFIG___
EOF
cat > /root/cloudian-spots/download_resources.py <<EOF
import boto3
import os
import stat

def main():
    s = boto3.Session(profile_name='default', region_name='us-east-2')
    s3 = s.resource('s3')
    s3.meta.client.download_file(
            'cloudian-qtspots', 
            'automation/setup_node.py', 
            '/root/cloudian-spots/setup_node.py')
    os.chmod('/root/cloudian-spots/setup_node.py', stat.S_IRWXU)

if __name__ == '__main__':
    main()

EOF
chmod 755 /root/cloudian-spots/download_resources.py
echo -e "$(date) Downloading setup_node.py  \e[1;33m [ PENDING ] \e[0m" >>/root/cloudian-spots/startup.log
cd /root/cloudian-spots/
/usr/local/bin/python3.7 download_resources.py >> /root/cloudian-spots/startup.log
echo -e "$(date) Downloading setup_node.py  \e[1;32m [ DONE ] \e[0m" >>/root/cloudian-spots/startup.log
echo -e "$(date) Executing setup_node.py  \e[1;33m [ PENDING ] \e[0m" >>/root/cloudian-spots/startup.log
cd /root/cloudian-spots/
/usr/local/bin/python3.7 setup_node.py >> /root/cloudian-spots/startup.log
echo -e "$(date) Executing setup_node.py  \e[1;32m [ DONE ] \e[0m" >>/root/cloudian-spots/startup.log

echo "___CLIENT_TOKEN___" > /root/cloudian-spots/client_token
echo "___VERSION___" > /root/cloudian-spots/version
echo "___INSTALL_REGIONS___" > /root/cloudian-spots/install_regions
echo "___SETUP_TAG___" > /root/cloudian-spots/setup_tag
echo "___SETUP_TAG___" > /root/cloudian-spots/random_domain
echo "___LEADER_ELECTION___" > /root/cloudian-spots/leader_election
echo "___NUM_NODES___" > /root/cloudian-spots/num_nodes
echo "___NUM_SPARES___" > /root/cloudian-spots/num_spares
echo "___INSTALL_BINARY___" > /root/cloudian-spots/install_binary
echo "___RUN_COSBENCH___" > /root/cloudian-spots/run_cosbench
echo "___COSBENCH_SSL___" > /root/cloudian-spots/cosbench_ssl
echo "___COSBENCH_WL___" > /root/cloudian-spots/cosbench_wl
echo "___COSBENCH_NUMUSER___" > /root/cloudian-spots/cosbench_numuser
echo "___CUSTOM_SCRIPT___" > /root/cloudian-spots/custom_script
echo "___STORAGE_POLICY___" > /root/cloudian-spots/storage_policy
echo "___DO_INSTALL___" > /root/cloudian-spots/do_install
echo "___ENFORCE_LOGICAL___" > /root/cloudian-spots/enforce_logical

v=___VERSION___
install_regions="___INSTALL_REGIONS___"
elect_leader=___LEADER_ELECTION___
num_nodes=___NUM_NODES___
num_spares=___NUM_SPARES___
setup_tag="___SETUP_TAG___"
install_binary="___INSTALL_BINARY___"
run_cb=___RUN_COSBENCH___
cb_wl="___COSBENCH_WL___"
cb_ssl="___COSBENCH_SSL___"
cb_nu=___COSBENCH_NUMUSER___
custom_script="___CUSTOM_SCRIPT___"
storage_policy="___STORAGE_POLICY___"
enforce_logical="___ENFORCE_LOGICAL___"
do_install="___DO_INSTALL___"

this_region=$(curl http://169.254.169.254/latest/meta-data/placement/availability-zone | sed 's/.$//')
echo $this_region > /root/cloudian-spots/this_region
this_az=$(curl http://169.254.169.254/latest/meta-data/placement/availability-zone)
echo $this_az > /root/cloudian-spots/this_az
ip=$(curl http://169.254.169.254/latest/meta-data/local-ipv4/)
echo $ip > /root/cloudian-spots/this_ip
pip=$(curl http://169.254.169.254/latest/meta-data/public-ipv4/)
echo $pip > /root/cloudian-spots/public_ip
hsuffix1=$(echo $ip | cut -d '.' -f 3)
hsuffix2=$(echo $ip | cut -d '.' -f 4)
hn=$(echo "ch-${this_region}-${this_az}-${hsuffix1}-${hsuffix2}")
lhn=$(curl http://169.254.169.254/latest/meta-data/local-hostname/ | cut -d '.' -f 2-)
echo "$ip ${hn}.${lhn} $hn" >> /etc/hosts
hostname $hn
echo $hn > /etc/hostname
sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/#PermitRootLogin yes/PermitRootLogin yes/' /etc/ssh/sshd_config
if [ $v == 6 ]; then service sshd restart; else systemctl restart sshd.service; fi
cat >> /root/.aws/config <<EOF

[dns]
output = json
region = us-east-2

EOF
cat /root/cloudian-spots/dns >> /root/.aws/credentials
cp -f /root/.ssh/id_rsa.pub /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys
/usr/bin/screen -dmS rpcs -s /usr/local/bin/rpcs
/usr/sbin/ntpdate 0.pool.ntp.org
rc=$(/bin/timeout 180s /root/cloudian-spots/setup_disks.sh)
if ((rc != 0)); then
    echo -e "$(date) setup_disks.sh timed out  \e[1;31m [ FAILED ] \e[0m" >> /root/cloudian-spots/startup.log
fi
touch /root/cloudian-spots/is_done
mkdir -p /root/CloudianPackages
cat > /root/cloudian-spots/driver.conf <<EOF
[driver]
name=driver
url=http://${ip}:18088/driver
EOF
cat > /root/cloudian-spots/cosbenchcfg.sh <<EOF
cd /root/cloudian-spots/
cp -f /root/cloudian-spots/driver.conf /root/cloudian-spots/cosbench/conf/driver.conf
cd /root/cloudian-spots/cosbench
./start-driver.sh
EOF
echo -e "$(date) Root login enabled  \e[1;32m [ OK ] \e[0m" >> /root/cloudian-spots/startup.log
chmod 755 /root/cloudian-spots/cosbenchcfg.sh
mkdir -p /root/CloudianTools/
cd /root/cloudian-spots/
echo -e "$(date) Running prepare_setup.py  \e[1;33m [ PENDING ] \e[0m" >>/root/cloudian-spots/startup.log
/usr/local/bin/python3.7 prepare_setup.py >> /root/cloudian-spots/startup.log
if [ $? -ne 0 ]; then
    echo -e "$(date) prepare_setup.py  \e[1;31m [ FAILED ] \e[0m" >> /root/cloudian-spots/startup.log
else
    echo -e "$(date) prepare_setup.py finished  \e[1;32m [ OK ] \e[0m" >> /root/cloudian-spots/startup.log
    cd /root/cloudian-spots/
    leader=$(cat /root/cloudian-spots/leader)
    if [ "$leader" == "$ip" ]; then
        echo -e "$(date) Waiting for all nodes to finish disk setups  \e[1;33m [ PENDING ] \e[0m" >>/root/cloudian-spots/startup.log
        echo "Waiting max 2 minutes for disk setups to finish." >> /root/cloudian-spots/startup.log
        attempts=0
        disks_done=0
        expected=$(cat /root/CloudianPackages/survey.csv | wc -l)
        echo "Expecting ${expected} hosts to finish setting up disks." >> /root/cloudian-spots/startup.log
        while true
        do
            disks_done=0
            for i in $(cat /root/CloudianPackages/survey.csv | awk -F, '{print $3}')
            do
                echo "Disks done ${disks_done}" >> /root/cloudian-spots/startup.log
                echo "Checking ${i}" >> /root/cloudian-spots/startup.log
                disks_done=$(/usr/local/bin/all sh -c "test -f /root/cloudian-spots/is_done && echo ok" | grep -c "ok")
                echo "Disks done ${disks_done}" >> /root/cloudian-spots/startup.log
            done
                if ((disks_done == expected)); then
                    echo -e "$(date) Disk setup finished  \e[1;32m [ OK ] \e[0m" >> /root/cloudian-spots/startup.log
                    break
                else
                    echo "expected ${expected} done ${disks_done} attempts ${attempts}." >> /root/cloudian-spots/startup.log
                    ((attempts++))
                    sleep 1
                fi

                if ((attempts > 120)); then
                    echo -e "$(date) Disk setup timed out  \e[1;31m [ FAILED ] \e[0m" >> /root/cloudian-spots/startup.log
                    exit 1 
                fi

        done
        if ((enforce_logical == 1)); then
            for i in $(cat /root/CloudianPackages/survey.csv) 
            do 
                iip=$(echo $i | awk -F, '{print $3}') 
                hn=$(echo $i | awk -F, '{print $2}') 
                ssh -o StrictHostKeyChecking=no $iip hostname $hn 
            done
        fi
        if ((do_install == 1)); then
            echo -e "$(date) Configuring cloudian ports  \e[1;33m [ PENDING ] \e[0m" >>/root/cloudian-spots/startup.log
            ./cfg_cloudian_ports.sh
            echo -e "$(date) Configuring cloudian ports  \e[1;32m [ OK ] \e[0m" >> /root/cloudian-spots/startup.log
            echo -e "$(date) Unpacking cloudian bin file  \e[1;33m [ PENDING ] \e[0m" >>/root/cloudian-spots/startup.log
            echo "Unpacking cloudian software" >> /root/cloudian-spots/startup.log
            cd /root/CloudianPackages/
            /bin/sh ./CloudianHyper*.bin ./cloudian_12345.lic >> /root/cloudian-spots/startup.log
            echo -e "$(date) Unpacking cloudian bin file  \e[1;32m [ OK ] \e[0m" >> /root/cloudian-spots/startup.log
            sed -i 's/cloudian.s3.max_user_buckets=<%= @cloudian_s3_max_user_buckets %>/cloudian.s3.max_user_buckets=1000/' /etc/cloudian-*-puppet/modules/cloudians3/templates/mts.properties.erb
            sed -i 's/cloudian_s3_max_user_buckets,100/cloudian_s3_max_user_buckets,1000/' /etc/cloudian-*-puppet/manifests/extdata/dynsettings.csv
            echo -e "$(date) Starting cloudian installation  \e[1;33m [ PENDING ] \e[0m" >>/root/cloudian-spots/startup.log
            ./cloudianInstall.sh -b -s survey.csv -k /root/.ssh/id_rsa force configure-dnsmasq >> /root/cloudian-spots/startup.log
            echo -e "$(date) Cloudian installation  \e[1;32m [ OK ] \e[0m" >> /root/cloudian-spots/startup.log
            echo -e "$(date) Setting up users and groups  \e[1;33m [ PENDING ] \e[0m" >>/root/cloudian-spots/startup.log
            /root/cloudian-spots/setup_user_group.sh
            echo -e "$(date) Setting up users and groups  \e[1;32m [ DONE ] \e[0m" >>/root/cloudian-spots/startup.log
            echo -e "$(date) Setting up SSL  \e[1;33m [ PENDING ] \e[0m" >>/root/cloudian-spots/startup.log
            /root/cloudian-spots/setup_ssl.sh
            echo -e "$(date) Setting up SSL  \e[1;32m [ DONE ] \e[0m" >>/root/cloudian-spots/startup.log
            echo -e "$(date) Setting up storage policy  \e[1;33m [ PENDING ] \e[0m" >>/root/cloudian-spots/startup.log
            /root/cloudian-spots/setup_storage_policy.sh
            echo -e "$(date) Setting up storage policy  \e[1;32m [ DONE ] \e[0m" >>/root/cloudian-spots/startup.log
            cd /root/cloudian-spots/
            if [ -e cosbench.zip ]; then
                echo -e "$(date) Unpacking cosbench  \e[1;33m [ PENDING ] \e[0m" >>/root/cloudian-spots/startup.log
                unzip cosbench.zip
                echo -e "$(date) Unpacking cosbench  \e[1;32m [ DONE ] \e[0m" >>/root/cloudian-spots/startup.log
                cp -f controller.conf cosbench/conf/
                cp -f driver.conf cosbench/conf/
                cd /root/cloudian-spots/cosbench
                echo -e "$(date) Starting cosbench  \e[1;33m [ PENDING ] \e[0m" >>/root/cloudian-spots/startup.log
                ./start-cosbench.sh >>/root/cloudian-spots/startup.log
                cd /root/cloudian-spots/
                if [ $cb_wl != "None" ]; then
                    ak=$(cat /root/cloudian-spots/ak)
                    sk=$(cat /root/cloudian-spots/sk)
                    sed -i "s:__AK__:$ak:" /root/cloudian-spots/workload.xml
                    sed -i "s:__SK__:$sk:" /root/cloudian-spots/workload.xml
                    ep=""
                    if ((cb_ssl == 1)); then
                        ep=$(echo "https://s3.${setup_tag}.cloudian-spots.com")
                    else
                        ep=$(echo "http://s3.${setup_tag}.cloudian-spots.com")
                    fi
                    sed -i "s:__IP__:$ep:" /root/cloudian-spots/workload.xml
                    echo "${this_ip} s3.${setup_tag}.cloudian-spots.com" >> /etc/hosts
                    echo "${this_ip} s3-admin.${setup_tag}.cloudian-spots.com" >> /etc/hosts
                    echo -e "$(date) submitting workload  \e[1;33m [ PENDING ] \e[0m" >>/root/cloudian-spots/startup.log
                    curl "http://cosbench.${setup_tag}.cloudian-spots.com:19088/controller/cli/submit.action?username=anonymous&password=cosbench" -F "config=@/root/cloudian-spots/workload.xml" >> /root/cloudian-spots/startup.log
                    echo -e "$(date) submitting workload  \e[1;32m [ DONE ] \e[0m" >>/root/cloudian-spots/startup.log
                fi
                echo -e "$(date) Starting cosbench  \e[1;32m [ DONE ] \e[0m" >>/root/cloudian-spots/startup.log
            fi
        else
            echo -e "$(date) No install selected  \e[1;32m [ CONTINUE ] \e[0m" >>/root/cloudian-spots/startup.log
        fi
        if [ $custom_script != "None" ]; then
            echo -e "$(date) Starting ${custom_script}  \e[1;33m [ PENDING ] \e[0m" >>/root/cloudian-spots/startup.log
            chmod 755 /root/cloudian-spots/scripts/${custom_script}
            /root/cloudian-spots/scripts/${custom_script}
            echo -e "$(date) ${custom_script}  \e[1;32m [ DONE ] \e[0m" >>/root/cloudian-spots/startup.log
        fi
    else
        cd /root/cloudian-spots/
        if [ -e cosbench.zip ]; then
            echo -e "$(date) Unpacking cosbench  \e[1;33m [ PENDING ] \e[0m" >>/root/cloudian-spots/startup.log
            unzip cosbench.zip
            echo -e "$(date) Unpacking cosbench  \e[1;32m [ DONE ] \e[0m" >>/root/cloudian-spots/startup.log
            ./cosbenchcfg.sh >>/root/cloudian-spots/startup.log
        fi
        echo "Not the master node, done." >> /root/cloudian-spots/startup.log
    fi
fi

echo -e "$(date) Downloading aws cli  \e[1;33m [ PENDING ] \e[0m" >>/root/cloudian-spots/startup.log
curl "https://s3.amazonaws.com/aws-cli/awscli-bundle.zip" -o "/root/cloudian-spots/awscli-bundle.zip"
echo -e "$(date) Download finished  \e[1;32m [ OK ] \e[0m" >> /root/cloudian-spots/startup.log
cd /root/cloudian-spots/
unzip awscli-bundle.zip
rm -f /usr/local/bin/aws
echo -e "$(date) Installing  aws cli  \e[1;33m [ PENDING ] \e[0m" >>/root/cloudian-spots/startup.log
/usr/local/bin/python3.7 /root/cloudian-spots/awscli-bundle/install -i /usr/local/aws -b /usr/local/bin/aws
echo -e "$(date) Install finished  \e[1;32m [ OK ] \e[0m" >> /root/cloudian-spots/startup.log
#spotfleets
