#!/usr/bin/env python

"""
Written by Paulo Mariano
Github: https://github.com/paulomariano77
Email: pazevedo@stone.com.br

This script generates a ansible dynamic inventory for VMWare vCenter
"""

import atexit
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vmodl
from pyVmomi import vim
import argparse
import getpass
import ssl
import os
from terminaltables import SingleTable
import re

try:
    import json
except ImportError:
    import simplejson as json


def get_args():
    parser = argparse.ArgumentParser(description='Arguments for talking to vCenter')
    parser.add_argument('-s', '--host',
                        default=os.environ.get('VMWARE_VCENTER_HOST', None),
                        action='store',
                        help='vCenter host to connect to')

    parser.add_argument('-o', '--port',
                        default=443,
                        type=int,
                        action='store',
                        help='Port to connect on vCenter')

    parser.add_argument('-u', '--username',
                        default=os.environ.get('VMWARE_VCENTER_USER', None),
                        action='store',
                        help='User name to connect on vCenter')

    parser.add_argument('-p', '--password',
                        required=False,
                        default=os.environ.get('VMWARE_VCENTER_PASSWORD'),
                        action='store',
                        help='User password to connect on vCenter')
    
    parser.add_argument('--debug',
                        default=False,
                        action='store_true',
                        help='show debug info')

    parser.add_argument('--list',
                        default=True,
                        action='store_true',
                        help='List instances (default: True)')
    
    args = parser.parse_args()

    if not args.password:
        args.password = getpass.getpass(prompt='Enter your password: ')
    
    return args

def open_connection(args):
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    ssl_context.verify_mode = ssl.CERT_NONE

    connection = SmartConnect(host=args.host, user=args.username, pwd=args.password, port=args.port, sslContext=ssl_context)
    
    if args.debug:
        print 'Connected to vCenter...'
    
    return connection


def close_connection(connection, args):
    atexit.register(Disconnect, connection)
    
    if args.debug:
        print 'Desconnected of vCenter...'


def get_obj(content, vimtype):
    containers = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    obj = containers.view
    return obj


def print_vm_info(summary_vm):
    table_data = []
    table_data.append(['VM Name:', summary_vm.config.name])
    table_data.append(['IP Address:', summary_vm.guest.ipAddress])
    table_data.append(['Annotation:', summary_vm.config.annotation])
    table = SingleTable(table_data)
    table.inner_row_border = True
    print table.table


def create_inventory(summary_vm, inventory):
    tags = re.findall(r'#(\w+)', summary_vm.config.annotation)
    for tag in tags:
        if tag in inventory:
            vm_hosts = inventory[tag].get('hosts')
            vm_hosts.append(summary_vm.config.name)
            inventory[tag]['hosts'] = vm_hosts
        else:
            inventory[tag] = {}
            inventory[tag]['hosts'] = [summary_vm.config.name]
        
        inventory['_meta']['hostvars'][summary_vm.config.name] = { "ansible_host": summary_vm.guest.ipAddress }


def main():
    inventory = {}
    inventory['_meta'] = {}
    inventory['_meta']['hostvars'] = {}
    inventory['local'] = ['127.0.0.1']

    args = get_args()

    if args.list:
        service_instance = open_connection(args)
        content = service_instance.RetrieveContent()
        virtual_machines = get_obj(content, [vim.VirtualMachine])
        close_connection(service_instance, args)

        for vm in virtual_machines:
            summary_vm = vm.summary
            if ((not summary_vm.config.template) and (summary_vm.config.annotation != "") and 
                (summary_vm.runtime.powerState == "poweredOn") and (summary_vm.guest.ipAddress is not None)):
                    
                    if args.debug:
                        print_vm_info(summary_vm)
                    
                    create_inventory(summary_vm, inventory)
        
                

    print json.dumps(inventory, indent=4)


if __name__ == '__main__':
    main()

