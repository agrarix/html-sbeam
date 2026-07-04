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
| `SIZE_MOBILE` | Lettergrootte (font-size) van de tabel op mobiele apparaten | `0.9em` |
| `SIZE_DESKTOP` | Lettergrootte (font-size) van de tabel op desktop/grote schermen | `1.25em` |
| `TITLE` | Hoofdkop en paginatitel van de website | `SunnyBEAM DATA (van de zonnepanelen op CHL14)` |

*Tip: Gebruik forward slashes (`/`) of dubbele backslashes (`\\`) in paden.*

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
- **Grijs / Wit (`#f0f0f0`)** - Geen gegevens of geen vergelijking met vorig jaar mogelijk.

---

## 📈 Interactieve Grafiek

De lijngrafiek onder de tabel is interactief dankzij Chart.js:
- **Enkel jaar tonen**: Klik op een jaartal in de legenda aan de rechterkant om uitsluitend dat jaar te tonen en alle andere jaren te verbergen.
- **Jaren toevoegen/verwijderen (Multi-selectie)**: Houd de `Ctrl`-toets ingedrukt (of `Cmd` op macOS) en klik op een jaartal in de legenda om dat specifieke jaar toe te voegen aan of te verwijderen uit de actieve selectie.
- **Alle jaren herstellen**: Klik zonder `Ctrl` nogmaals op het actieve (enige getoonde) jaartal in de legenda om alle jaren weer zichtbaar te maken.

---

## 📋 Gegevensstroom

De SBEAM-gegevens worden als volgt aangeleverd:
- De **SB1200** omvormer stelt de data via **Bluetooth** beschikbaar aan de **SunnyBEAM** uitleesunit.
- Een **Raspberry Pi** staat via een **USB-verbinding** in contact met de SunnyBEAM om de dagelijkse logs uit te lezen en op te slaan in de datamap (`Z:\DATA\SBEAM`).

```
Z:\DATA\SBEAM\YY-MM-DD.CSV (Dagelijkse logs)
    ↓
(gecompileerd door html-sbeam.py naar)
    ↓
Z:\DATA\SBEAM\_YYYY-MM.CSV (Gecompileerde maandlogs met dagelijkse rijen)
    ↓
python html-sbeam.py (leest html-sbeam.rc in voor instellingen)
    ↓ (leest _YYYY-MM.CSV, berekent Y-o-Y vergelijking en jaartotalen, genereert HTML)
Z:\WWW\domains\www.agrarix.net\pages\sbeam\index.html
```

---

## 🔧 Berekeningsdetails

Om historische consistentie te garanderen, gebruikt het script de volgende formule voor de maandopbrengst:
`maandopbrengst = int(laatste_totaal) - (int(eerste_totaal) - int(eerste_vandaag))`

Jaartotalen:
- **gr.ttl**: Cumulatieve tellerstand (`E-Total`) aan het einde van het betreffende jaar.
- **Y.ttl**: Jaarlijkse opbrengst (`gr.ttl` van dit jaar minus `gr.ttl` van het dichtstbijzijnde voorgaande jaar met gegevens).
