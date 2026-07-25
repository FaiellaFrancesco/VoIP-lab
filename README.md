# VoIP-lab

Un piccolo laboratorio per **rompere** e poi **difendere** le comunicazioni VoIP. In pratica ricostruisco un'intera reticella telefonica dentro Docker — un centralino, un telefono-vittima e due container per gli attacchi (uno che intercetta, uno che falsifica l'identità) — per far vedere dal vivo cosa succede quando SIP e RTP viaggiano senza protezioni.

## 1. Obiettivo

L'idea di fondo: i protocolli base del VoIP (**SIP** e **RTP**) sono nati per *funzionare*, non per essere *sicuri*. Senza cifratura, chi si trova sulla stessa rete può:

1. **Ascoltare la conversazione** (intercettazione / *eavesdropping*) — colpisce il flusso audio **RTP**.
2. **Falsificare l'identità del chiamante** (*caller ID spoofing*) — colpisce la segnalazione **SIP**.

Morale: Serve difesa vera (SRTP, SIP/TLS, autenticazione).

## 2. Mappa dei file del progetto

```
voip-lab/
├── docker-compose.yml          # orchestra i container + la rete
│
├── asterisk/                   # il CENTRALINO
│   ├── Dockerfile              #   come costruire l'immagine Asterisk
│   ├── pjsip.conf              #   i due telefoni SIP (6001, 6002) + endpoint anonimo
│   ├── extensions.conf         #   il "dialplan": cosa fa un numero quando lo chiami
│   └── secret.wav              #   (residuo del vecchio Playback; ora la 500 usa Echo)
│
├── phone/                      # il TELEFONO-VITTIMA
│   ├── Dockerfile              #   come costruire l'immagine baresip
│   ├── config                  #   audio/moduli di baresip
│   ├── accounts                #   la "SIM": credenziali e registrazione
│   └── secret.wav              #   l'audio noto (60s) che la vittima "dice"
│
├── attacker/                   # l'ATTACCANTE (attacco 1: intercettazione)
│   └── Dockerfile              #   immagine con arpspoof + tcpdump
│
├── spoofer/                    # il CHIAMANTE MALEVOLO (attacco 2: spoofing)
│   ├── Dockerfile              #   immagine con sipp
│   └── spoof.xml               #   scenario SIP con From: falsificato
│
├── gen_secret.py               # genera secret.wav (8kHz mono, ~60s)
└── captures/                   # (creata automaticamente) i .pcap catturati
```

## 3. Requisiti

- **Docker** e **Docker Compose v2** su un host **Linux**.
- **Wireshark** sull'host, per ricostruire l'audio e leggere i messaggi SIP dai `.pcap`.

## 4. Avvio rapido

```bash
docker compose up --build
```

Controlla che i telefoni siano registrati:
```bash
docker exec voip-asterisk asterisk -rx "pjsip show endpoints"
```
`6001` deve risultare `Not in use` (= registrato).

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
| `voip-attacker` | 172.20.0.66 | Attacco 1 — intercettazione: arpspoof (ARP poisoning) + tcpdump |
| `voip-spoofer` | 172.20.0.99 | Attacco 2 — spoofing: sipp che invia un INVITE con identità falsa |

Tutti i telefoni sono forzati sul codec **G.711**, così Wireshark riesce a ricostruire l'audio nativamente.

## 6. Gli attacchi in breve

**Attacco 1 — Intercettazione (eavesdropping)**
L'attaccante fa ARP spoofing per mettersi in mezzo (MITM), cattura l'RTP con tcpdump e ricostruisce l'audio in Wireshark. Poiché l'RTP è in chiaro, la conversazione si riascolta.

**Attacco 2 — Caller ID Spoofing (Scenario A)**
Un container esterno **senza credenziali** invia un INVITE con `From: "Assistenza Banca"`. Il centralino, configurato per accettare chiamate anonime, lo instrada. Il `From:` falso è leggibile in chiaro. È il meccanismo del *vishing*.


## 7. Stato del progetto

- [x] Infrastruttura Docker (centralino + vittima + attaccanti) funzionante
- [x] Chiamata con audio noto stabile (~60s)
- [x] Attacco 1: ARP spoofing + cattura + ricostruzione audio in Wireshark
- [x] Attacco 2: caller ID spoofing con INVITE falsificato
- [ ] Contromisure (SRTP, SIP/TLS, autenticazione) e confronto prima/dopo

## 8. Nota sulla sicurezza

Le password SIP qui dentro sono **credenziali usa-e-getta a scopo didattico**. In un sistema vero andrebbero messe fuori dal codice (es. in un `.env` non versionato) e mai committate in chiaro. Stessa cosa per l'endpoint anonimo in `pjsip.conf`: è **volutamente** insicuro, serve a dimostrare l'attacco 2.