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

python_library(name='nginx',
  dependencies=[
    '3rdparty/python:Jinja2',
    'tellapart/aurproxy/backends',
    'tellapart/aurproxy/backends/nginx/metrics',
    'tellapart/aurproxy/metrics/store:increment_counter',
    'tellapart/aurproxy/metrics/store:update_counter',
    'tellapart/aurproxy/metrics/store:update_gauge',
    'tellapart/aurproxy/util:get_logger',
    'tellapart/aurproxy/util:move_file',
    'tellapart/aurproxy/util:run_local',
  ],
  sources=globs('tellapart/aurproxy/backends/nginx/*.py'),
)