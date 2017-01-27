FROM ubuntu:14.04
MAINTAINER Codey oxley <codey.a.oxley+os@gmail.com>
EXPOSE 8990

# These are the supported environment variables.
# Use them to control the 'default' Django database configuration:
#     DB_ENGINE
#     DB_NAME
#     DB_USER
#     DB_PASSWORD
#     DB_HOST
#     DB_PORT
#
#     NSOT_EMAIL
#     NSOT_SECRET

# Install necessary packages
#
# The development packages are for building certain dependencies that pip pulls
# in
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get --quiet=2 update
RUN apt-get --quiet=2 install -y \
        python \
        python-dev \
        python-pip \
        libffi6 \
        libffi-dev \
        libssl-dev \
        libmysqlclient-dev \
        curl

RUN apt-get --quiet=2 install -y python-psycopg2
RUN apt-get --quiet=2 install -y sqlite3
RUN pip install MySQL-Python
RUN pip install psycopg2

# Try to run this as late as possible for layer caching - this version will be
# updated every update so let the build not take longer than necessary
RUN pip install nsot==1.1.1
COPY conf /etc/nsot

ENTRYPOINT ["nsot-server", "--config=/etc/nsot/nsot.conf.py"]

# If using --no-upgrade then the database won't be built for first run. Use
# should specify --no-upgrade manually if they don't want it
CMD ["start", "--noinput"]
# CMD ["start", "--noinput", "--no-upgrade"]
