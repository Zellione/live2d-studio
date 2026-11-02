# Phase 0: PSD2Live → SillyTavern compatibility

Prüfdatum: 2026-11-02. **Phase 0 bestanden für die geometrische Test-Fixture:
PSD2Live-Export → Modellsuche → installierte Live2D-Erweiterung → sichtbares
Browser-Rendering und erneutes Laden erfolgreich.** Dies ist keine Freigabe
eines vollständigen Charakter-Rigs oder aller möglichen PSD2Live-Exporte.
Die vorhandene SillyTavern-Installation wurde ausschließlich gelesen.
Keine Software installiert, keine Produktionsassets oder Einstellungen geändert.

## Lokaler Bestand und Versionen

| Komponente | Gefundener Stand |
| --- | --- |
| SillyTavern | `/home/zelli/tools/ai/SillyTavern`, package 1.18.0, Commit `8172dcd0ee672d3cd9a5e5f7af134f91a45cd2b8`, AGPL-3.0 |
| Erweiterung | `data/default-user/extensions/Extension-Live2d`, Manifest 0.1.0, Commit `d1801d36a32ace9451cf6377c005a7a64292fc39`, GPL-3.0; sauberer Git-Status bei Prüfung |
| Modellverzeichnis | `data/default-user/assets/live2d`; keine lokalen Testmodelle gefunden |
| PSD2Live | `/home/zelli/.local/opt/psd2live/v3.6.7/PSD2Live`, Haupt-JAR 3.6.7; GPL-3.0 laut Upstream |
| MCP | Verbindung erfolgreich, anfänglich kein Projekt geöffnet; nur Fixture-Erstellung/-Export für Phase 0 ausgeführt |
| Cubism Core | installierte `lib/live2dcubismcore.min.js`, **5.0.0**, numerisch `83886080`, höchste MOC-Version `5` |
| Weitere Runtime | `live2d.min.js` für ältere Modelle; `pixi.min.js` **6.5.2** (MIT); `index.min.js` meldet **0.4.0**, enthält Cubism2/4-ModelSettings |
| Testwerkzeuge | uv 0.13.6, Node 24.20.0, Python-Standardbibliothek; keine zusätzlichen Python-Pakete |
| Browser | vorhandener Google Chrome 156.0.8078.79 (proprietäre Chrome-Lizenz; nicht weiterverteilt), separates Profil, headless, ANGLE SwiftShader |

