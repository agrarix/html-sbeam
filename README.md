# SunnyBEAM Kleurgecodeerde HTML-generator

Dit project bevat scripts om een kleurgecodeerde HTML-tabel te genereren die de kWh-productie van zonnepanelen toont, inclusief een automatische jaar-op-jaar vergelijking.

## 📁 Bestanden

- **html-sbeam.py** - Python-script dat:
  - De configuratie inleest vanuit `html-sbeam.rc` (als deze bestaat).
  - Dagelijkse bestanden (`YY-MM-DD.CSV`) verwerkt om maandbestanden (`_YYYY-MM.CSV`) te compileren (als deze nog niet bestaan).
  - De maandelijkse opbrengst berekent op basis van de gecompileerde `_YYYY-MM.CSV` bestanden.
  - Een HTML-tabel genereert met CSS-styling.
  - Elk maandtotaal vergelijkt met dezelfde maand van het voorgaande jaar en automatisch de juiste kleurklasse toekent.
  - Het HTML-bestand opslaat in de opgegeven `OUTPUT_DIR`.
  
- **html-sbeam.rc** - Configuratiebestand met variabelen voor de directories en weergave-instellingen.

## ⚙️ Configuratie (html-sbeam.rc)

Het configuratiebestand gebruikt de `SLEUTEL="waarde"`-syntax. De belangrijkste variabelen zijn:

```bash
INPUT_DIR="Z:\DATA\SBEAM"                            # Locatie van de zonnepaneelgegevens (dagelijkse en maandelijkse CSV's)
OUTPUT_DIR="Z:\WWW\domains\www.agrarix.net\pages\sbeam" # Locatie waar de HTML-pagina moet worden opgeslagen
INDEX_FILE="index.html"                              # Bestandsnaam van de HTML-pagina
VERSION="1.03"                                       # Versie-indicator op de webpagina
FFACE="verdana"                                      # Lettertype voor de pagina
FSIZE="6"                                            # Grootte van de tabeltekst
HOSTNAME="xynix"                                     # Hostnaam getoond in de footer
```

## 🎨 Kleurenschema

- **Groen (`#90EE90`)** - Productie van de huidige maand is **hoger** dan vorig jaar.
- **Oranje (`#FFA500`)** - Productie van de huidige maand is **lager** dan vorig jaar.
- **Lichtblauw (`#ADD8E6`)** - Productie van de huidige maand is **gelijk** aan vorig jaar.
- **Grijs / Wit (`#f0f0f0`)** - Geen gegevens of geen vergelijking met vorig jaar mogelijk.

## 📊 Uitvoer

De gegenereerde HTML is direct te bekijken via de publieke URL:
[https://www.agrarix.net/sbeam/](https://www.agrarix.net/sbeam/)

## 🚀 Gebruik

Voer het script handmatig uit in de terminal:

```powershell
python html-sbeam.py
```

U kunt ook een specifiek configuratiebestand opgeven:

```powershell
python html-sbeam.py pad/naar/config.rc
```

## 📋 Gegevensstroom

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

## 🔧 Berekeningsdetails

Om historische consistentie te garanderen, gebruikt het script de volgende formule voor de maandopbrengst:
`maandopbrengst = int(laatste_totaal) - (int(eerste_totaal) - int(eerste_vandaag))`

Jaartotalen:
- **gr.ttl**: Cumulatieve tellerstand (`E-Total`) aan het einde van het betreffende jaar.
- **Y.ttl**: Jaarlijkse opbrengst (`gr.ttl` van dit jaar minus `gr.ttl` van vorig jaar).
