#!/usr/bin/env python3

import json
import sys
import os

IPs = []
hostnames = []


with open('terraform.tfstate') as json_file:
    data = json.load(json_file)
    for res in data['resources']:
        if res['name'] == 'vm_instance':
            for vm in res['instances']:
                hostnames.append(vm['attributes']['name'])
                for nic in vm['attributes']['network_interface']:
                    if nic['name'] == 'nic0':
                        print("{} (IP: {})".format(vm['attributes']['name'], nic['access_config'][0]['nat_ip']))
                        IPs.append(nic['access_config'][0]['nat_ip'])



with open('hosts', 'w') as host_file:
    host_file.write('[master]\n')
    host_file.write(IPs[0]+'\n')
    host_file.write('\n')

    host_file.write('[workers]\n')
    for IP in IPs[1:4]:
        host_file.write(IP+'\n')
    host_file.write('\n')

    host_file.write('[driver]\n')
    host_file.write(IPs[4]+'\n')
    host_file.write('\n')

    host_file.write('[kafka]\n')
    host_file.write(IPs[5]+'\n')
    host_file.write('\n')

    host_file.write('[ssh_clients]\n')
    for IP in IPs[0:4]:
        host_file.write(IP+'\n')
    host_file.write('\n')

    host_file.write('[spark_machines]\n')
    for IP in IPs[0:5]:
        host_file.write(IP+'\n')
    host_file.write('\n')

    host_file.write('[all:vars]\n')
    host_file.write('ansible_ssh_user={}\n'.format(os.environ['GCP_userID']))
    host_file.write('ansible_ssh_private_key_file={}\n'.format(os.environ['GCP_privateKeyFile']))
    host_file.write('ansible_ssh_common_args=\'-o StrictHostKeyChecking=no\'\n')
