# FROM --platform=linux/amd64 kitware/trame:py3.12-uv
FROM --platform=amd64 kitware/trame:py3.11

RUN apt-get update && apt-get install -y \
    libglu1-mesa-dev \
    libgl1-mesa-dev \
    libxrandr2 \
    libxinerama1 \
    libxcursor1 \
    libxi6 \
    libxft2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && echo "Mutex posixsem" >> /etc/apache2/apache2.conf
 

COPY --chown=trame-user:trame-user . /deploy

ENV TRAME_CLIENT_TYPE=vue3
RUN /opt/trame/entrypoint.sh build