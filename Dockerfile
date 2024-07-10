FROM ubuntu:latest

RUN apt-get update && apt-get -y install cron python3 python3-pip python3-virtualenv unzip libjpeg-dev zlib1g-dev

RUN useradd mountaineer

# Build files and create deployments
#===================================
RUN mkdir -p /opt/mountain/build
RUN python3 -m virtualenv /opt/mountain/build/_venv
RUN /opt/mountain/build/_venv/bin/pip install argparse
COPY common /opt/mountain/build/common/
COPY "*.py" /opt/mountain/build/
COPY "requirements.*.txt" /opt/mountain/build/

WORKDIR /opt/mountain/build
RUN mkdir -p /opt/mountain/build/deploy
RUN _venv/bin/python deploy.py snapshot
RUN _venv/bin/python deploy.py classify

# Copy deployments to prep for installation
#==========================================
RUN mkdir -p /opt/mountain/snapshot
RUN cp deploy/snapshot.zip /opt/mountain/snapshot/.

RUN mkdir -p /opt/mountain/classify
RUN cp deploy/classify.zip /opt/mountain/classify/.

# Install snapshotting service
#=============================
WORKDIR /opt/mountain/snapshot
COPY release/take-mountain-snapshot /usr/local/bin/.
RUN unzip snapshot.zip
RUN python3 -m virtualenv _venv
RUN _venv/bin/pip install -r requirements.txt

# Install classification service
#===============================
WORKDIR /opt/mountain/classify
COPY release/classify-mountain-snapshot /usr/local/bin/.
RUN unzip classify.zip
RUN python3 -m virtualenv _venv
RUN _venv/bin/pip install -r requirements.txt

RUN chmod a+x /usr/local/bin/*-mountain-snapshot

COPY release/99-mountain-cron /etc/crontab

CMD cron