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

python_library(
  name = '_library',
  sources = rglobs('*.py'),
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
    'tellapart/aurproxytest/backends/nginx',
    'tellapart/aurproxytest/backends',
    'tellapart/aurproxytest/share',
    'tellapart/aurproxytest/source/sources',
    'tellapart/aurproxytest/source',
  ],
)
