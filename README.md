# NAD C 356BEE for Home Assistant

En HACS-kompatibel custom integration som styrer NAD C 356BEE via RS-232,
inkludert ESPHome sin innebygde `serial_proxy` over Native API.

## Funksjoner

- Mediespiller med av/på, mute, inngangsvalg og volum opp/ned.
- Brytere for Speaker A, Speaker B og Tape1 Monitor.
- Tilstand leses fra forsterkeren ved oppsett og hvert 15. sekund.
- Tilkoblingen gjenopprettes ved neste polling etter forbindelsesfeil.
- Oppsett via brukergrensesnittet, med norsk og engelsk oversettelse.

C 356BEE støtter bare `Main.Volume+` og `Main.Volume-` fordi volumkontrollen er
motorisert. Integrasjonen tilbyr derfor ingen volumprosent eller absolutt volum.
Inngangsnavnene følger RS-232-protokollen: CD, Tuner, Video, Disc, Ipod, Tape2, Aux.
Tape1 Monitor er en egen bryter.

## Maskinvare og ESPHome

Du trenger en ESP32 og en **RS-232-transceiver som tåler 3,3 V logikk**, for
eksempel en egnet MAX3232-modul. Ikke koble ESP32 GPIO direkte til NAD sin
RS-232-port; spenningsnivåene er forskjellige.

Se [ESPHome-eksemplet](examples/esphome-nad.yaml). Tilpass board og GPIO-pinner,
og legg Wi-Fi, API-nøkkel og OTA-passord i ESPHome sin `secrets.yaml`.

NAD sin DB9-port bruker pinne 2 for TX, pinne 3 for RX og pinne 5 for signaljord:

| Fra | Til |
| --- | --- |
| ESP32 TX (GPIO17 i eksemplet) | Transceiver sin TTL-inngang for sending |
| Transceiver sin RS-232-utgang | NAD DB9 pinne 3 (RX) |
| NAD DB9 pinne 2 (TX) | Transceiver sin RS-232-inngang |
| Transceiver sin TTL-utgang for mottak | ESP32 RX (GPIO16 i eksemplet) |
| Signaljord | NAD DB9 pinne 5 og transceiver/ESP32 GND |

Sjekk modulens pinnebeskrivelse; DB9-kontakter på ferdige moduler kan ha ulik
kobling. Kommunikasjonen er 115200 baud, 8N1, uten flytkontroll. Forsterkerens
hovedstrømbryter må være på; integrasjonen kan styre standby.

Flash ESPHome og legg enheten til i Home Assistant sin ESPHome-integrasjon før
du setter opp NAD-integrasjonen. Bruk ESPHome 2026.5 eller nyere med
`serial_proxy` og Home Assistant 2026.5 eller nyere. Serial proxy er fortsatt
merket eksperimentell av ESPHome.

## Installasjon via HACS

Dette prosjektet må først publiseres som et GitHub-repository. Ingen publisert
repository-adresse følger med denne lokale utgaven.

1. Last opp prosjektet til ditt GitHub-repository, og lag gjerne release `v0.1.0`.
2. I HACS velger du **Custom repositories**, legger til repository-URL-en og
   velger kategorien **Integration**.
3. Last ned **NAD C 356BEE**, og start Home Assistant på nytt.
4. Gå til **Innstillinger → Enheter og tjenester → Legg til integrasjon**,
   velg **NAD C 356BEE**, og velg ESPHome-porten **NAD RS232**.

Alternativt kan du kopiere `custom_components/nad_c356bee` til Home Assistant
sin `config/custom_components/`-mappe og starte på nytt.

Serieportvelgeren støtter også lokale porter. ESPHome-porten som Home Assistant
tilbyr, bruker `esphome-hass://` og eksisterende API-tilkobling. Unngå å legge
API-nøkler manuelt i URL-er. Én integrasjon skal eie serieporten om gangen.

Oppsettet spør etter modell og tilstand, uten å slå på forsterkeren eller endre
volumet. Hvis oppsettet feiler, sjekk TX/RX, baudrate, at ESPHome er tilkoblet,
og at NAD sin hovedstrømbryter er på. Kontroller også at ingen andre bruker porten.

## Utvikling og verifikasjon

```sh
python3 -m unittest discover -s tests -v
python3 -m compileall -q custom_components tests
```

Testene bruker en simulert seriell forbindelse og verifiserer kommandoer,
fragmenterte CR/LF-svar, modellkontroll og feilbehandling. Fysisk ESP32/NAD og
installasjon gjennom HACS må fortsatt testes på faktisk utstyr.

## Referanser

- [Home Assistant: migrering til serialx](https://developers.home-assistant.io/blog/2026/04/27/pyserial-to-serialx/)
- [ESPHome serial_proxy](https://esphome.io/components/serial_proxy/)
- [NAD RS-232-protokoll](https://nadelectronics.com/support/code/NAD_TXX5_Control_Docs/nad_ethernet_rs232_spec_2.03.pdf)
- Modellkommandoene er basert på NAD-dokumentet `C356_RS232_Commands.pdf`
  (17. november 2010), som følger med NAD sin C356BEE RS232 Codes-pakke.

Lisens: MIT.
