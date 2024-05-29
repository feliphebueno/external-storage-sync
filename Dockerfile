ARG BASE_IMAGE=python:3.12.2-slim-bookworm
ARG APP_FOLDER=/var/www/external_storage_sync

FROM ${BASE_IMAGE} as base_builder
ARG SSHKEY
ARG KNOWN_HOSTS

RUN : "---------- install OS libs ----------" \
    && apt-get update -y \
    && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        openssh-client \
        build-essential \
        libssl-dev \
        libffi-dev \
        make \
        gcc \
        libpq-dev \
        zlib1g-dev \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

FROM base_builder as dependencies_builder

WORKDIR ${APP_FOLDER}

COPY requirements/*.txt /tmp/requirements/

RUN : "---------- build project dependencies --------------" \
    && python -m pip install --upgrade pip  \
    && python -m pip wheel --wheel-dir=/root/wheels -r /tmp/requirements/prod.txt;

# Final app image
FROM ${BASE_IMAGE} as app_final_image
ARG APP_FOLDER

WORKDIR ${APP_FOLDER}

COPY --from=dependencies_builder /root/wheels /root/wheels
COPY ./bin/*.sh ./bin/
COPY ./bin/setup_admin_user.py ./bin/

RUN : "---------- install container extras ----------" \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    procps \
    curl \
    netcat-traditional \
    openssl;

RUN : "---------- install project libs ----------" \
    && WHEELS=$(cd /root/wheels; ls -1 *.whl | awk -F - '{ gsub("_", "-", $1); print $1 }' | uniq) \
    && python -m pip install --no-index --find-links=/root/wheels $WHEELS;


# Django app
EXPOSE 8000

WORKDIR ${APP_FOLDER}
ENTRYPOINT ["/entrypoint.sh"]

HEALTHCHECK \
    --start-period=15s \
    --timeout=14s \
    --retries=1 \
    --interval=20s \
    CMD /health_check.sh
