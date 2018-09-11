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

"""Registration implementation for Azure Load Balancers.
"""

__copyright__ = 'Copyright (C) 2015 TellApart, Inc. All Rights Reserved.'

from tellapart.aurproxy.register.azuretools import AzureRegisterer
from tellapart.aurproxy.register.base import (
    RegistrationAction,
    RegistrationActionReason
)
from tellapart.aurproxy.util import get_logger

logger = get_logger(__name__)

class AzureException(BaseException): pass

class BaseAzureLbRegisterer(AzureRegisterer):
  def __init__(self, lb_names, region, subscription_id, tenant_id, client_id=None, client_secret=None):
    """
    Common code for Azure load balancer Registerers.

    Args:
      lb_names - str - Comma-delimited list of ELB names.
      region - str - Azure region name (EG: 'westcentralus','westus','eastus').
      subscription_id - str - Azure subscription ID (as GUID).
      tenant_id - str - Azure tenant ID (as GUID).
      client_id - str - Azure client (application) ID (as GUID).
      client_secret - str - Azure client secret key.
    """
    super(BaseAzureLbRegisterer, self).__init__(
        region, subscription_id, tenant_id, client_id, client_secret)
    self._lb_names = lb_names.split(',')

  @property
  def lbs(self):
    """
    Retrieves specified Azure LoadBalancer instances.

    Returns:
      List of LoadBalancers objects (azure.mgmt.network.models.LoadBalancer) matching the list of names this class was instantiated with.
    """
    lbs_iter = self.conn.network.load_balancers.list_all()
    # iterates all paged items into a single list, filtering on current lb names
    lb_list = [b for b in lbs_iter if b.name in self._lb_names]
    return lb_list

  def match_load_balancer_and_vm(self, lb, vm):
    """
    Given a load balancer and a VM, builds a dict of matched objects.
    Properties: load_balancer, vm, network_interface, backend_pool, ip_config
    """
    if not lb:
        return None
    if not vm:
        return None
    for nf in vm.network_profile.network_interfaces:
        nic = self.get_network_interface(nf.id)
        bp_item = self._match_backend_pool(lb, nic)
        if bp_item:
            bp_item['network_interface'] = nic
            bp_item['vm'] = vm
            bp_item['load_balancer'] = lb
            return bp_item
    return None

  def add_vm_to_load_balancer(self, lb, vm, backend_pool=None):
    """
    Adds the VM to the load balancer.

    Args:
      lb - azure.mgmt.network.v2018_02_01.models.LoadBalancer - LoadBalancer object
      vm - azure.mgmt.compute.v2017_03_30.models.VirtualMachine - VirtualMachine object
      backend_pool - str - The name of the backend pool within the load balancer to add the VM. If not specified, the first pool will be chosen.

    Returns:
      Bool whether add was successful
    """
    # cannot add VM if load balancer doesn't exist or has no backend pools
    if not lb or not lb.backend_address_pools or len(lb.backend_address_pools) == 0:
        logger.warn('no lb backend pools to register with!')
        return False
    if not vm:
        logger.warn('no vm to register!')
        return False
    bp = self._find_backend_pool(lb, None)
    match = self._match_ip_config(vm)
    if not match or not bp:
        logger.warn('failed to find nic without pooling ip config for this vm!')
        return False
    match['ip_config'].load_balancer_backend_address_pools = [bp]
    nic = match['network_interface']

    return self.save_network_interface(nic)

  def remove_vm_from_load_balancer(self, lb, vm):
    """
    Removes the VM from the load balancer.

    Args:
      lb - azure.mgmt.network.v2018_02_01.models.LoadBalancer - LoadBalancer object
      vm - azure.mgmt.compute.v2017_03_30.models.VirtualMachine - VirtualMachine object

    Returns:
      Bool whether remove was successful
    """
    match = self.match_load_balancer_and_vm(lb, vm)
    if not match: return False
    # remove the link between the VM's IP config object and the corresponding load balancer backend pool
    nic = match['network_interface']
    match['ip_config'].load_balancer_backend_address_pools = None

    return self.save_network_interface(nic)

  def _match_backend_pool(self, lb, nic):
    """
    Given a load balancer and a network interface, attempts to find a match on backend pool and ip config.
    """
    for ip in nic.ip_configurations:
      # if ip.load_balancer_backend_address_pools:
      for bp in (ip.load_balancer_backend_address_pools or []):
        for lbp in lb.backend_address_pools:
          if (lbp.id == bp.id):
            return {'backend_pool': bp, 'ip_config': ip}
    return None

  def _find_backend_pool(self, lb, bp_name):
    """
    Given a load balancer, attempts to find the backend pool, and if not found, returns the first backend pool.
    """
    if not lb or not lb.backend_address_pools or len(lb.backend_address_pools) == 0:
      return None
    bp_list = [b for b in lb.backend_address_pools if b.name == bp_name]
    if len(bp_list) > 0:
      return bp_list[0]
    else:
      return lb.backend_address_pools[0]

  def _match_ip_config(self, vm):
    """
    Finds the ip config object within the network interface to associate the backend pool for the VM.
    """
    for nf in vm.network_profile.network_interfaces:
      nic = self.get_network_interface(nf.id)
      if nic.primary:
        return {'network_interface': nic, 'ip_config': next(iter(nic.ip_configurations))}
    return None


