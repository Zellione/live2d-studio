# Phase 2 results

Prüfdatum: 2026-11-02. **Technischer MVP erfolgreich für die kontrollierte
geometrische Vorlage; allgemeines Anime-Part-Parsing nicht bestanden.**
Ein flaches Bild wird lokal in transparente Kandidatenebenen zerlegt, begrenzt
rekonstruiert, über ein Manifest nach PSD2Live importiert und als PSD/Projekt/
Runtime exportiert. Der neue Export rendert und bewegt sich in der unveränderten
installierten SillyTavern-Erweiterung innerhalb einer frischen Testkopie.

Keine manuelle Bildbearbeitung für den synthetischen Lauf nötig. Keine fremden
Originalbilder, neuen Exportbundles, Rohtranskripte oder Browserframes in Git.
Keine Produktionsinstallation, Treiber-, Kernel- oder System-CUDA-Änderungen.

## Cleanup

Separater Commit `c5d6512`, nach 15 bestehenden Tests und Core-Geometrieprüfung
erstellt und gepusht. Entfernt wurden die ausdrücklich genannten historischen
Phase-1-Zwischenstände und alle Phase-1-Rohbelege aus dem **Index**. Lokale Kopien
blieben erhalten. `final/`, `rig-recipe.json`, Fixture-README und das Phase-0-Bundle
bleiben versioniert. Kein Golden-Fixture wurde ersetzt; keine History umgeschrieben.
Historische Messergebnisse bleiben im Phase-1-Bericht mit Bezug auf `07f56b3`.
Die neue [Artifact-Policy](artifact-policy.md) beschreibt Ausnahmen und Ignore-Regeln.

## Tatsächlich ausgeführte Bildverarbeitung

Pillow 12.0.0, NumPy 2.3.4, SciPy 1.16.3, Python 3.13.15; deterministische
Farbkomponenten und relative Geometrie, Alphakanal/gleichförmiger Randhintergrund,
begrenztes Füllen mit nächster Originalfarbe. Keine ML-Segmentierung, kein SAM,
keine Diffusion, keine extern gehostete Inferenz. Exakte Dependency-Hashes stehen
in `uv.lock`, Lizenzen und Modellbewertung in der [Architektur](phase2-architecture.md).

`prepare`, `inspect`, separater `reconstruct`-Replay, `flatten-fixture`, `evaluate`,
`build`, `mcp-check` und `doctor` sind implementiert. Das versionierte Manifest
prüft Referenzen, Hashes, Bildmodi, Grenzen, Z-Order, Maskenunion und unveränderte
sichtbare Originalpixel. PNG, WebP und JPEG werden eingelesen; verlustfreier
Hintergrundtest, Skalierung/Verschiebung/Farbvariation und Teiltransparenz sind
abgedeckt. JPEG-Decodierung ist kein Nachweis zuverlässiger JPEG-Semantik.

## Synthetischer Benchmark

Die vorhandenen finalen Einzelebenen werden ohne gleichzeitig geschlossene und
offene Augen/Mundformen zusammengesetzt. Die Pipeline erhält ausschließlich
`flat.png`; Ground Truth wird erst anschließend ausgewertet. Ein Test entfernt
die Metadaten vor einem Wiederholungslauf. Keine versteckten Fixture-Koordinaten
oder exakten Farbwerte im Segmentierer.

| Prüfung | Ergebnis |
| --- | --- |
| Canvas / sichtbare Ground-Truth-Teile | 256×300 / 13 |
| Ausgabeschichten | 16: 13 erkannte Kandidaten + 3 generierte Alternativformen |
| Mittlere sichtbare Masken-IoU | **1,00000** |
| Mittlere vollständige Masken-IoU | **0,9364596** |
| Gesicht, Iris, Lider, Brauen, Nase, Mund, Kleidung: vollständige IoU | 1,0 für diese Vorlage |
| Augenweiß links/rechts: vollständige IoU | jeweils **0,9293785** |
| Hals: vollständige IoU | **0,3152174** |
| Veränderte sichtbare Originalpixel / Composite-Pixel | **0 / 0** |
| Unzugeordnete Vordergrundpixel | 0 von 30 244 |
| Markierte rekonstruierte/generierte Pixel | 3910, einschließlich Alternativformen |
| CPU-Einzellauf, Segmentierung / gesamt | etwa 0,013 / 0,068 s; kein statistischer Performancebenchmark |

Sichtbare Masken erfassen vorhandene Pixel zuverlässig **in dieser kontrollierten
Vorlage**. Verdeckte Halskontur und Augenweiß unter den Lidern bleiben teilweise
fehlend. Der volle Maskenscore bewertet das ausdrücklich mit. Ein neues
speicherbegrenztes Replay erzeugte dieselben Layer-Dateihashes und Metadaten wie
der importierte finale Satz; ein neuer Export war dafür nicht erforderlich.

