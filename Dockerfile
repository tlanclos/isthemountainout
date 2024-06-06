FROM ubuntu:latest

RUN apt-get update && apt-get -y install cron python3 python3-pip python3-virtualenv unzip libjpeg-dev zlib1g-dev

RUN useradd mountaineer

COPY deploy/snapshot.zip /opt/mountain/snapshot/
COPY release/take-mountain-snapshot /usr/local/bin/.
RUN unzip /opt/mountain/snapshot/snapshot.zip -d /opt/mountain/snapshot
RUN python3 -m virtualenv /opt/mountain/snapshot/_venv
RUN /opt/mountain/snapshot/_venv/bin/pip install -r /opt/mountain/snapshot/requirements.txt

COPY deploy/classify.zip /opt/mountain/classify/
COPY release/classify-mountain-snapshot /usr/local/bin/.
RUN unzip /opt/mountain/classify/classify.zip -d /opt/mountain/classify
RUN python3 -m virtualenv /opt/mountain/classify/_venv
RUN /opt/mountain/classify/_venv/bin/pip install -r /opt/mountain/classify/requirements.txt

RUN chmod a+x /usr/local/bin/*-mountain-snapshot

CMD cron