# Studieklokka

En studietimer som holder oversikt over hvor mye du faktisk studerer. Du velger fag og hvor lenge økta skal vare, og når den er ferdig legges tiden til et sammendrag for **dagen, uken, måneden og året**.

Laget med vibe coding (AI-assistert programmering) som obligatorisk oppgave i DAVE3625.

## Hvorfor
Jeg følger en fast studieplan med fem fag, og det er lett å *tro* at man har studert mye uten å vite det. Appen gjør studietiden målbar: hver økt blir logget per fag, og jeg ser med en gang om jeg når dagsmålet og hvordan uka fordeler seg på fagene.

## Funksjoner
- **Timer** med forhåndsvalg (25, 45, 60, 90 min) eller egen tid, og start, pause og stopp. Mellomromstasten starter og pauser.
- **Fag per økt.** Fagene kan velges, og du kan legge til egne.
- **Sammendrag** for i dag, inneværende uke (med ukenummer), måned og år.
- **Ukegraf** som viser minutter per dag fra mandag til søndag, med dagsmålet som en stiplet linje.
- **Fagfordeling** som viser hvor tiden har gått denne uken.
- **Streak** som teller dager på rad med minst én økt.
- **Dagsmål** som kan endres, med fremdriftslinje.
- **Historikk** over siste økter. Sletting krever to klikk, så man ikke sletter ved et uhell.
- **Stopper du tidlig**, lagres tiden du faktisk brukte. Økter under 1 minutt lagres ikke.
- **Eksempeldata** med én knapp, slik at det er lett å vise hvordan appen ser ut etter noen uker i bruk.
- Lyd når økta er ferdig, mørkt og lyst tema, og tilpasset mobil.

## Teknologi
- Én fil, `index.html`, med HTML, CSS og JavaScript. Ingen rammeverk og ingen server.
- Data lagres lokalt i nettleseren med `localStorage`. Ingenting sendes noe sted, og ingen personopplysninger forlater maskinen.
- Timeren regner ut gjenværende tid fra et **sluttidspunkt** i stedet for å telle ned ett og ett sekund. Derfor går den riktig selv om fanen ligger i bakgrunnen (der nettleseren bremser JavaScript-timere), og selv om siden lastes på nytt midt i en økt.

## Kjøre appen
**Demo:** https://iitsmokk.github.io/StudieKlokka/

Eller åpne `index.html` direkte i en nettleser.

## Hvordan AI ble brukt
Hele appen er laget med Claude (Anthropic) i samtale på norsk:

1. **Idé og krav.** Jeg beskrev hva jeg ville ha: en timer der jeg velger tid, og der ferdige økter summeres per dag, uke, måned og år.
2. **Første prototype.** AI-en laget en enkel versjon med timer, pause og sammendrag.
3. **Utvidelse.** Jeg ba om å få bygget ut hele appen. Da kom fag per økt, ukegraf, fagfordeling, streak, dagsmål og eksempeldata til, og designet ble gjort ferdig.
4. **Testing.** AI-en skrev automatiske tester (`tests/test_app.py`) som kjører appen i en ekte nettleser (Chromium via Playwright) med en *falsk klokke*. Slik kan en 25-minutters økt testes på under ett sekund.
5. **Feilretting ut fra testene og skjermbildene**, beskrevet under.

## Testing og forbedringer
Testene sjekker 37 ting, blant annet:
- at timer, pause og fortsett teller riktig
- at timeren overlever at siden lastes på nytt
- at ferdige og tidlig stoppede økter lagres med riktig tid, og at økter under 1 min ikke lagres
- at summene for dag, uke, måned og år blir riktige med testdata fordelt over flere uker, måneder og år (uka starter på mandag)
- at «I dag» nullstilles ved midnatt mens uka beholdes
- at nye fag og økter er lagret etter omlasting
- at sletting krever bekreftelse
- at det ikke er horisontal scrolling på mobil (375 px bredde)

**Feil funnet og rettet:**

| Første kjøring | Årsak | Retting |
|---|---|---|
| Testene tok over 5 minutter | Den falske klokka simulerte hvert kvartsekund i 12 timer | Testene hopper fram i tid i stedet |
| Banneret for eksempeldata forsvant ikke | CSS-regelen `display:flex` overstyrte `hidden`-attributtet | La til `[hidden]{display:none!important}` |
| Ukenummer-testen feilet | Teksten vises med store bokstaver | Sammenligner uten å skille store og små bokstaver |
| Store summer ble kuttet («36 t 42 min») | Fire fliser på rad var for smalt | Flisene vises nå i et 2×2-rutenett |
| Datoer i historikken ble kuttet på mobil | Fag og dato lå på samme linje | Datoen vises på egen linje under faget |
| Knappen «Stopp og lagre» brøt over to linjer | Teksten var for lang | Endret til «Stopp» |

Etter rettingene består alle 37 testene. Skjermbilder ligger i `tests/`.

```
python3 -m pip install playwright
python3 -m playwright install chromium
python3 tests/test_app.py
```

## Begrensninger
- Dataene ligger i nettleseren på én enhet og synkroniseres ikke mellom PC og mobil.
- En økt som går over midnatt telles på dagen den startet.
