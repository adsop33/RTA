FROM quay.io/jupyter/pyspark-notebook:python-3.11

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl vim wget git netcat-openbsd graphviz \
    postgresql-client redis-tools && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV KAFKA_VERSION=3.7.1
ENV SCALA_VERSION=2.12
RUN wget -q https://archive.apache.org/dist/kafka/${KAFKA_VERSION}/kafka_${SCALA_VERSION}-${KAFKA_VERSION}.tgz && \
    tar -xzf kafka_${SCALA_VERSION}-${KAFKA_VERSION}.tgz -C /usr/local/ && \
    ln -s /usr/local/kafka_${SCALA_VERSION}-${KAFKA_VERSION} /usr/local/kafka && \
    rm kafka_${SCALA_VERSION}-${KAFKA_VERSION}.tgz && \
    rm -rf /usr/local/kafka/bin/windows /usr/local/kafka/site-docs
ENV PATH="$PATH:/usr/local/kafka/bin"

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /tmp/requirements.txt && \
    fix-permissions "/home/${NB_USER}"

USER ${NB_USER}
WORKDIR /home/jovyan/notebooks/PROJEKT