class AzureLbSelfRegisterer(BaseAzureLbRegisterer):
  """
  Registerer that adds and removes current machine from configured ELBs.
  """

  def add(self):
    """
    Add the current instance to all configured LBs.
    Assumes that this code is running on an Azure instance.
    """
    instance_id = self.get_current_instance_id()
    vm = self.get_current_machine()
    for lb in self.lbs:
      # Note: This only finds the VM in one of the balancer's backend pools
      match = self.match_load_balancer_and_vm(lb, vm)
      if not match:
        self.record(lb.name,
                    instance_id,
                    RegistrationAction.REGISTER,
                    [RegistrationActionReason.NOT_YET_REGISTERED])
        if not self.add_vm_to_load_balancer(lb, vm):
            raise AzureException("failed to register vm {} with lb {}".format(vm, lb))
        else:
            logger.info("registered vm {} with lb {}".format(vm, lb))
      else:
        self.record(lb.name,
                    instance_id,
                    RegistrationAction.NONE,
                    [RegistrationActionReason.ALREADY_REGISTERED])

  def remove(self):
    """
    Remove the current instance from all configured LBs.
    Assumes that this code is running on an Azure instance.
    """
    instance_id = self.get_current_instance_id()
    vm = self.get_current_machine()
    for lb in self.lbs:
      match = self.match_load_balancer_and_vm(lb, vm)
      #if instance_id in self._get_elb_instance_ids(elb):
      if match:
        self.record(lb.name,
                    instance_id,
                    RegistrationAction.REMOVE)
        self.remove_vm_from_load_balancer(lb, vm)
      else:
        self.record(lb.name,
                    instance_id,
                    RegistrationAction.NONE,
                    [RegistrationActionReason.NOT_ALREADY_REGISTERED])


