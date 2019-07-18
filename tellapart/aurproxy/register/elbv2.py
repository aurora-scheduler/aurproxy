"""Registration implementation for AWS V2 Elastic Load Balancers.
"""

from tellapart.aurproxy.register.aws import AwsRegisterer
from tellapart.aurproxy.register.base import (
  RegistrationAction,
  RegistrationActionReason
)
from tellapart.aurproxy.util import get_logger

logger = get_logger(__name__)


class ElbSelfRegisterer(AwsRegisterer):
  """
  Registerer that adds and removes current machine from configured ELB target group.
  """

  def __init__(self, target_group_arn, region, access_key=None, secret_key=None):
    """
    Common code for ELB V2 Registerers.

    Args:
      target_group_arn - str - ARN for target group to register with.
      region - str - AWS region (EG: 'us-east-1').
      access_key - str - Optional AWS access key.
      secret_key - str - Optional AWS secret key.
    """
    super(ElbSelfRegisterer, self).__init__(region, access_key, secret_key)
    self._target_group_arn = target_group_arn


  def add(self):
    """
    Add the current instance to configured ELB Target Group.
    Assumes that this code is running on an EC2 instance.
    """
    instance_id = self.get_current_instance_id()
    self.conn.elbv2.register_targets(TargetGroupArn=self._target_group_arn,
                                     Targets=[{'Id': instance_id}])
    self.record(self._target_group_arn,
                instance_id,
                RegistrationAction.REGISTER)


  def remove(self):
    """
    Remove the current instance from all configured ELBs.
    Assumes that this code is running on an EC2 instance.
    """
    instance_id = self.get_current_instance_id()
    self.conn.elbv2.deregister_targets(TargetGroupArn=self._target_group_arn,
                                       Targets=[{'Id': instance_id}])
    self.record(self._target_group_arn,
                instance_id,
                RegistrationAction.REMOVE)
