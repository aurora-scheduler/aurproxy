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

python_library(name='backends',
  dependencies=[
    'tellapart/aurprroxy/config',
    'tellapart/aurprroxy/exception',
    'tellapart/aurprroxy/metrics/store:increment_counter',
    'tellapart/aurprroxy/source',
    'tellapart/aurprroxy/util',
    'tellapart/aurprroxy/util:get_logger',
    'tellapart/aurprroxy/util:load_klass_factory',
    'tellapart/aurprroxy/util:load_klass_plugin',
  ],
  sources=globs('tellapart/aurproxy/backends/backend.py'),
)