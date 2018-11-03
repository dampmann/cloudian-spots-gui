from botocore.client import Config

block_device_mappings = [
    {
      "DeviceName": "/dev/sda1",
      "Ebs": {
        "DeleteOnTermination": True ,
        "VolumeSize": 256
      }
    },
    {
        "DeviceName": "/dev/sdb",
        "VirtualName": "ephemeral0"
    },
    {
        "DeviceName": "/dev/sdc",
        "VirtualName": "ephemeral1"
    },
    {
        "DeviceName": "/dev/sdd",
        "VirtualName": "ephemeral2"
    },
    {
        "DeviceName": "/dev/sde",
        "VirtualName": "ephemeral3"
    },
    {
        "DeviceName": "/dev/sdf",
        "VirtualName": "ephemeral4"
    },
    {
        "DeviceName": "/dev/sdg",
        "VirtualName": "ephemeral5"
    },
    {
        "DeviceName": "/dev/sdh",
        "VirtualName": "ephemeral6"
    },
    {
        "DeviceName": "/dev/sdi",
        "VirtualName": "ephemeral7"
    },
    {
        "DeviceName": "/dev/sdj",
        "VirtualName": "ephemeral8"
    },
    {
        "DeviceName": "/dev/sdk",
        "VirtualName": "ephemeral9"
    },

    {
        "DeviceName": "/dev/sdl",
        "VirtualName": "ephemeral10"
    },

    {
        "DeviceName": "/dev/sdm",
        "VirtualName": "ephemeral11"
    },

    {
        "DeviceName": "/dev/sdn",
        "VirtualName": "ephemeral12"
    },

    {
        "DeviceName": "/dev/sdo",
        "VirtualName": "ephemeral13"
    },

    {
        "DeviceName": "/dev/sdp",
        "VirtualName": "ephemeral14"
    },

    {
        "DeviceName": "/dev/sdq",
        "VirtualName": "ephemeral15"
    },

    {
        "DeviceName": "/dev/sdr",
        "VirtualName": "ephemeral16"
    },

    {
        "DeviceName": "/dev/sds",
        "VirtualName": "ephemeral17"
    },

    {
        "DeviceName": "/dev/sdt",
        "VirtualName": "ephemeral18"
    },

    {
        "DeviceName": "/dev/sdu",
        "VirtualName": "ephemeral19"
    },

    {
        "DeviceName": "/dev/sdv",
        "VirtualName": "ephemeral20"
    },

    {
        "DeviceName": "/dev/sdw",
        "VirtualName": "ephemeral21"
    },
    {
        "DeviceName": "/dev/sdx",
        "VirtualName": "ephemeral22"
    },
    {
        "DeviceName": "/dev/sdy",
        "VirtualName": "ephemeral23"
    }
]

launch_spec = {
    'SecurityGroups':  [],
    'BlockDeviceMappings': block_device_mappings, 
    'ImageId': '',
    'InstanceType': '',
    'KeyName': 'Cloudian-Spots',
    'SpotPrice': '6.0',
    'SubnetId': '',
    'UserData': '',
    'TagSpecifications': []
}

request_config = {
    'AllocationStrategy': 'lowestPrice',
    'IamFleetRole': '',
    'LaunchSpecifications': [],
    'SpotPrice': '6.0',
    'TargetCapacity': 1,
    'TerminateInstancesWithExpiration': True,
    'ReplaceUnhealthyInstances': False,
    'ValidUntil': ''
}

boto_config = Config(connect_timeout=5, retries={'max_attempts': 0})
