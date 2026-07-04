# SunnyBEAM Projectrichtlijnen

Dit project verwerkt de dagelijkse zonnepaneelmetingen van SunnyBEAM en publiceert deze op de website.

## Belangrijke Richtlijnen

1. **Bestandsnamen & Locaties**:
   - De ruwe maandelijkse data staat in `Z:\DATA\SBEAM\YYYY-MM.CSV` (bijvoorbeeld `2026-06.CSV`).
   - Het verwerkingsprogramma heet `html-sbeam.py`.
   - Het configuratiebestand heet `html-sbeam.rc` en staat in dezelfde map.
   - De HTML-uitvoer moet worden opgeslagen op `Z:\WWW\domains\www.agrarix.net\pages\sbeam\index.html` (beide mappen zijn configureerbaar via `html-sbeam.rc`).

2. **Berekeningsmethode**:
   - Gebruik altijd de historische afrondingsformule om consistentie met historische data te garanderen:
     `maandopbrengst = int(laatste_totaal) - (int(eerste_totaal) - int(eerste_vandaag))`
   - Jaartotalen:
     - `gr.ttl` is de cumulatieve tellerstand (`E-Total`) aan het einde van het jaar.
     - `Y.ttl` is de opbrengst van dat jaar, berekend als het verschil tussen de `gr.ttl` van dit jaar en die van het vorige jaar.

3. **Testen**:
   - Het Python-script `html-sbeam.py` hoeft NIET getest te worden door de AI-assistent.
