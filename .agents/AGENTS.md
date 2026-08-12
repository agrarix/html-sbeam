# SunnyBEAM Projectrichtlijnen

Dit project verwerkt de dagelijkse zonnepaneelmetingen van SunnyBEAM en publiceert deze op de website.

## Response instructions
Please respond like smart caveman. Cut all filler, keep technical substance.
- Drop articles (a, an, the), filler (just, really, basically, actually).
- Drop pleasantries (sure, certainly, happy to).
- No hedging. Fragments fine. Short synonyms.
- Technical terms stay exact. Code blocks unchanged.
- Pattern: [thing] [action] [reason]. [next step].

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

4. **Documentatie**:
   - Documenteer alle functionele en configuratiewijzigingen eerst in de `README.md` alvorens deze via Git te uploaden.

5. **Referentiebronnen**:
   - De GitHub-organisatie [agrarix](https://github.com/agrarix/) kan (moet) altijd worden geraadpleegd voor referentiecode en context.

6. **Taal**:
   - Schrijf plannen (zoals het implementatieplan), documentatie en communicatie bij voorkeur in het Nederlands.

7. **SSH & Deployment**:
   - Server: `maarten@fabrix` (`192.168.178.40`).
   - Lokale SSH-sleutel: `%USERPROFILE%\.ssh\id_ed25519` (`ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEofRFBlLvMPpWjceKR/7YV/q4h/eDWNkraTvjsBvXvM nl19471@fenestrix`).
   - Projectmap op server: `~/html-sbeam`.
   - Deployment-commando: `ssh -i %USERPROFILE%\.ssh\id_ed25519 -o StrictHostKeyChecking=no maarten@192.168.178.40 "cd ~/html-sbeam && git checkout -- . && git pull"`.

8. **Verificatie na deployment**:
   - Controleer ALTIJD de live website (`https://www.agrarix.net/sbeam/`) na elke deployment via `curl` of `read_url_content`.
   - Verifieer: correcte CSS-versie in `<link>` tag, aanwezigheid van nieuwe HTML-klassen, correcte footer-tekst.
   - Meld pas "klaar" als verificatie geslaagd is.


