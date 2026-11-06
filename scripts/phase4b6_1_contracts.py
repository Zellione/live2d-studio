"""Bind independent saved-project geometry inspections to exact runtime exports."""
import json
from pathlib import Path
from live2d_studio.manifest import digest,write_json
ROOT=Path(__file__).resolve().parents[1]
for label,inspection,model in [
 ('codel','runs/phase4b6-1-diagnosis/mouth-project-host/inspection.json','runs/phase4b5-codel-mouths/export/runtime/Generated_artwork.model3.json'),
 ('sara','runs/phase4b6-1-diagnosis/sara-project/inspection.json','runs/phase4b4-1-sara-v4/export/runtime/Generated_artwork.model3.json')]:
 i=json.loads((ROOT/inspection).read_text());m=ROOT/model;refs=json.loads(m.read_text())['FileReferences']
 write_json(ROOT/f'runs/phase4b6-1-diagnosis/{label}-contract.json',dict(details=i['details'],project_sha256=i['project_sha256'],moc_sha256=digest(m.parent/refs['Moc'])))
