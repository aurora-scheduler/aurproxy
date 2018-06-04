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

"""Basic Flask HTTP modules for composing larger applications.
"""

__copyright__ = 'Copyright (C) 2015 TellApart, Inc. All Rights Reserved.'

import os
import socket
from flask import (
  Blueprint,
  Response)
import flask_restful
from prometheus_client import REGISTRY, core

from tellapart.aurproxy.app import lifecycle
from tellapart.aurproxy.metrics.store import root_metric_store

# Define a standard blueprint for lifecycle management endpoints
lifecycle_blueprint = Blueprint('lifecycle', __name__)
_bp = flask_restful.Api(lifecycle_blueprint)

hostname = socket.getfqdn()
environ = os.environ.get('ENVIRON', 'beta')
domain = os.environ.get('DOMAIN', 'localhost')

@_bp.resource('/quitquitquit')
class QuitQuitQuit(flask_restful.Resource):
  def post(self):
    lifecycle.execute_shutdown_handlers()
    return 'OK', 200

@_bp.resource('/abortabortabort')
class AbortAbortAbort(flask_restful.Resource):
  def post(self):
    lifecycle.execute_shutdown_handlers()
    return 'OK', 200

@_bp.resource('/health')
class Health(flask_restful.Resource):
  def get(self):
    status, message = lifecycle.check_health()
    if not status:
      # Still respond with 200, otherwise Aurora UI doesn't show failure text.
      return Response(response='Health checks failed: %s' % message)

    return Response(response='OK')

@_bp.resource('/metrics')
class Metrics(flask_restful.Resource):
  def get(self):
    '''Returns the metrics from the registry in latest text format as a string.'''
    output = []
    for metric in REGISTRY.collect():
      output.append('# HELP {0} {1}'.format(
        metric.name, metric.documentation.replace('\\', r'\\').replace('\n', r'\n')))
      output.append('\n# TYPE {0} {1}\n'.format(metric.name, metric.type))
      for name, labels, value in metric.samples:
        if labels:
          labels['host'] = hostname
          labels['env'] = environ
          labels['domain'] = domain
          labelstr = '{{{0}}}'.format(','.join(
            ['{0}="{1}"'.format(k, v.replace('\\', r'\\').replace('\n', r'\n').replace('"', r'\"'))
              for k, v in sorted(labels.items())]
          ))
        else:
          labelstr = ''
        output.append('aurproxy_{0}{1} {2}\n'.format(name, labelstr, core._floatToGoString(value)))
    return Response(response=''.join(output).encode('utf-8'), mimetype="text/plain")

@_bp.resource('/metrics.json')
class MetricsJson(flask_restful.Resource):
  def get(self):
    metrics = root_metric_store().get_metrics()
    ordered_metrics = sorted(metrics, key=lambda metric: metric.name)

    return dict((m.name, m.value()) for m in ordered_metrics)
