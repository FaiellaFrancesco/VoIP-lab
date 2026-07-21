FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y --no-install-recommends baresip \
 && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /root/.baresip
COPY config      /root/.baresip/config
COPY accounts    /root/.baresip/accounts
COPY secret.wav  /root/secret.wav

CMD ["baresip", "-f", "/root/.baresip"]
