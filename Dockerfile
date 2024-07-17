FROM ubuntu:jammy AS build

RUN apt-get update && apt-get install -y apt-transport-https curl gnupg
RUN curl -fsSL https://bazel.build/bazel-release.pub.gpg | gpg --dearmor >bazel-archive-keyring.gpg
RUN mv bazel-archive-keyring.gpg /usr/share/keyrings
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/bazel-archive-keyring.gpg] https://storage.googleapis.com/bazel-apt stable jdk1.8" | tee /etc/apt/sources.list.d/bazel.list
RUN apt-get update && apt-get -y install cron python3 python3-pybind11 \
  python3-pip python3-virtualenv unzip libjpeg-turbo8-dev \
  zlib1g-dev pkg-config libhdf5-dev cmake git bazel-6.1.0 bazel

# Build tensorflow lite from source
#==================================
RUN git clone --depth 1 --branch v2.14.0 https://github.com/tensorflow/tensorflow.git /opt/tensorflow
RUN mkdir -p /opt/tensorflow/build
RUN cd /opt/tensorflow/build && PYTHON=python3 ../tensorflow/lite/tools/pip_package/build_pip_package_with_bazel.sh native

# Build files and create deployments
#===================================
RUN mkdir -p /opt/mountain/build
RUN python3 -m virtualenv /opt/mountain/build/_venv
RUN /opt/mountain/build/_venv/bin/pip install argparse
COPY "requirements.*.txt" /opt/mountain/build/
RUN /opt/mountain/build/_venv/bin/pip install -r /opt/mountain/build/requirements.prod.txt
RUN /opt/mountain/build/_venv/bin/pip install -r /opt/mountain/build/requirements.dev.txt
RUN /opt/mountain/build/_venv/bin/pip install /opt/tensorflow/tensorflow/lite/tools/pip_package/gen/tflite_pip/python3/dist/tflite_runtime-2.14.0-cp310-cp310-linux_x86_64.whl

COPY common /opt/mountain/build/common/
COPY "*.py" /opt/mountain/build/
WORKDIR /opt/mountain/build
RUN _venv/bin/python deploy.py prod-package

# Copy deployments to prep for installation
#==========================================
RUN mkdir -p /opt/mountain/prod
RUN cp deploy/prod.zip /opt/mountain/prod/.

# Install cron services
#=============================
WORKDIR /opt/mountain/prod
RUN unzip prod.zip
RUN python3 -m virtualenv _venv
RUN _venv/bin/pip install -r requirements.txt
RUN _venv/bin/pip install /opt/tensorflow/tensorflow/lite/tools/pip_package/gen/tflite_pip/python3/dist/tflite_runtime-2.14.0-cp310-cp310-linux_x86_64.whl

# Create final / image container
#=======================
FROM ubuntu:jammy

RUN apt-get update && apt-get -y install python3 curl libjpeg-turbo8 zlib1g 

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

COPY --from=build /opt/mountain/prod /opt/mountain/prod
COPY cron/take-mountain-snapshot /usr/local/bin/.
COPY cron/classify-mountain-snapshot /usr/local/bin/.

# Copy over snapshotting tools
#=============================
RUN chmod a+x /usr/local/bin/*-mountain-snapshot
COPY cron/99-mountain-cron /etc/crontab

USER mountaineer
CMD supercronic /etc/crontab