Lokale Belege: `runs/phase2-synthetic/`, `runs/phase2-release-layers/`;
Ground-Truth-Auswertung unter `runs/phase2-final-layers/evaluation.json`.
Die HTML-Vorschau liegt unter `runs/phase2-release-layers/preview/index.html`.

## Realistische Illustration: negativer Semantiktest

Auf Nutzerwunsch wurde [Wikipe-tan face von Kasuga](https://commons.wikimedia.org/wiki/File:Wikipe-tan_face.png)
mit dokumentierter [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)
lokal geladen. Attribution, SHA-256, Quellrevision und Lizenzlink stehen in der
Architektur und im lokalen Provenienzdatensatz. Das unveränderte Original ist
440×440, ein angeschnittenes, geneigtes Gesicht; kein idealer frontaler Bustest.
Getrennte, validierte Ground-Truth-Masken lagen nicht vor: **keine reale IoU angegeben**.

Finaler begrenzter Lauf: **145 250 von 187 018 Vordergrundpixeln (77,7%)** bleiben
`unknown`. Neun erwartete Rolle/Seite-Kombinationen fehlen: Kleidung, Nase, rechte
Iris, beide Wimpern, Brauen und geschlossenen Augen. Das Ausgangsbild enthält
keinen vollständigen Oberkörper; Kleidung ist hier auch kein fairer Parsingtest.
Eine farbige Mundfläche wurde fälschlich als Hals eingeordnet. Die linke Iris
enthält Konturanteile; Gesicht/Haargrenzen sind nicht als verborgene Anatomie
rekonstruiert. Die vorhandenen Klassen sind daher **Kandidaten, keine bestätigten
Erkennungen**. 3595 markierte Füll-/Alternativpixel sind kein Plausibilitätsnachweis.

Die sichtbaren Originalpixel und der Composite bleiben dennoch pixelgleich.
Das ist möglich, weil `unknown` alle Restpixel bewahrt, und demonstriert, weshalb
Pixelgleichheit keine semantische Qualität beweist. Laufzeit etwa 0,068 s
Segmentierung / 0,152 s gesamt auf CPU. Der Build-Gate verweigert diesen Satz
vor einem MCP-Aufruf. Keine Behauptung eines importierten oder animierbaren
realen Charakter-Rigs. Lokale Belege: `runs/phase2-wikipe-tan-release/`.

## PSD2Live und tatsächlicher Browserlauf

Installationsstände wie Phase 0/1: PSD2Live 3.6.7, ST 1.18.0, Extension 0.1.0,
Core 5.0.0, PIXI 6.5.2, Bridge 0.4.0. Authentifizierter verbundener MCP-Pfad:
Create → Overview → Save → PSD → Reopen → Runtime erfolgreich. 16 Quellen werden
zu **18 ArtMeshes, 19 Deformern und 20 Parametern**, einschließlich Standard-
Augen-/Mund-/Kopfparameter. Keine übernommenen Phase-1-Mood-IDs oder Keyforms.
Exportwarnung über normalisierte doppelte Namen bleibt im lokalen Transkript;
stabile Layer-IDs unterscheiden die Ebenen. Importzuordnung separat validiert.

Bundle-Referenzen, MOC-Version 5 und installierte Core bestanden. Core-Geometrie:
Blink links/rechts unabhängig, Mund und Kopf X/Y/Z gebunden, Zwischenwerte
verschieden, Defaults wiederherstellbar. Browsertest am tatsächlichen ST-Modell:

| Pose | Geänderte Canvas-Pixel gegen neutral |
| --- | ---: |
| Linkes / rechtes Auge geschlossen | 4155 / 4154 |
| Beide Augen halb / ganz geschlossen | 7328 / 8309 |
| Mund halb / ganz geöffnet | 1231 / 2798 |
| Kopf X −25 / +25 | 20028 / 20164 |
| Kopf Y −20 / +20 | 23678 / 23838 |
| Kopf Z −20 / +20 | 53079 / 53060 |

Kontrollrauschen 0; alle vier geforderten Modellressourcen HTTP 200, keine
unerwarteten Modell-HTTP-Fehler, keine unbehandelten JS-Ausnahmen. Discovery,
Dropdown, Laden und Reload bestanden. Bilder neutral/halb geschlossen/Kopf X
wurden zusätzlich visuell geprüft: hartkantige geometrische Formen, vereinfachte
Lidzwischenformen und kleine sichtbare Lücken am Hals bei Rotation. Keine
hochwertige Charakteranimation, kein Text-Talk-/Emotionstrigger-Nachweis.
Der 2D-Layer-Composite zeigt den Eingabemund offen; PSD2Live-Default ist Mund zu.
Diese verschiedenen Zustände werden nicht als pixelgleiche Rig-Pose ausgegeben.

Browserbeleg: `runs/phase2-final-browser/`; PSD, `.psd2live`, Runtime, Importprüfung,
Core/Geometrie und MCP-Transkript: `runs/phase2-final-build/`. Das endgültige MOC
wird per Hash in `core.json`/`rig-geometry.json` identifiziert. Browser nutzt
SwiftShader; dies ist kein GPU-Rendering-Benchmark.

## Regression und Hardware

**33 automatisierte Tests bestanden**, einschließlich der bisherigen 15,
unabhängiger Raster-Inferenz, Determinismus, Überschreibschutz, Alphaintegrität,
Rekonstruktion, Referenz-/Symlink-/Hashfehler und MCP-Transportverhalten.
Zusätzlich beide bisherigen Browser-Szenarien erneut bestanden:

- Phase 0: 104 703 türkise Pixel vor/nach Reload; alle erwarteten Ressourcen.
- Phase 1: unverändertes Golden-Fixture; alle zwölf Posen und drei Expressions,
  Idle mit ca. 11,209° Z-Spanne, Blinkminimum nahe null, 20 830 geänderte
  Idle-Stichprobenpixel. Dies sind **neue Phase-2-Regressionsmessungen**, getrennt
  von den historischen Zahlen im Phase-1-Bericht.
- 137 Server-/Extension-Dateien nach den Läufen erneut per Hash verglichen:
  Testkopie und ursprüngliche Installation unverändert. Golden-Fixtures ebenfalls
  unverändert. Testserver und separater Chrome wurden nach der Prüfung beendet.

Belege lokal: `runs/phase2-final-tests.log`, `runs/phase2-regression-phase0/`,
`runs/phase2-regression-phase1/`, `runs/phase2-final-build/isolation.json`.

NVIDIA RTX 5090, 32 607 MiB, Treiber 615.78.08. Optional projektlokal installiert:
**PyTorch 2.9.0+cu128**, CUDA-Wheel 12.8. Tatsächlicher CUDA-Matrixmultiplikationstest
bestanden, Compute Capability 12.0 / `sm_120`, 9 043 968 Bytes Peak-Allokation,
ca. 0,999 s inklusive Erstinitialisierung. Sandboxzugriff scheiterte zunächst;
der freigegebene Lauf außerhalb der Sandbox bestand. Keine neuralen Bildmodelle
geladen, **keine GPU-Bildinferenz behauptet**. Die CPU-Bildläufe belegen 0 GPU-VRAM.

## Offene Grenzen und nächste sinnvolle Arbeit

- Semantische Zuordnung bei echten Illustrationen ist der primäre Engpass:
  zusammenhängende dunkle Konturen, Schattierungen, Haarüberdeckung und Bildbeschnitt.
  Zuerst einen lizenzierten frontalen Benchmark samt Teilmasken erstellen und
  einen Anime-spezifischen Parser/Detektor bewerten. SAM kann danach Masken verfeinern.
- Gesichtsbasis hinter Haaren, Hinterkopf, Haar vorn/hinten, separate Pupillen,
  Mundinnenraum mit Zähnen/Zunge und verborgene Hals-/Haaransätze sind ungelöst.
  Die echte Illustration würde heute korrigierte Masken und nachgezeichnete
  verdeckte Flächen brauchen. Das Automatisierungsziel ist dafür noch nicht erfüllt.
- Generatives Inpainting erst nach geprüfter Semantik mit geschützten sichtbaren
  Pixeln, separaten Masken, festem Seed und visuellem Vergleich evaluieren. Keine
  Aussage über SDXL-Animequalität oder dessen tatsächlichen VRAM-Bedarf.
- Eigenständige CLI-Authentifizierung bleibt offen: realer Read-only-Test liefert
  HTTP 401 ohne `PSD2LIVE_MCP_TOKEN`. Tokenheader, JSON/SSE, Session, Redirectschutz
  und verständliche 401-Fehler sind mit Dummy-Credentials geprüft. Minimal fehlt
  das lokal eingegebene Server-Token für `mcp-check` und anschließend `build`;
  keinerlei Profil-Secrets wurden gelesen. Verbundener MCP-Export ist nachgewiesen.

Vollständige Befehle für Bildstufen/Tokeneingabe: [Architektur](phase2-architecture.md).
Browserwiederholung: frische Testkopie und Chrome wie in [Phase 0](compatibility.md),
Phase-1-Golden-Runtime nach `assets/live2d/phase1`, eigenen Build nach
`assets/live2d/phase2` **innerhalb dieser Kopie** legen. Dann nacheinander
`st_browser_scenario.js`, `phase1_browser_scenario.js`, `phase2_browser_scenario.js`
mit `cdp_smoke.mjs` und neuen lokalen Ergebnisordnern ausführen. Geometrieprüfung
des neuen Bundles: `node scripts/probe_rig.cjs CORE_JS MODEL_MOC3 basic`; ohne
`basic` bleibt die bisherige Phase-1-Mood-Prüfung verpflichtend.

**Stopp nach Phase 2.** Phase 3 und Produktionsautomatisierung wurden nicht begonnen.
