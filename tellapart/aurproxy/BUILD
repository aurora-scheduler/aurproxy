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
#

python_binary(
  name='tellapart.aurproxy',
  entry_point = 'tellapart.aurproxy.command',
  dependencies = [
    ':aurproxy_lib'
  ],
)

python_library(
  name = 'tellapart.aurproxy.command',
  sources = [ 'command.py' ],
  dependencies = [
    ':_lib',
    '3rdparty/python:pex',
  ]
)

python_library(
  name = '_lib',
  dependencies = [
    '3rdparty/python:boto',
    '3rdparty/python:commandr',
    '3rdparty/python:Flask-RESTful',
    '3rdparty/python:gevent',
    '3rdparty/python:Jinja2',
    '3rdparty/python:kazoo',
    '3rdparty/python:librato-metrics',
    '3rdparty/python:psutil',
    '3rdparty/python:python-dateutil',
    '3rdparty/python:raven',
    '3rdparty/python:requests',
    'tellapart/aurproxy/app/module',
    'tellapart/aurproxy/app',
    'tellapart/aurproxy/backends/nginx',
    'tellapart/aurproxy/backends',
    'tellapart/aurproxy/config',
    'tellapart/aurproxy/metrics',
    'tellapart/aurproxy/register',
    'tellapart/aurproxy/share/adjusters',
    'tellapart/aurproxy/share',
    'tellapart/aurproxy/source/sources',
    'tellapart/aurproxy/source',
  ],
  sources=globs('tellapart/aurproxy/*.py'),
)
