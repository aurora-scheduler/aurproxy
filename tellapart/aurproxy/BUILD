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
    'tellapart/aurproxy',
  ],
)

python_binary(
  name='aurproxy',
  dependencies=[
    ':_library',
  ],
  source='*.py',
)