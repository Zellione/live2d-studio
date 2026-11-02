"""Read-only production audit. No installer, writes, service calls or HTTP requests.

Only public code, Live2D asset trees and a projection of settings.json are read.
Unknown settings values are lexically skipped without decoding/materializing them.
Character names and model preferences are reduced to counts before reporting.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

from .packaging import REPO, EXT, CORE, policy, verify, core_probe, digest, files, safe_tree
from .deployment import adapter_bytes, ancestors

NAME = 'girl2-phase3-portrait-v1'
MODEL_URL = f'/assets/live2d/{NAME}/Generated_artwork.model3.json'
SCALAR = 'scalar'
# Only establish whether each character/model record exists. Its custom fields
# (including click messages and expression labels) need not be decoded at all.
MODEL_PREFS = {}
SETTINGS_SCHEMA = {'extension_settings': {
    'api': SCALAR,
    'disabledExtensions': {'[]': SCALAR},
    'expressions': {'api': SCALAR},
    'live2d': {**{k: SCALAR for k in ('enabled', 'followCursor', 'force_loop', 'force_animation', 'autoSendInteraction')},
               'characterModelMapping': {'*': SCALAR},
               'characterModelsSettings': {'*': {'*': MODEL_PREFS}}}}}


class Projection:
    """Small bounded streaming JSON projection; errors never include input text."""
    def __init__(self, stream):
        self.stream = stream
        self.c = stream.read(1)

    def step(self):
        self.c = self.stream.read(1)

    def space(self):
        while self.c and self.c.isspace(): self.step()

    def expect(self, value):
        if self.c != value: raise ValueError('Invalid settings JSON structure')
        self.step(); self.space()

    def string(self, keep):
        if self.c != '"': raise ValueError('Invalid settings JSON string')
        buf = ['"'] if keep else None
        self.step()
        while self.c:
            c = self.c
            if keep: buf.append(c)
            self.step()
            if c == '"':
                if keep:
                    try: return json.loads(''.join(buf))
                    except ValueError: raise ValueError('Invalid selected settings string') from None
                return None
            if c == '\\':
                if not self.c: break
                if keep: buf.append(self.c)
                self.step()
            if keep and len(buf) > 100000: raise ValueError('Selected settings field too large')
        raise ValueError('Truncated settings JSON')

    def value(self, schema, depth=0):
        if depth > 80: raise ValueError('Settings nesting limit exceeded')
        self.space()
        if isinstance(schema, dict) and self.c != ('[' if '[]' in schema else '{'):
            raise ValueError('Unexpected selected settings structure')
        if self.c == '{':
            selected = isinstance(schema, dict)
            result = {} if selected else None
            seen = set()
            self.step(); self.space()
            if self.c != '}':
                while True:
                    key = self.string(selected)
                    self.space(); self.expect(':')
                    child = schema.get(key, schema.get('*')) if selected else None
                    v = self.value(child, depth+1)
                    if child is not None:
                        if key in seen: raise ValueError('Duplicate selected settings key')
                        seen.add(key); result[key] = v
                    self.space()
                    if self.c != ',': break
                    self.step(); self.space()
            self.expect('}')
            if schema == SCALAR: raise ValueError('Expected scalar preference')
            return result
        if self.c == '[':
            child = schema.get('[]') if isinstance(schema, dict) else None
            result = [] if child else None
            self.step(); self.space()
            if self.c != ']':
                while True:
                    v = self.value(child, depth+1)
                    if child: result.append(v)
                    self.space()
                    if self.c != ',': break
                    self.step(); self.space()
            self.expect(']')
            if schema == SCALAR: raise ValueError('Expected scalar preference')
            return result
        if self.c == '"':
            return self.string(schema == SCALAR)
        buf = [] if schema == SCALAR else None
        consumed = False
        while self.c and self.c not in ',]} \t\n\r':
            if buf is not None: buf.append(self.c)
            consumed = True; self.step()
        if not consumed: raise ValueError('Invalid settings JSON value')
        if buf is not None:
            try: return json.loads(''.join(buf))
            except ValueError: raise ValueError('Invalid selected scalar preference') from None
        return None

    def read(self, schema):
        result = self.value(schema)
        self.space()
        if self.c: raise ValueError('Trailing settings data')
        return result


def summarize_settings(stream, model_url=MODEL_URL):
    data = Projection(stream).read(SETTINGS_SCHEMA)
    ext = data.get('extension_settings', {})
    live = ext.get('live2d', {})
    mapping = live.get('characterModelMapping', {})
    configured = live.get('characterModelsSettings', {})
    normalize = lambda s: '/' + s.lstrip('/') if isinstance(s, str) else None
    target = [v for models in configured.values() for key, v in models.items() if normalize(key) == model_url]
    flags = {k: v for k, v in live.items() if k not in {'characterModelMapping', 'characterModelsSettings'}
             and (isinstance(v, bool) or v is None)}
    return dict(live2d_settings_present='live2d' in ext, flags=flags,
        extension_disabled='third-party/Extension-Live2d' in ext.get('disabledExtensions', []),
        mapped_characters=len(mapping), configured_characters=len(configured),
        configured_character_model_pairs=sum(len(v) for v in configured.values()),
        proposed_path_mappings=sum(normalize(v) == model_url for v in mapping.values()),
        proposed_path_preferences=len(target),
        classifier_api=ext.get('expressions', {}).get('api') if isinstance(ext.get('expressions', {}).get('api'), int) else None,
        legacy_api_is_llm=ext.get('api') == 2,
        requires_preference_merge=bool(target), names_and_custom_messages_omitted=True)


def metadata(path):
    ancestors(path)
    s = path.stat()
    return dict(device=s.st_dev, device_major=os.major(s.st_dev), device_minor=os.minor(s.st_dev),
                uid=s.st_uid, gid=s.st_gid, mode=oct(stat.S_IMODE(s.st_mode)), size=s.st_size,
                mtime_ns=s.st_mtime_ns, ctime_ns=s.st_ctime_ns)


def asset_inventory(root):
    if not root.exists(): return dict(files=0, model_json=0, bytes=0, hashes={})
    safe_tree(root)
    hashes = files(root)
    return dict(files=len(hashes), model_json=sum('model' in n and n.endswith('.json') for n in hashes),
                bytes=sum((root/n).stat().st_size for n in hashes), hashes=hashes)


def plan_operations(package, root, patched_sha, companion_sha):
    dest = root / 'data/default-user/assets/live2d' / NAME
    txn = root.parent / '.live2d-studio-transactions' / root.name / (NAME + '-001')
    rows = [dict(action='create', path=str(dest/name), sha256=sha,
                 stage=str(txn/'stage/model'/name), backup=None) for name, sha in files(package).items()]
    rows += [dict(action='modify-if-adapter-approved', path=str(root/EXT/'live2d.js'), sha256=patched_sha,
                  before_sha256=digest(root/EXT/'live2d.js'), stage=str(txn/'stage/adapter/live2d.js'),
                  backup=str(txn/'backup/adapter/live2d.js'), before_metadata=metadata(root/EXT/'live2d.js')),
             dict(action='create-if-adapter-approved', path=str(root/EXT/'rp-talk.mjs'), sha256=companion_sha,
                  stage=str(txn/'stage/adapter/rp-talk.mjs'), backup=None)]
    return dict(destination=str(dest), model_url=MODEL_URL, transaction=str(txn), files=rows,
        new_directories=[str(dest), str(dest/'Generated_artwork.4096')],
        transaction_directories=[str(txn.parent.parent), str(txn.parent), str(txn), *[str(txn/n) for n in
            ('stage/model/Generated_artwork.4096','stage/adapter','backup/adapter','quarantine')]],
        transaction_metadata=[dict(path=str(txn/'plan.json'), purpose='Immutable approved hashes/destinations'),
            dict(path=str(txn/'journal.json'), purpose='Write-ahead state; atomic private temp + replace'),
            dict(path=str(txn/'recover.py'), purpose='Future reviewed standalone recovery helper; implementation/hash not yet available'),
            dict(path=str(txn.parent/'lock'), purpose='Exclusive transaction coordination')],
        runtime_generated_names='Private journal.json.<nonce>.tmp; stage/restore/live2d.js; quarantine/{model,live2d.js,rp-talk.mjs}; no served backups',
        existing_model_backup='None: new destination required; refuse instead of replacing user assets',
        settings_action='none', installed_file_count_without_adapter=len(rows)-2,
        installed_file_count_with_adapter=len(rows), production_execution_implemented=False)


def audit(root, package):
    root, package = Path(root).absolute(), Path(package).absolute()
    ancestors(root)
    spec = policy(); manifest = verify(package)
    assets = root/'data/default-user/assets/live2d'
    settings = root/'data/default-user/settings.json'
    before = {name: digest(root/name) for name in spec['compatibility']['target_sha256']}
    settings_before = metadata(settings)
    with settings.open() as stream: preferences = summarize_settings(stream)
    global_assets = asset_inventory(assets)
    # Never open character cards or chats; only independently named live2d subtrees.
    per_character = []
    characters = root/'data/default-user/characters'
    if characters.exists():
        ancestors(characters)
        for child in characters.iterdir():
            if child.is_symlink(): raise ValueError('Character directory contains a link; manual path review required')
            if child.is_dir() and (child/'live2d').exists():
                per_character.append(asset_inventory(child/'live2d'))
    mismatches = [n for n, sha in before.items() if sha != spec['compatibility']['target_sha256'][n]]
    core = core_probe(package, root/CORE, spec) if not mismatches else None
    patch = adapter_bytes(root) if not mismatches else None
    sha = lambda b: hashlib.sha256(b).hexdigest()
    patched_sha = sha(patch) if patch else None
    companion_sha = digest(REPO/'integrations/sillytavern/rp-talk.mjs')
    plan = plan_operations(package, root, patched_sha, companion_sha)
    paths = [Path(plan['destination']), root/EXT/'rp-talk.mjs', Path(plan['transaction']).parent,
             root/EXT/'live2d.upstream.js']
    conflicts = [str(p) for p in paths if p.exists() or p.is_symlink()]
    if preferences['proposed_path_mappings'] or preferences['proposed_path_preferences']:
        conflicts.append('Proposed model URL already has saved preferences/mappings; explicit review required')
    if any(p.name.casefold() == NAME.casefold() for p in assets.iterdir()):
        conflicts.append('Exact/case-folded model destination exists')
    heads = {}
    for name, location in [('sillytavern',root),('extension',root/EXT)]:
        heads[name] = subprocess.check_output(['git','--no-optional-locks','-C',str(location),'rev-parse','HEAD'],text=True).strip()
    versions = dict(sillytavern=json.loads((root/'package.json').read_text())['version'],
                    extension=json.loads((root/EXT/'manifest.json').read_text())['version'], git=heads)
    if heads != {'sillytavern':spec['compatibility']['sillytavern_commit'], 'extension':spec['compatibility']['extension_commit']}:
        mismatches.append('Git revision mismatch')
    runtime_hashes = {p.name:digest(p) for p in sorted((root/EXT/'lib').glob('*.js'))}
    # Bind inherited browser evidence to all public code/runtime/extension files in that run.
    baseline = json.loads((REPO/'runs/phase4a-acceptance-v4/production-before.json').read_text())
    public_baseline = {n: h for n,h in baseline.items() if n.startswith(('src/','public/',EXT+'/')) or n=='package.json'}
    inherited_mismatches = [n for n,h in public_baseline.items() if not (root/n).is_file() or digest(root/n)!=h]
    result = dict(schema_version=1, audit_only=True, production_authorized=False,
        compatibility='verified-pinned-code-and-Core' if not mismatches and not inherited_mismatches else 'blocked',
        versions=versions, pinned_files=before, version_mismatches=mismatches, runtime_hashes=runtime_hashes,
        inherited_browser_evidence=dict(run='runs/phase4a-acceptance-v4',files_checked=len(public_baseline),
            mismatches=inherited_mismatches,new_production_browser_session=False),
        core_probe=core, preferences=preferences, global_assets=global_assets,
        character_assets=dict(locations=len(per_character),files=sum(x['files'] for x in per_character),
            model_json=sum(x['model_json'] for x in per_character),names_omitted=True),
        filesystems={str(p):metadata(p) for p in [REPO,root.parent,root,assets,root/EXT]},
        cross_filesystem=REPO.stat().st_dev != root.stat().st_dev,
        target_local_same_device=len({p.stat().st_dev for p in [root.parent,root,assets,root/EXT]})==1,
        package_manifest_sha256=digest(package/'package-manifest.json'), package_bytes=sum(p.stat().st_size for p in package.rglob('*') if p.is_file()),
        conflicts=conflicts, adapter=dict(upstream_sha256=before[EXT+'/live2d.js'],patched_sha256=patched_sha,
            companion_sha256=companion_sha,manifest_auto_update=json.loads((root/EXT/'manifest.json').read_text()).get('auto_update'),production_patch_performed=False),
        readiness=dict(production_execution='blocked-unimplemented-target-filesystem-transaction',
            automatic_emotions=('blocked-current-LLM-preference-uses-fallback' if preferences['classifier_api']==2 and not preferences['legacy_api_is_llm']
                else 'requires-provider-review-and-separate-inference-validation'),
            settings_policy='preserve-all-preferences'),
        plan=plan, settings_metadata=settings_before,
        settings_read_policy='Projected allowlist; unknown values skipped, no raw settings copy/hash, chats/cards/credentials unopened')
    if before != {name:digest(root/name) for name in before} or settings_before != metadata(settings) or global_assets != asset_inventory(assets):
        raise RuntimeError('Production audit inputs changed during inspection; repeat before authorization')
    result['inspected_inputs_unchanged'] = True
    return result


def save_audit(root, package, output):
    output = Path(output).absolute()
    ancestors(output)
    if '..' in output.parts or not output.is_relative_to(REPO/'runs') or output == REPO/'runs':
        raise ValueError('Audit output must be a new file under project runs/')
    if output.exists(): raise FileExistsError('Audit output already exists')
    report = audit(root, package)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as handle:
        json.dump(report, handle, indent=2, sort_keys=True); handle.write('\n')
    return dict(report=str(output), compatibility=report['compatibility'],
                cross_filesystem=report['cross_filesystem'], production_authorized=False)