Exakte Dateihashes: [installation.json](evidence/phase0/installation.json).
Das installierte Bridge-Bundle ist über seinen Hash gepinnt; die eingebettete
Versionsnummer allein identifiziert mögliche lokale/upstream Anpassungen nicht.
Für `live2d.min.js` und Bridge/Extra wurde keine separate Paket-Lizenzmetadatei
ermittelt; keine eigenständige Weiterverteilung dieser Dateien vorgenommen.
Cubism Core trägt ausdrücklich eine proprietäre Live2D-Lizenz, siehe Dateikopf:
[Live2D-Lizenz](https://www.live2d.com/eula/live2d-proprietary-software-license-agreement_en.html).
Kostenlose lokale Ausführung bedeutet hier nicht, dass jede Runtime Open Source ist.

Gesucht wurde in den Projekt-/Tool-Verzeichnissen unter `/data`,
`/home/zelli/tools`, Downloads, Documents, Pictures, Projects/projects sowie
der PSD2Live-Installation. Kein vorhandenes `.moc3`-/`.model3.json`-Testmodell,
PSD oder `.psd2live`-Projekt gefunden. Keine privaten Chats/Schlüssel gelesen.
Die Suche ist keine Aussage über alle Datenträger oder Container.

## Tatsächlicher Ladepfad

Die [ST-Dokumentation](https://docs.sillytavern.app/extensions/live2d/) nennt
`.model.json`. Der installierte Server prüft jedoch in
`src/endpoints/assets.js:130` und `:348` nur
`file.includes('model') && file.endsWith('.json')`. Damit wird auch
`Generated_artwork.model3.json` gefunden. Die allgemeine Assetsuche ist rekursiv;
die charakterspezifische Suche untersucht Dateien innerhalb der Modell-Unterordner.

`constants.js:59` lädt Core, alte Live2D-Runtime, PIXI, Bridge und Extra in dieser
Reihenfolge. `live2d.js:280–282` ruft `PIXI.live2d.Live2DModel.from(model_path)`
auf (zunächst mit Erweiterungsoptionen, danach als Fallback ohne Optionen).
`ui.js` bezieht Modellpfade aus der Assets-API. Die Galerie behandelt beide
JSON-Endungen ausdrücklich. Ein Discovery-Adapter ist nach diesem Befund unnötig.

`.model.json`/`.moc` und `.model3.json`/`.moc3` sind unterschiedliche
Schemas/Binärfamilien. **Nicht umbenennen.** Eine akzeptierte JSON-Endung
beweist weder gültiges MOC noch unterstützte MOC-Version oder Rendering.

| Prüfung | Ergebnis / Grenze |
| --- | --- |
| Cubism 2 `.model.json`/`.moc` | Discovery und Runtime-Code vorhanden; kein reales Vergleichsmodell getestet |
| Cubism 3+ `.model3.json` | Discovery laut installiertem Code vorhanden; JSON-Schema Version 3 validiert |
| PSD2Live 3.6.7 `.moc3` | Echter Export: MOC-Version 5; installierte Core erzeugt Modell, 1 Drawable, Update erfolgreich |
| Neuere/andere Exportoptionen | Nicht pauschal freigegeben; gegen exakt installierte Core prüfen |
| Browser-Rendering mit installierter Bridge | Bestanden innerhalb der vollständigen Erweiterung; separater Runtime-Harness nicht zusätzlich ausgeführt |
| Tatsächliche SillyTavern-Oberfläche | Bestanden in isolierter Kopie der installierten Dateien; Produktionsinstanz unangetastet |

## Testmodell und Belege

`tests/fixtures/phase0/` enthält eine selbst erzeugte türkise 64×64-Farbfläche,
`tile.psd`, `tile.psd2live` und den vollständigen PSD2Live-Export.
Die [Fixture-Provenienz](../tests/fixtures/phase0/README.md) beschreibt Erstellung
und MCP-Reproduktion. Keine fremden Charakterrechte oder Modell-Downloads nötig.

- [Export samt Warnungen](evidence/phase0/export.json): fehlende Gesichts-, Augen-
  und Mundsemantik. Das Modell ist ausdrücklich kein funktionierender Charakter-Rig.
- [Referenzprüfung](evidence/phase0/integrity.json): bestanden, Dateihashes erfasst.
- [Core-Ladetest](evidence/phase0/core.json): bestanden; **kein Rendering-Nachweis**.
- [Automatisierte Tests](evidence/phase0/tests.log): zehn Tests bestanden.
- [End-to-End-Bericht](evidence/phase0/st-browser/result.json): Modellsuche und
  Dropdown, Parameterzuordnung, erstes Rendering, Reload, Expression-/Motion-Laden.
- [Browserprotokoll](evidence/phase0/st-browser/browser-events.json): bereinigte
  Konsolenausgaben und HTTP-Statuscodes, ohne Cookies/Request-Header.
- [Screenshot](evidence/phase0/st-browser/screenshot.png): türkise Fixture links
  neben dem Chat, Testcharakter „Phase0 Tile“.
- [Isolation](evidence/phase0/isolation.json): 137 Server-/Extension-Dateien nach
  dem Test erneut verglichen; Testkopie und Installation weiterhin identisch.

Der finale Lauf zählt 104704 türkise Canvas-Pixel beim ersten Rendering und
104703 nach Reload (animationsbedingte Abweichung). Alle neun erwarteten
angeforderten Modellressourcen lieferten HTTP 200, keine unerwarteten
Modell-HTTP-Fehler und keine unbehandelten JavaScript-Ausnahmen.
Smile, Sad, Angry und Surprised wurden über `playExpression`, Nod über
`playMotion` der unveränderten Erweiterung aufgerufen. Dateiladen und
Ausführbarkeit sind damit geprüft, sichtbare Mimik ist es nicht.

Beobachtete Einschränkungen: Der optionale Abruf `sillytavern_settings.json`
liefert 404; die Erweiterung verwendet ihre Defaults. Beim Zerstören des
temporären UI-Vorschaumodells kann eine laufende Idle-Motion-Anfrage mit
`Aborted` enden (`loadModelUi` → `destroy`); das anschließend tatsächlich
angezeigte Modell lädt die Idle-Datei erfolgreich. Keine Runtime-Anpassung nötig.
Bei Defaultposition lag die Fixture hinter dem undurchsichtigen Chatpanel;
reguläre Modell-Einstellungen `scale=0.4`, `x=-75`, `y=0` machen sie links sichtbar.
Software-WebGL belegt keine RTX-5090-/Wayland-Leistung.

Die Core-Parameter enthalten `ParamAngleX/Y/Z`, `ParamBodyAngleX`, `ParamBreath`,
`ParamEyeBallX/Y`, `ParamMouthOpenY`, `ParamEyeLOpen/ROpen`.
Die Erweiterung nutzt diese Cubism-IDs bzw. alte `PARAM_*`-Alternativen
(`constants.js`, `utils.js`). `playTalk` verlangt `addParameterValueById`.
Vorhandene IDs beweisen keine gebundenen sichtbaren Augen/Mundformen.

## Reproduzierbare Prüfungen

Aus dem Projektverzeichnis, zsh-sicher, ohne Netzwerk/Installation:

```bash
export UV_CACHE_DIR="$PWD/.cache/uv"
uv run --no-project --no-managed-python --offline python -m unittest discover -s tests -v
uv run --no-project --no-managed-python --offline python scripts/validate_bundle.py \
  tests/fixtures/phase0/export/Generated_artwork.model3.json
node scripts/probe_core.cjs \
  /home/zelli/tools/ai/SillyTavern/data/default-user/extensions/Extension-Live2d/lib/live2dcubismcore.min.js \
  tests/fixtures/phase0/export/Generated_artwork.moc3
```

Beide CLI-Prüfungen liefern JSON und Exitcode 0 bei Erfolg, sonst ungleich 0.
Validator: relative lokale Referenzen, Groß-/Kleinschreibung, Symlink-Ausbruch,
leere/fehlende Dateien, MOC3-Header, Texturen, Motion-/Expression-/Physics-/Pose-/
UserData-/DisplayInfo-JSON und Motion-Sounds. PNG-Signatur wird geprüft, keine
vollständige Bilddecodierung oder vollständige Cubism-Schemavalidierung.
Binäre Semantik prüft die installierte Core; erwartete MVP-IDs werden dort geprüft.

Für den separat vorbereiteten Browser-Test:

```bash
uv run --no-project --no-managed-python --offline python scripts/runtime_smoke.py \
  --extension /home/zelli/tools/ai/SillyTavern/data/default-user/extensions/Extension-Live2d \
  --model tests/fixtures/phase0/export/Generated_artwork.model3.json
```

Für den optionalen Einzel-Runtime-Test `http://127.0.0.1:8765/` öffnen.
Der Server bindet nur Loopback und stellt ausgewählte Bibliotheken sowie das
Fixture-Bundle lesend bereit. Keine Benutzerprofile/Chats oder ST-Einstellungen.
Der Test verwendet den installierten unveränderten Bibliotheksstapel, prüft
Laden und nichttransparente Pixel und zeigt einen JSON-Bericht an. Diesen über
„Download report“ sichern; zusätzlich Screenshot und Browserkonsole unter
`docs/evidence/phase0/` ablegen. Server mit Ctrl-C stoppen.
**Auch ein erfolgreicher Harness ist kein Test der vollständigen Erweiterung.**

## Vollständigen SillyTavern-Test wiederholen

Der Nutzer hat den isolierten Testlauf ausdrücklich freigegeben. Die Testkopie
unter `.cache/phase0-st` besitzt eigene Abhängigkeiten (keine Symlinks zur
Installation), Konfiguration und Userdaten. Automatische Erweiterungsupdates,
Modell-Downloads, Server-Plugins und automatischer Browserstart sind deaktiviert.
Der Testtreiber verwendet Node-eigenes CDP/WebSocket; keine Browserpakete installiert.

In drei Terminals aus dem Projektverzeichnis ausführen. Für eine komplett neue
Wiederholung frische Ziel-/Profil-/Ergebnisnamen wählen, z. B. die folgenden
`-repeat`-Namen. Bereits belegte Ports zuerst freigeben oder konsistent ändern.

```bash
# 1. Isolierte Kopie erstellen (verweigert vorhandenes Ziel)
export UV_CACHE_DIR="$PWD/.cache/uv"
uv run --no-project --no-managed-python --offline python scripts/prepare_st_smoke.py \
  --source /home/zelli/tools/ai/SillyTavern \
  --extension /home/zelli/tools/ai/SillyTavern/data/default-user/extensions/Extension-Live2d \
  --destination .cache/phase0-st-repeat
cd .cache/phase0-st-repeat
node server.js --listen false --port 8766 --browserLaunchEnabled false
```

```bash
# 2. Vorhandenen Browser mit eigenem Profil starten
/opt/google/chrome/chrome --headless=new \
  --user-data-dir="$PWD/.cache/phase0-chrome-repeat" \
  --remote-debugging-address=127.0.0.1 --remote-debugging-port=9227 \
  --no-first-run --no-default-browser-check --disable-background-networking \
  --disable-component-update --disable-sync --enable-unsafe-swiftshader \
  --use-angle=swiftshader --window-size=1280,900 about:blank
```

```bash
# 3. Nach Serverstart den End-to-End-Test ausführen
node scripts/cdp_smoke.mjs http://127.0.0.1:9227 http://127.0.0.1:8766/ \
  scripts/st_browser_scenario.js docs/evidence/phase0/st-browser-repeat
```

Der Szenariotest erledigt Onboarding, Testcharakter-Erstellung, Charakterauswahl,
die tatsächliche Assets-API-Abfrage und Auswahl in den Extension-Dropdowns.
Er ruft die originalen UI-Handler, Expression-/Motion-Funktionen und
`loadLive2d` auf. Weder Loader noch Runtime werden ersetzt oder gemockt.
Der Treiber liefert Exitcode 0 nur bei Szenarioerfolg sowie erfolgreichen
erwarteten Ressourcen und ohne unbehandelte Ausnahmen. JSON, Screenshot und
bereinigte Browserereignisse landen im gewählten Ergebnisverzeichnis.
Nur der optionale Settings-404 ist zugelassen; Abbrüche beim Vorschau-Cleanup
werden im Protokoll erhalten. Anschließend Browser und Server mit Ctrl-C in
ihren Terminals beenden. Bei Automatisierung Server-/Browserprozesse ebenfalls
gezielt beenden; niemals die Produktionsinstanz stoppen.
Die für diesen Bericht gestarteten Testprozesse wurden nach Abschluss beendet.

Browser-/Server-Sandboxfreigaben können lokal nötig sein: der erste Serverstart
und die erste CDP-Verbindung wurden hier mit `EPERM` blockiert; die gezielten
freigegebenen Wiederholungen waren erfolgreich.

Es fehlt derzeit kein kostenpflichtiges Werkzeug und kein Testmodell mehr.
Ein aussagekräftiges Charaktermodell wird später für sichtbares Blinzeln,
Text-Talk und Emotionstrigger benötigt; die Farbfläche kann diese Tests nicht
ersetzen. Kein Adapter, Dateiumbenennen oder Runtime-Austausch ist für diese
geprüfte Kombination erforderlich. Phase 1 und die Bild-/Rigging-Pipeline
wurden nicht begonnen.

Upstream zur Herkunft: [Extension-Live2d](https://github.com/SillyTavern/Extension-Live2d),
[PSD2Live](https://github.com/tsunehimatoi/psd2live). Lokale Befunde und ausgeführte
Tests, nicht diese Dokumentationslinks, begründen die obigen Teilergebnisse.
