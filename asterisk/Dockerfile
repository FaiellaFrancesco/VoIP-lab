# Immagine base (Ubuntu mantiene il pacchetto asterisk; Debian bookworm no)
FROM ubuntu:24.04

# Evita i prompt interattivi durante l'installazione (es. tzdata)
ENV DEBIAN_FRONTEND=noninteractive

# Installa Asterisk dai repository Ubuntu
RUN apt-get update \
 && apt-get install -y --no-install-recommends asterisk \
 && rm -rf /var/lib/apt/lists/*

# Copia le configurazioni del lab
COPY pjsip.conf       /etc/asterisk/pjsip.conf
COPY extensions.conf  /etc/asterisk/extensions.conf

# Copia l'audio noto usato dalla extension 500 (Playback)
RUN mkdir -p /var/lib/asterisk/sounds/en
COPY secret.wav /var/lib/asterisk/sounds/en/secret.wav

# Avvia Asterisk in primo piano (obbligatorio dentro un container)
CMD ["asterisk", "-f", "-vvv"]
