"""Offline Cubism 3 JSON/reference integrity gate; not a runtime acceptance test."""
import hashlib
import json
from pathlib import Path, PurePosixPath


def validate(model_path):
    model_path = Path(model_path).resolve()
    root = model_path.parent
    errors, files = [], {}

    def reference(value):
        if not isinstance(value, str) or not value:
            raise ValueError(f"Invalid reference: {value!r}")
        rel = PurePosixPath(value)
        if rel.is_absolute() or '..' in rel.parts or any(c in value for c in '\\:%?#'):
            raise ValueError(f"Nonportable reference: {value}")
        target = root.joinpath(*rel.parts)
        if not target.resolve().is_relative_to(root):
            raise ValueError(f"Escaping symlink: {value}")
        current = root
        for part in rel.parts:
            if part not in [p.name for p in current.iterdir()]:
                raise ValueError(f"Missing/case-mismatched reference: {value}")
            current /= part
        data = target.read_bytes()
        if not data:
            raise ValueError(f"Empty reference: {value}")
        files[value] = hashlib.sha256(data).hexdigest()
        if value.endswith('.json'):
            json.loads(data)
        if value.lower().endswith('.png') and not data.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError(f"Invalid PNG signature: {value}")
        return data

    try:
        data = json.loads(model_path.read_bytes())
        if data.get('Version') != 3:
            raise ValueError('Expected Cubism model JSON Version 3; no filename conversion')
        refs = data['FileReferences']
        moc = reference(refs['Moc'])
        if len(moc) < 64 or moc[:4] != b'MOC3':
            raise ValueError('Missing/truncated MOC3 header (Core probe still required)')
        if not isinstance(refs['Textures'], list) or not refs['Textures']:
            raise ValueError('At least one texture required')
        for item in refs['Textures']:
            reference(item)
        for key in ('Physics', 'Pose', 'UserData', 'DisplayInfo'):
            if key in refs:
                reference(refs[key])
        for item in refs.get('Expressions', []):
            reference(item['File'])
        for group in refs.get('Motions', {}).values():
            for item in group:
                reference(item['File'])
                if 'Sound' in item:
                    reference(item['Sound'])
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        errors.append(str(error))
    return {'stage': 'bundle-integrity-only', 'status': 'fail' if errors else 'pass',
            'render_tested': False, 'model_sha256': hashlib.sha256(model_path.read_bytes()).hexdigest()
            if model_path.is_file() else None, 'files_sha256': files, 'errors': errors}
