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

from tellapart.aurproxy.config import SourceEndpoint, ShareEndpoint
from tellapart.aurproxy.exception import AurProxyConfigException
from tellapart.aurproxy.source import ProxySource
from tellapart.aurproxy.util import get_logger

logger = get_logger(__name__)


class StaticProxySource(ProxySource):

  def __init__(self,
               signal_update_fn=None,
               share_adjuster_factories=None,
               **kwargs):
    super(StaticProxySource, self).__init__(signal_update_fn,
                                            share_adjuster_factories)
    self._name = kwargs.get('name')
    self._host = kwargs.get('host')
    self._port = kwargs.get('port')
    self._endpoint = SourceEndpoint(self._host, self._port)
    err_fmt = '"{0}" required on StaticProxySource'
    if not self._name:
      raise AurProxyConfigException(err_fmt.format('name'))
    if not self._host:
      raise AurProxyConfigException(err_fmt.format('host'))
    if not self._port:
      raise AurProxyConfigException(err_fmt.format('port'))

  @property
  def blueprint(self):
    return None

  @property
  def slug(self):
    return '{0}__{1}__{2}'.format(self._name,
                                  self._host,
                                  self._port)

  def start(self):
    self.add(self._endpoint)

  def stop(self):
    self.remove(self._endpoint)


class StaticListProxySource(ProxySource):
  """
    ServerListProxy
  """

  def __init__(self,
               signal_update_fn=None,
               share_adjuster_factories=None,
               **kwargs):
    """

    :param signal_update_fn:
    :param share_adjuster_factories:
    :param kwargs:
    """
    super(StaticListProxySource, self).__init__(signal_update_fn,
                                                share_adjuster_factories)
    self._server_set = []
    server_list = kwargs.get('server_list')
    logger.info('ServerList: {0}'.format(server_list))
    err_fmt = '"{0}" required on StaticListProxySource'
    for idx, server_info in enumerate(server_list):
      _host = server_info.get('host')
      _port = server_info.get('port')
      _share = server_info.get('share') if server_info.get('share') else 1.0
      _context = {'source': "{0}.{1}.{2}.{3}.{4}".format(kwargs.get('cluster'),
                                                         kwargs.get('role'),
                                                         kwargs.get('environment'),
                                                         kwargs.get('job'),
                                                         idx)}
      if not _host:
        raise AurProxyConfigException(err_fmt.format('host'))
      if not _port:
        raise AurProxyConfigException(err_fmt.format('port'))
      self._server_set.append(ShareEndpoint(_host, _port, _share, 1.0, _context))
    if self._server_set.count == 0:
      raise AurProxyConfigException(err_fmt.format('server_list'))

  @property
  def blueprint(self):
    return None

  @property
  def slug(self):
    slugs = []
    for server_info in self._server_set:
      slugs.append('{0}_{1}'.format(server_info.host, server_info.port))
    return '__'.join(slugs)

  def start(self):
    for server in self._server_set:
      logger.debug("Add ServerList: {0}:{1}".format(server.host, server.port))
      self.add(server)

  def stop(self):
    for server in self._server_set:
      logger.debug("Remove ServerList: {0}:{1}".format(server.host, server.port))
      self.remove(server)
