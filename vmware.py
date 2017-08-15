#/usr/bin/env python

"""
Written by Paulo Mariano
Github: https://github.com/paulomariano77
Email: pazevedo@stone.com.br

This Script convert a Vitrual Machina to a Template and vice versa
"""

import atexit
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vmodl
from pyVmomi import vim
import argparse
import getpass
import ssl
import os

try:
    import json
except ImportError:
    import simplejson as json


def get_args():
    parser = argparse.ArgumentParser(description='Arguments for talking to vCenter')
    parser.add_argument('-s', '--host',
                        required=True,
                        action='store',
                        help='vCenter host to connect to')

    parser.add_argument('-o', '--port',
                        default=443,
                        type=int,
                        action='store',
                        help='Port to connect on vCenter')

    parser.add_argument('-u', '--username',
                        required=True,
                        action='store',
                        help='User name to connect on vCenter')

    parser.add_argument('-p', '--password',
                        required=False,
                        action='store',
                        help='User password to connect on vCenter')
    
    args = parser.parse_args()

    if not args.password:
        args.password = getpass.getpass(prompt='Enter your password: ')
    
    return args

def open_connection(host, user, passowrd, port):
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    ssl_context.verify_mode = ssl.CERT_NONE

    connection = SmartConnect(host=host, user=user, pwd=passowrd, port=port, sslContext=ssl_context)
    print 'Connected to vCenter...'
    return connection


def close_connection(connection):
    atexit.register(Disconnect, connection)
    print 'Desconnected of vCenter...'


def get_obj(content, vimtype):
    containers = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    obj = containers.view
    return obj


def grouplist(si):
    inventory = {}
    inventory['local'] = ['127.0.0.1']
    content = si.RetrieveContent()
    virtual_machines = get_obj(content, [vim.VirtualMachine])

    for child in content.rootFolder.childEntity:
        if hasattr(child, 'vmFolder'):
            datacenter = child
            vmFolder = datacenter.vmFolder
            print datacenter.vmFolder
            vmList = vmFolder.childEntity
            for folder in vmFolder.childEntity:
                print 'Folder: ', folder.childType
    # print json.dumps(inventory, indent=4)aa


def main():
    args = get_args()
    service_instance = open_connection(args.host, args.username, args.password, args.port)
    grouplist(service_instance)


if __name__ == '__main__':
    main()

