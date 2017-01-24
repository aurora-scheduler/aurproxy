# Newer python base images may break gevent.
# See https://github.com/docker-library/python/issues/29#issuecomment-70727289
FROM docker-registry.prod.foursquare.com/fs-base:2016-07-22-1516


######
# System prerequisite installation
######

# Ensure produser exists.
RUN useradd produser

# Install custom nginx plus deps for gevent build
RUN rpm --rebuilddb && \
  rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY* && \
  yum install -y --nogpgcheck aurproxy-nginx gcc python27-devel

######
# System prerequisite configuration
######

# Set up run directory for pids
RUN mkdir -p /var/run

# Remove default nginx config
RUN rm /etc/nginx/nginx.conf

# Symlink aurproxy nginx config
RUN mkdir -p /etc/aurproxy/nginx
RUN ln -sf /etc/aurproxy/nginx/nginx.conf /etc/nginx

# Create dynamic gor config location
RUN mkdir -p /etc/aurproxy/gor

######
# Application prerequisite installation
######

# Set up application sandbox
# (Gets mounted by aurora in production)
RUN mkdir -p /mnt/mesos/sandbox/sandbox

# Set up application directory
RUN mkdir -p /opt/aurproxy/

# Add application requirements
ADD ./requirements.txt /opt/aurproxy/requirements.txt

#  Install application requirements
RUN /usr/local/bin/virtualenv /opt/aurproxy/venv && \
  /opt/aurproxy/venv/bin/pip install -r /opt/aurproxy/requirements.txt


######
# Application setup
######
ADD ./tellapart/__init__.py /opt/aurproxy/tellapart/__init__.py
ADD ./tellapart/aurproxy /opt/aurproxy/tellapart/aurproxy
ADD ./templates /opt/aurproxy/tellapart/aurproxy/templates

# Not intended to be run
# Command will come from aurproxy.aur
CMD ["echo done"]