# TODO refactor with less spite
class AzureGatewaySelfRegisterer(AzureRegisterer):
  def __init__(self, lb_names, region, subscription_id, tenant_id, client_id=None, client_secret=None):
    """
    Common code for Azure application gateway Registerers.

    Args:
      lb_names - str - Comma-delimited list of ELB names.
      region - str - Azure region name (EG: 'westcentralus','westus','eastus').
      subscription_id - str - Azure subscription ID (as GUID).
      tenant_id - str - Azure tenant ID (as GUID).
      client_id - str - Azure client (application) ID (as GUID).
      client_secret - str - Azure client secret key.

    Note: client id must be authorized to read/list Network resources as well as Virtual Machine
    Resources. Giving this prinicipal "Virtual Machine Contributor" and "Network Contributor" role
    assignments is suitable.

    """
    super(AzureGatewaySelfRegisterer, self).__init__(
        region, subscription_id, tenant_id, client_id, client_secret)
    self._lb_names = lb_names.split(',')

  @property
  def lbs(self):
    """
    Retrieves specified Azure ApplicationGateway instances.

    Returns:
      List of LoadBalancers objects (azure.mgmt.network.models.LoadBalancer) matching the list of names this class was instantiated with.
    """
    lbs_iter = self.conn.network.application_gateways.list_all()
    # iterates all paged items into a single list, filtering on current lb names
    lb_list = [b for b in lbs_iter if b.name in self._lb_names]
    return lb_list

  def match_load_balancer_and_vm(self, lb, vm):
    """
    Given a load balancer and a VM, builds a dict of matched objects.
    Properties: load_balancer, vm, network_interface, backend_pool, ip_config
    """
    if not lb:
        return None
    if not vm:
        return None
    for nf in vm.network_profile.network_interfaces:
        nic = self.get_network_interface(nf.id)
        bp_item = self._match_backend_pool(lb, nic)
        if bp_item:
            bp_item['network_interface'] = nic
            bp_item['vm'] = vm
            bp_item['load_balancer'] = lb
            return bp_item
    return None

  def add_vm_to_load_balancer(self, lb, vm, backend_pool=None):
    """
    Adds the VM to the load balancer (gateway).

    Args:
      lb - azure.mgmt.network.v2018_02_01.models.ApplicationGateway - ApplicationGateway object
      vm - azure.mgmt.compute.v2017_03_30.models.VirtualMachine - VirtualMachine object
      backend_pool - str - The name of the backend pool within the load balancer to add the VM. If not specified, the first pool will be chosen.

    Returns:
      Bool whether add was successful
    """
    # cannot add VM if load balancer doesn't exist or has no backend pools

    if not lb or not lb.backend_address_pools or len(lb.backend_address_pools) == 0:
        logger.warn('no lb backend pools to register with!')
        return False
    if not vm:
        logger.warn('no vm to register!')
        return False
    bp = self._find_backend_pool(lb, None)
    match = self._match_ip_config(vm)
    if not match or not bp:
        logger.warn('failed to find nic without pooling ip config for this vm!')
        return False

    match['ip_config'].application_gateway_backend_address_pools = [bp]
    nic = match['network_interface']

    return self.save_network_interface(nic)

  def remove_vm_from_load_balancer(self, lb, vm):
    """
    Removes the VM from the load balancer.

    Args:
      lb - azure.mgmt.network.v2018_02_01.models.ApplicationGateway - ApplicationGateway object
      vm - azure.mgmt.compute.v2017_03_30.models.VirtualMachine - VirtualMachine object

    Returns:
      Bool whether remove was successful
    """
    match = self.match_load_balancer_and_vm(lb, vm)
    if not match: return False
    # remove the link between the VM's IP config object and the corresponding load balancer backend pool
    nic = match['network_interface']
    match['ip_config'].application_gateway_backend_address_pools = None

    return self.save_network_interface(nic)

  def _match_backend_pool(self, lb, nic):
    """
    Given a load balancer and a network interface, attempts to find a match on backend pool and ip config.
    """
    for ip in nic.ip_configurations:
      # if ip.load_balancer_backend_address_pools:
      for bp in (ip.application_gateway_backend_address_pools or []):
        for lbp in lb.backend_address_pools:
          if (lbp.id == bp.id):
            return {'backend_pool': bp, 'ip_config': ip}
    return None

  def _find_backend_pool(self, lb, bp_name):
    """
    Given a load balancer, attempts to find the backend pool, and if not found, returns the first backend pool.
    """
    if not lb or not lb.backend_address_pools or len(lb.backend_address_pools) == 0:
      return None
    bp_list = [b for b in lb.backend_address_pools if b.name == bp_name]
    if len(bp_list) > 0:
      return bp_list[0]
    else:
      return lb.backend_address_pools[0]

  def _match_ip_config(self, vm):
    """
    Finds the ip config object within the network interface to associate the backend pool for the VM.
    """
    for nf in vm.network_profile.network_interfaces:
      nic = self.get_network_interface(nf.id)
      if nic.primary:
        return {'network_interface': nic, 'ip_config': next(iter(nic.ip_configurations))}
    return None

  def add(self):
    """
    Add the current instance to all configured LBs.
    Assumes that this code is running on an Azure instance.
    """
    instance_id = self.get_current_instance_id()
    vm = self.get_current_machine()
    for lb in self.lbs:
      # Note: This only finds the VM in one of the balancer's backend pools
      match = self.match_load_balancer_and_vm(lb, vm)
      if not match:
        self.record(lb.name,
                    instance_id,
                    RegistrationAction.REGISTER,
                    [RegistrationActionReason.NOT_YET_REGISTERED])
        if not self.add_vm_to_load_balancer(lb, vm):
            raise AzureException("failed to register vm {} with lb {}".format(vm, lb))
        else:
            logger.info("registered vm {} with lb {}".format(vm, lb))
      else:
        self.record(lb.name,
                    instance_id,
                    RegistrationAction.NONE,
                    [RegistrationActionReason.ALREADY_REGISTERED])

  def remove(self):
    """
    Remove the current instance from all configured LBs.
    Assumes that this code is running on an Azure instance.
    """
    instance_id = self.get_current_instance_id()
    vm = self.get_current_machine()
    for lb in self.lbs:
      match = self.match_load_balancer_and_vm(lb, vm)
      if match:
        self.record(lb.name,
                    instance_id,
                    RegistrationAction.REMOVE)
        self.remove_vm_from_load_balancer(lb, vm)
      else:
        self.record(lb.name,
                    instance_id,
                    RegistrationAction.NONE,
                    [RegistrationActionReason.NOT_ALREADY_REGISTERED])
