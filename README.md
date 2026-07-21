# VoIP-lab
 
Laboratorio didattico per dimostrare, e poi difendere, le vulnerabilità delle comunicazioni VoIP non protette. Ricrea un'intera rete telefonica in miniatura con tre container Docker: centralino, telefono-vittima e attaccante.

## 1. Obiettivo
 
Il lab dimostra come i protocolli di base VoIP (**SIP** e **RTP**) siano progettati per funzionare, ma **non** per essere sicuri. Senza cifratura, un attaccante sulla stessa rete può:
 
1. **Ascoltare la conversazione** (intercettazione / *eavesdropping*) — colpisce il flusso audio **RTP**.
2. **Falsificare l'identità del chiamante** (*caller ID spoofing*) — colpisce il flusso di segnalazione **SIP**.
La conclusione è che **non ci si può affidare ai soli protocolli iniziali**: serve difesa (SRTP, SIP/TLS, autenticazione).

## 2. Mappa dei file del progetto
 
```
voip-lab/
├── docker-compose.yml          # orchestra i 3 container + la rete
│
├── asterisk/                   # il CENTRALINO
│   ├── Dockerfile              #   come costruire l'immagine Asterisk
│   ├── pjsip.conf              #   definisce i due telefoni SIP (6001, 6002)
│   ├── extensions.conf         #   il "dialplan": cosa fa un numero quando lo chiami
│   └── secret.wav              #   (residuo del vecchio Playback; ora la 500 usa Echo)
│
├── phone/                      # il TELEFONO-VITTIMA
│   ├── Dockerfile              #   come costruire l'immagine baresip
│   ├── config                  #   configurazione audio/moduli di baresip
│   ├── accounts                #   la "SIM": credenziali e registrazione
│   └── secret.wav              #   l'audio noto (60s) che la vittima "dice"
│
├── attacker/                   # l'ATTACCANTE
│   └── Dockerfile              #   immagine con arpspoof + tcpdump
│
├── gen_secret.py               # genera secret.wav (8kHz mono, ~60s)
└── captures/                   # (creata automaticamente) i .pcap catturati
```
 
## 3. Requisiti
 
- **Docker** e **Docker Compose v2** su un host **Linux** (necessario per l'ARP spoofing di basso livello).
- **Wireshark** sull'host, per ricostruire l'audio dai `.pcap` catturati.
## 4. Avvio rapido
 
```bash
docker compose up --build
```
 
Verifica che i telefoni siano registrati:
```bash
docker exec voip-asterisk asterisk -rx "pjsip show endpoints"
```
`6001` deve risultare `Not in use` (registrato).
 
Prova una chiamata con audio:
```bash
docker attach voip-phone     # digita 500 + Invio; 'b' per riagganciare
                             # Ctrl-P poi Ctrl-Q per staccarti senza spegnere
```
## 5. Componenti
 
| Container | IP | Ruolo |
|---|---|---|
| `voip-asterisk` | 172.20.0.10 | Centralino (PBX): registra i telefoni e instrada SIP/RTP |
| `voip-phone` | 172.20.0.20 | Telefono-vittima (baresip), estensione 6001 |
| `voip-attacker` | 172.20.0.66 | Attaccante: arpspoof (ARP poisoning) + tcpdump (cattura) |
 
Tutti i telefoni sono forzati sul codec **G.711**, così Wireshark può ricostruire l'audio nativamente.
 
## 6. Stato del progetto
 
- [x] Infrastruttura Docker (centralino + vittima + attaccante) funzionante
- [x] Chiamata con audio noto stabile (~60s)
- [x] Esecuzione dell'attacco: ARP spoofing + cattura + ricostruzione in Wireshark
- [ ] Attacco 2: caller ID spoofing
- [ ] Contromisure (SRTP, SIP/TLS) e confronto prima/dopo
## 7. Nota
 
Le password SIP in questo repository sono **credenziali usa-e-getta a scopo didattico**. In un sistema reale andrebbero esternalizzate (es. in un file `.env`, escluso dal versionamento) e mai committate in chiaro.
 
