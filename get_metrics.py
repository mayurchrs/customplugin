"""
Script to get vThunder instances CPU Usage data on per minute basis and store in a variable
 in automation account.

author: Vikas Gautam
author email: vgautam@a10networks.com
"""

from cgitb import handler
import logging
import os
import requests
import json
# import time
import ast

# from azure.mgmt.compute import ComputeManagementClient
from dotenv import load_dotenv
# from datetime import datetime, timedelta
from azure.mgmt.network import NetworkManagementClient
from azure.identity import DefaultAzureCredential
# from azure.mgmt.automation import AutomationClient

import warnings

warnings.filterwarnings("ignore")


class Authentication:
    @staticmethod
    def get_azure_cred():
        """
        Get azure credential object using service app environment variable.
        :return credential:
        """
        # Acquire a credential object
        token_credential = DefaultAzureCredential()
        return token_credential

    @staticmethod
    def get_vth_auth_token(baseurl):
        """
        Return vthunder instance authentication token for AXAPI.
        :param baseurl:
        :return auth_token:
        """
        payload = json.dumps({
            "credentials": {
                "username": "admin",
                "password": "a10"
            }
        })
        headers = {
            'Content-Type': 'application/json'
        }
        url = baseurl + '/auth'
        try:
            response = requests.request("POST", url, headers=headers, data=payload, verify=False)
            response = response.json()
            auth_token = 'A10 ' + response['authresponse']['signature']
            return auth_token
        except Exception as exp:
            logging.error(exp)
            return None


class GetMetricData:
    @staticmethod
    def get_data_cpu_usage(baseurl, auth_token):
        """
        Get vthunder instance last 1 minute data CPU usage.
        :param baseurl:
        :param auth_token:
        :return:
        """
        url = baseurl + '/system-cpu/ctrl-cpu/oper'
        headers = {
            'Authorization': auth_token
        }
        payload = {}
        try:
            response = requests.request("GET", url, headers=headers, data=payload, verify=False)

            cpu_usage_list = response.json()['ctrl-cpu']['oper']['cpu-usage']

            total_cpu_usage = 0
            for cpu_usage in cpu_usage_list:
                total_cpu_usage += cpu_usage['60-sec']
            return total_cpu_usage / len(cpu_usage_list)

        except Exception as exp:
            logging.error(exp)
            return 0


class VMSSvThunders:
    @staticmethod
    def list_vmss_vthunders_ips(client, resource_group_name, virtual_machine_scale_set_name):
        automation_variable = 'vThunderIP'
        vth_ips = client.public_ip_addresses.list_virtual_machine_scale_set_public_ip_addresses(resource_group_name, virtual_machine_scale_set_name)

        return vth_ips


def handle():
    logging.info('Executing GetMetric function')
    # load env variables
    load_dotenv(".env")
    auth = Authentication()
    # get azure credentials
    credential = auth.get_azure_cred()
    # gat subscription id value
    # subscription_id = os.getenv("SubscriptionId")
    subscription_id = "07d34b9b-61e3-475a-abbc-006b16812a3e"
    resource_group_name = "spatil2_rg_2"
    virtual_machine_scale_set_name = "vthunder-vmss-name"
    # compute_client = ComputeManagementClient(credential=credential, subscription_id=subscription_id)
    network_client = NetworkManagementClient(credential=credential, subscription_id=subscription_id)
    # # get vmss vthunder instances ips
    vmss = VMSSvThunders()
    vth_ips = vmss.list_vmss_vthunders_ips(client=network_client,
                                           resource_group_name=resource_group_name,
                                           virtual_machine_scale_set_name=virtual_machine_scale_set_name)
    list_of_Ips = []
    for i in vth_ips:
        list_of_Ips.append(i.ip_address)

    # print(list_of_Ips)
    # get CPU usage of each vthunder
    vmss_total_cpu_usage = 0
    get_cpu_usage = GetMetricData()
    for ip in list_of_Ips:
        try:
            baseurl = 'https://'+ip+'/axapi/v3'
            auth_token = auth.get_vth_auth_token(baseurl=baseurl)
            cpu_usage = get_cpu_usage.get_data_cpu_usage(baseurl, auth_token)
            vmss_total_cpu_usage += cpu_usage
            # print(vmss_total_cpu_usage)
        except Exception as exp:
            logging.error(exp)

    # get vmss cpu average
    if len(list_of_Ips):
        vmss_avg_cpu_usage = vmss_total_cpu_usage/len(list_of_Ips)
    else:
        vmss_avg_cpu_usage = vmss_total_cpu_usage

    print(vmss_avg_cpu_usage)
    
    
    # print("python execution")
    # with open('/home/azureuser/example.json', 'r+') as f:
    #     data = json.load(f)
    #     data['cpu_usage'] = vmss_avg_cpu_usage
    #     f.seek(0)
    #     json.dump(data, f, indent=4)
    #     f.truncate()

    # print(vmss_avg_cpu_uage)
    # # get current avg cpu
    # last_cpu_usage = automation_client.variable.get(resource_group_name=resource_group_name,
    #                                                 automation_account_name=automation_account,
    #                                                 variable_name=cpu_variable_name)

    # # convert string into json object
    # last_cpu_usage = last_cpu_usage.value
    # last_cpu_usage = json.loads(last_cpu_usage)
    # if isinstance(last_cpu_usage, str):
    #     last_cpu_usage = ast.literal_eval(last_cpu_usage)

    # # delete older than 5 minute avg cpu data from automation account variable
    # for timestamp in list(last_cpu_usage):
    #     date = datetime.fromtimestamp(int(timestamp))
    #     if date < datetime.utcnow()-timedelta(minutes=10):
    #         del last_cpu_usage[timestamp]

    # # insert avg cpu data from automation account variable
    # dtime = datetime.utcnow()
    # unixtime = time.mktime(dtime.timetuple())
    # last_cpu_usage.update({str(int(unixtime)): vmss_avg_cpu_uage})
    # last_cpu_usage = json.dumps(last_cpu_usage)
    # # automation_client.variable.update()
    # automation_client.variable.update(resource_group_name, automation_account, cpu_variable_name,
    #                                     {
    #                                         "name": cpu_variable_name,
    #                                         "value": last_cpu_usage,
    #                                         "description": "last 5 minute cpu usage",
    #                                         "is_encrypted": False
    #                                     }
    #                                     )
    # logging.info('Updated automation account at %s' % datetime.utcnow())


handle()
