# Copyright 2015 TellApart, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Base class and other utility methods for registration in Azure.
"""

__copyright__ = 'Copyright (C) 2015 TellApart, Inc. All Rights Reserved.'

import azure.mgmt
import azure.mgmt.compute
import azure.profiles
import requests
import re

from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from msrestazure.azure_active_directory import ServicePrincipalCredentials
from tellapart.aurproxy.register.base import BaseRegisterer

_CONN_MGR = None
# These are configured based on the latest version at the time. Changing these may cause some breaking changes.
_AZURE_API_COMPUTE_VERSION = '2018-04-01'
_AZURE_API_NETWORK_VERSION = '2018-02-01'
# for more information on the Azure metadata service, see: https://docs.microsoft.com/en-us/azure/virtual-machines/windows/instance-metadata-service
_AZURE_METADATA_URI = 'http://169.254.169.254/metadata/instance/{0}?api-version=2017-08-01&format=text'


class AzureRegisterer(BaseRegisterer):
  """
    Common code for Azure Registerers.
  """
  def __init__(self, region, subscription_id, tenant_id, client_id, client_secret):
    """
    Args:
      region - str - Azure region name (EG: 'westcentralus','westus','eastus').
      subscription_id - str - Azure subscription ID (as GUID).
      tenant_id - str - Azure tenant ID (as GUID).
      client_id - str - Azure client (application) ID (as GUID).
      client_secret - str - Azure client secret key.
    """
    self._region = region
    self._subscription_id = subscription_id
    self._tenant_id = tenant_id
    self._client_id = client_id
    self._client_secret = client_secret

  @property
  def conn(self):
    """
    Manages access to global AzureConnectionManager.

    Returns:
      AzureConnectionManager
    """
    global _CONN_MGR
    if not _CONN_MGR:
      _CONN_MGR = AzureConnectionManager(self._region,
                                        self._subscription_id,
                                        self._tenant_id,
                                        self._client_id,
                                        self._client_secret)
    return _CONN_MGR

  def get_current_instance_id(self):
    """Retrieves the Azure instance id of the current machine.

    Returns:
      The VM ID (as GUID).
    """
    return self._get_instance_metadata('compute/vmId')

  def get_current_machine(self):
    """Retrieves the Azure virtual machine object of the current machine.
    """
    vm_id = self.get_current_instance_id()
    return self.get_virtual_machine(vm_id)

  def get_virtual_machine(self, vm_id):
    """Retrieves the Azure instance id of the current machine.

    Returns:
      The VirtualMachine object (as azure.mgmt.compute.v2017_03_30.models.VirtualMachine)
    """
    vm_list = self.get_all_virtual_machines()
    vm_list = [vm for vm in vm_list if vm.vm_id == vm_id]
    if not vm_list or len(vm_list) == 0: return None
    return vm_list[0]

  def get_all_virtual_machines(self):
    """Retrieves all of the Azure virtual machine in the subscription.

    Returns:
      A list of VirtualMachine objects (as azure.mgmt.compute.v2017_03_30.models.VirtualMachine)
    """
    vm_paged = self.conn.compute.virtual_machines.list_all()
    vm_list = [v for v in vm_paged]
    return vm_list

  def get_network_interface(self, nic_id):
    """Retrieves the Azure network interface object for the specified nic_id.

    Args:
      nic_id - str - Azure nic_id (i.e.: '/subscriptions/abcd1234-1234-0000-0000-c754cb241ea4/resourceGroups/ResourceGroup1/providers/Microsoft.Network/networkInterfaces/nic_1')

    Returns:
      The NetworkInterface object (as azure.mgmt.network.v2018_02_01.models.NetworkInterface)
    """
    client = self.conn.network
    nic_paged = client.network_interfaces.list_all()
    nic_list = [n for n in nic_paged if n.id == nic_id]
    if not nic_list or len(nic_list) == 0: return None
    return nic_list[0]

  def save_network_interface(self, nic):
    """Saves the Azure network interface object.

    Args:
      nic - azure.mgmt.network.v2018_02_01.models.NetworkInterface - Azure network interface object

    Returns:
        Bool whether save was successful
    """
    if not nic: return False
    path_info = self._extract_path_info_from_id(nic.id)
    res_group = path_info['resource_group']
    if not res_group: return False
    # save the network interface
    client = self.conn.network
    # print(f'create_or_update(resource_group: {res_group}, name: {nic.name})')
    client.network_interfaces.create_or_update(resource_group_name=res_group, network_interface_name=nic.name, parameters=nic)

    return True

  def get_load_balancer(self, lb_name):
    """
      Gets the specific load balancer by name.

    Returns:
      The LoadBalancer object (as azure.mgmt.network.v2018_02_01.models.LoadBalancer )
    """
    client = self.conn.network
    lb_paged = client.load_balancers.list_all()
    # iterate all paged items into a single list
    lb_list = [lb for lb in lb_paged if lb.name == lb_name]
    if len(lb_list) == 0: return None
    return lb_list[0]

  def _get_instance_metadata(self, identifier):
    """Gets a specific piece of instance metadata for the current Azure instance.

    Args:
      identifier - The identifier of the metadata.
      Examples: 'compute/location', 'compute/name', 'ipv4/privateIpAddress'

    Returns:
      The value corresponding to identifier.
    """
    global _AZURE_METADATA_URI
    url = _AZURE_METADATA_URI
    session = requests.Session()
    session.trust_env = False  # Ignore http_proxy setting for this
    session.headers.update({'Metadata': 'true'}) # required by Azure metadata service
    return session.get(url, timeout=2).content

  def _extract_path_info_from_id(self, id):
    """Given a common Azure object id, extracts the subscription_id and resource_group.

    Args:
      id - str - The ID of the Azure object
      Examples: '/subscriptions/abcd1234-7b0a-b558-4c0c-c754cb241ea4/resourceGroups/ResourceGroup1'

    Returns:
      The value corresponding to identifier.
    """
    pattern = r'/subscriptions/([^/]+)/resourceGroups/([^/]+)(/|$)'
    match = re.search(pattern, id)
    groups = match.groups()
    result = { 'subscription_id': None, 'resource_group': None }
    if len(groups) > 2:
        result['subscription_id'] = groups[0]
        result['resource_group'] = groups[1]
    return result


class AzureConnectionManager(object):
  """Connection manager for Azure.
  """
  def __init__(self, region, subscription_id, tenant_id, client_id, client_secret):
    """
    Args:
      region - str - Azure region string.
      subscription_id - str - Subscription credentials which uniquely identify Microsoft Azure subscription. The subscription ID forms part of the URI for every service call.
      tenant_id - str - TBD
      client_id - str - TBD
      client_secret - str - TBD
    """
    self._region = region
    self._subscription_id = subscription_id
    self._tenant_id = tenant_id
    self._client_id = client_id
    self._client_secret = client_secret

  def _make_credentials(self):
    """
    Creates and returns a Azure credential object.

    Returns:
      A Azure credential object.
    """
    return ServicePrincipalCredentials(
            client_id=self._client_id,
            secret=self._client_secret,
            tenant=self._tenant_id
        )

  @property
  def compute(self):
    """
    An Azure compute client.
    """
    if not getattr(self, '_compute_client', None):
      credentials = self._make_credentials()
      self._compute_client = ComputeManagementClient(credentials, self._subscription_id, _AZURE_API_COMPUTE_VERSION)
    return self._compute_client

  @property
  def network(self):
    """
    An Azure Network connection, for load balancing and DNS management.
    """
    if not getattr(self, '_network_client', None):
      credentials = self._make_credentials()
      self._network_client = NetworkManagementClient(credentials, self._subscription_id, _AZURE_API_NETWORK_VERSION)
    return self._network_client

