# SunnyBEAM Kleurgecodeerde HTML-generator

Dit project bevat een Python-programma om automatisch een kleurgecodeerde HTML-tabel te genereren die de kWh-productie van zonnepanelen toont, gebaseerd op de stijl van [www.agrarix.net/sbeam](https://www.agrarix.net/sbeam/).

Het programmascript (`html-sbeam.py`) is de actieve en volledige vervanging van alle eerdere shell- en hulpscripts. Het haalt de gegevens uit dagbestanden, compileert ze naar maandbestanden, en bouwt de uiteindelijke HTML-pagina.

---

## 📁 Projectstructuur

```
html-sbeam/
├── .agents/
│   └── AGENTS.md          # Projectrichtlijnen
├── html-sbeam.rc          # Configuratiebestand
├── html-sbeam.py          # Python-verwerkingsscript (primair)
└── README.md              # Projectdocumentatie
```

---

## ⚙️ Configuratie (html-sbeam.rc)

Alle instellingen worden gelezen uit `html-sbeam.rc` met de `SLEUTEL="waarde"`-syntax:

| Sleutel | Beschrijving | Standaardwaarde |
|---|---|---|
| `INPUT_DIR` | Locatie van de zonnepaneelgegevens (dagelijkse en maandelijkse CSV's) | `Z:\DATA\SBEAM` |
| `OUTPUT_DIR` | Locatie waar de HTML-pagina en het logbestand moeten worden opgeslagen | `Z:\WWW\domains\www.agrarix.net\pages\sbeam` |
| `INDEX_FILE` | Bestandsnaam van de HTML-pagina | `index.html` |
| `LOG_FILE` | Bestandsnaam van de logging (wordt opgeslagen in de huidige werkmap) | `html-sbeam.log` |
| `VERSION` | Versie-indicator die op de webpagina en in de footer getoond wordt | `1.03` |
| `FFACE` | Lettertype (font-family) voor de webpagina | `verdana` |
| `FSIZE` | Lettergrootte (font-size) van de tabeltekst | `6` |
| `HOSTNAME` | Hostnaam getoond in de voettekst/footer | `xynix` |
| `ICON` | Bestandsnaam van het website-icoon / favicon | `solar_pingu.jpg` |
| `SIZE_MOBILE` | Lettergrootte (font-size) van de tabel op mobiele apparaten | `0.9em` |
| `SIZE_DESKTOP` | Lettergrootte (font-size) van de tabel op desktop/grote schermen | `1.25em` |
| `TITLE` | Hoofdkop en paginatitel van de website | `Zonnepanelen opbrengst op CHL14 (mbv SunnyBEAM)` |
| `FOOTER` | De voettekst onderaan de pagina (ondersteunt `${PGM}`, `${VER}`, `${DATE}`, `${TIME}`, `${BUILD_TIME}`, `${PROCESS_TIME}`, `${HOSTNAME}`) | `${PROCESS_TIME} ${PGM} (${BUILD_TIME}) v${VER} at ${HOSTNAME}` |


*Tip: Omgevingsvariabelen (zoals `$HOME` of `%USERPROFILE%`) en backslashes (`\`) worden automatisch geëxpandeerd en genormaliseerd.*

### Linux / OS-specifieke keuzes

Net als bij `html-album` detecteert het script op welk besturingssysteem het draait en past daarop zijn gedrag aan:
* **Configuratie**: Op Linux wordt gezocht naar `~/etc/html-sbeam.rc` (indien een relatief configuratiepad is opgegeven). Op Windows in de map van het script.
* **Logbestand**: Als `LOG_FILE` een relatieve naam is, wordt het logbestand op Linux opgeslagen in `~/log/html-sbeam.log`. Op Windows wordt het opgeslagen in de map van het script.
* **Paden**: Paden voor `INPUT_DIR` en `OUTPUT_DIR` worden automatisch genormaliseerd (backslashes worden forward slashes op Linux) en omgevingsvariabelen worden geëxpandeerd.


---

## 🚀 Gebruik

Voer het script uit in de terminal:

```powershell
python html-sbeam.py
```

### Opties en Argumenten

Je kunt optioneel een specifiek configuratiebestand opgeven, help opvragen, of filteren op specifieke jaren/bestanden:

```powershell
# Gebruik een specifiek configuratiebestand in plaats van html-sbeam.rc
python html-sbeam.py test.rc
# of: python html-sbeam.py -c test.rc

# Alleen dagbestanden naar maandbestanden compileren (geen HTML genereren)
python html-sbeam.py -d
# of: python html-sbeam.py --days

# Alleen HTML-pagina genereren op basis van bestaande maandbestanden (geen compilatie)
python html-sbeam.py -p
# of: python html-sbeam.py --proc

# Filteren om alleen bestanden te verwerken die '2026' bevatten
python html-sbeam.py -f 2026
# of: python html-sbeam.py --filter 2026

# Toon de help-informatie (werkt ook met -h, /help of /?)
python html-sbeam.py --help

# Toon de versie- en build-informatie (werkt ook met --version)
python html-sbeam.py -V
```

---

## 🎨 Kleurenschema

- **Groen (`#90EE90`)** - Productie van de huidige maand is **hoger** dan vorig jaar.
- **Oranje (`#FFA500`)** - Productie van de huidige maand is **lager** dan vorig jaar.
- **Lichtblauw (`#ADD8E6`)** - Productie van de huidige maand is **gelijk** aan vorig jaar.
- **Roze (`#FFC0CB`)** - Onvolledige maand (minder dan 25 dagen met metingen).
- **Grijs / Wit (`#f0f0f0`)** - Geen gegevens of geen vergelijking met vorig jaar mogelijk.

---

## 📈 Interactieve Grafieken

Er worden twee lijngrafieken onder de tabel gegenereerd via Chart.js:
1. **Maandelijkse Opbrengst**: Toont de opbrengst per individuele maand per jaar. In deze grafiek is ook een zwarte gestreepte lijn ("Gemiddelde") toegevoegd die het historische gemiddelde per maand (berekend over alle volledige maanden) toont.
2. **Cumulatieve Opbrengst**: Toont de opgetelde (cumulatieve) opbrengst van januari tot december voor elk jaar. In deze grafiek is tevens een zwarte gestreepte lijn ("Gemiddelde") toegevoegd die de cumulatieve opbouw van het historisch gemiddelde toont.

Beide grafieken zijn interactief:
- **Enkel jaar tonen**: Klik op een jaartal in de legenda aan de rechterkant om uitsluitend dat jaar te tonen en alle andere jaren te verbergen. De lijn "Gemiddelde" blijft hierbij standaard wel zichtbaar om vergelijking mogelijk te maken.
- **Gemiddelde in-/uitschakelen**: Klik op "Gemiddelde" in de legenda om uitsluitend deze lijn te verbergen of te tonen.
- **Jaren toevoegen/verwijderen (Multi-selectie)**: Houd de `Ctrl`-toets ingedrukt (of `Cmd` op macOS) en klik op een jaartal in de legenda om dat specifieke jaar toe te voegen aan of te verwijderen uit de actieve selectie.
- **Alle jaren herstellen**: Klik zonder `Ctrl` nogmaals op het actieve (enige getoonde) jaartal in de legenda om alle jaren en de gemiddelde lijn weer zichtbaar te maken.

---

## 📋 Gegevensstroom

De data- en hardwareketen is als volgt opgebouwd:

```
SB1200 (omvormer) 
    ↓ (Bluetooth)
SunnyBEAM (uitleesunit)
    ↓ (USB)
RaspberryPi
    ↓ (Ethernet)
NAS (opslag databestanden Z:\DATA\SBEAM)
    ↓ (Ethernet)
PC / Linux (met html-sbeam.py verwerking)
    ↓
NAS (opslag index.html & html-sbeam.css)
    ↓
Linux-webserver (publiceert op www.agrarix.net/sbeam)
```

### Logbestandenverwerking:
```
Z:\DATA\SBEAM\YY-MM-DD.CSV (Dagelijkse logs van de Raspberry Pi)
    ↓
(gecompileerd door html-sbeam.py naar)
    ↓
Z:\DATA\SBEAM\_YYYY-MM.CSV (Gecompileerde maandlogs met dagelijkse rijen)
    ↓
python html-sbeam.py (verwerkt Y-o-Y vergelijking en jaartotalen op basis van html-sbeam.rc)
    ↓
Z:\WWW\domains\www.agrarix.net\pages\sbeam\index.html (HTML & CSS uitvoer)
```

---

## 🔧 Berekeningsdetails

Om historische consistentie te garanderen, gebruikt het script de volgende formule voor de maandopbrengst:
`maandopbrengst = int(laatste_totaal) - (int(eerste_totaal) - int(eerste_vandaag))`

Jaartotalen:
- **Gr.ttl**: Cumulatieve tellerstand (`E-Total`) aan het einde van het betreffende jaar.
- **Y.ttl**: Jaarlijkse opbrengst (`Gr.ttl` van dit jaar minus `Gr.ttl` van het dichtstbijzijnde voorgaande jaar met gegevens).

---

## 🏷️ Footer

Onderaan de pagina wordt een voettekst (footer) getoond. Het sjabloon hiervoor wordt uit de configuratie (`FOOTER`) gelezen en ondersteunt de volgende dynamische variabelen:
- `${PGM}`: De programmanaam (`html-sbeam.py`).
- `${VER}` (of `${VERSION}`): Het versienummer (`VERSION`).
- `${DATE}`: De huidige datum (`dd-mm-jjjj`).
- `${TIME}`: De huidige tijd (`uu:mm:ss`).
- `${BUILD_TIME}`: De dynamisch opgehaalde wijzigingstijd van het scriptbestand.
- `${PROCESS_TIME}`: De datum/tijd van de verwerking.
- `${HOSTNAME}`: De hostnaam (`HOSTNAME`).

---

## 📝 Wijzigingsgeschiedenis

- **06-07-2026**: 
  - De standaardtitel (`TITLE`) is aangepast naar `"Zonnepanelen opbrengst op CHL14 (mbv SunnyBEAM)"`.
  - De subkop `"Numbers in kWh"` boven de tabel is vertaald naar het Nederlands (`"Waarden in kWh"`).
  - Controle toegevoegd of `YYYY-MM.CSV` (ruwe maandelijkse data) nieuwer is dan `_YYYY-MM.CSV` (gecompileerde maandlog). Als dat zo is, wordt `_YYYY-MM.CSV` opnieuw opgebouwd aan de hand van de dagbestanden (`YY-MM-DD.CSV`).
  - Onvolledige maanden (minder dan 25 dagen met metingen) worden nu in het roze (Pink) weergegeven in de tabel en in de eerste grafiek.
  - Een zwarte gestreepte gemiddelde lijn ("Gemiddelde") toegevoegd aan de grafieken "Grafiek per Jaar" en "Cumulatieve Opbrengst per Jaar" (berekend op basis van alle jaren, met uitsluiting van onvolledige maanden).





