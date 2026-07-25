FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y --no-install-recommends asterisk \
 && rm -rf /var/lib/apt/lists/*

# pjsip.conf NON viene copiato: lo monta il compose (insecure o secure)
COPY extensions.conf  /etc/asterisk/extensions.conf
RUN mkdir -p /var/lib/asterisk/sounds/en
COPY secret.wav /var/lib/asterisk/sounds/en/secret.wav

CMD ["asterisk", "-f", "-vvv"]
