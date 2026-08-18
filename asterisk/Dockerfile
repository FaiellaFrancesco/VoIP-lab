FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y --no-install-recommends asterisk openssl \
 && rm -rf /var/lib/apt/lists/*

# Certificato self-signed per TLS (usato solo dal profilo "secure")
RUN mkdir -p /etc/asterisk/keys \
 && openssl req -x509 -newkey rsa:2048 -nodes \
      -keyout /etc/asterisk/keys/asterisk.key \
      -out /etc/asterisk/keys/asterisk.crt \
      -days 3650 -subj "/CN=172.20.0.10"

COPY extensions.conf  /etc/asterisk/extensions.conf
RUN mkdir -p /var/lib/asterisk/sounds/en
COPY secret.wav /var/lib/asterisk/sounds/en/secret.wav

CMD ["asterisk", "-f", "-vvv"]
