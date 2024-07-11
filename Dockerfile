FROM ubuntu:latest AS build

RUN apt-get update && apt-get -y install cron python3 python3-pip python3-virtualenv unzip libjpeg-dev zlib1g-dev

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
RUN unzip snapshot.zip
RUN python3 -m virtualenv _venv
RUN _venv/bin/pip install -r requirements.txt

# Install classification service
#===============================
WORKDIR /opt/mountain/classify
RUN unzip classify.zip
RUN python3 -m virtualenv _venv
RUN _venv/bin/pip install -r requirements.txt

# Create final / image container
#=======================
FROM ubuntu:latest

RUN apt-get update && apt-get -y install python3 curl

# Install Supercronic
#====================
# Latest releases available at https://github.com/aptible/supercronic/releases
ENV SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.2.30/supercronic-linux-amd64 \
  SUPERCRONIC=supercronic-linux-amd64 \
  SUPERCRONIC_SHA1SUM=9f27ad28c5c57cd133325b2a66bba69ba2235799
RUN curl -fsSLO "$SUPERCRONIC_URL" \
  && echo "${SUPERCRONIC_SHA1SUM}  ${SUPERCRONIC}" | sha1sum -c - \
  && chmod +x "$SUPERCRONIC" \
  && mv "$SUPERCRONIC" "/usr/local/bin/${SUPERCRONIC}" \
  && ln -s "/usr/local/bin/${SUPERCRONIC}" /usr/local/bin/supercronic

RUN useradd -m mountaineer

COPY --from=build /opt/mountain/snapshot /opt/mountain/snapshot
COPY --from=build /opt/mountain/classify /opt/mountain/classify
COPY release/take-mountain-snapshot /usr/local/bin/.
COPY release/classify-mountain-snapshot /usr/local/bin/.

# Copy over snapshotting tools
#=============================
RUN chmod a+x /usr/local/bin/*-mountain-snapshot
COPY release/99-mountain-cron /etc/crontab

USER mountaineer
CMD supercronic /etc/crontab