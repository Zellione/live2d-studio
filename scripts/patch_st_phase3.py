"""Apply the opt-in RP fixes ONLY to a verified isolated ST copy in this repo."""
import argparse,hashlib,json
from pathlib import Path

UPSTREAM='f6bae7eff0705593403de51062b9dead7a1a5799a8aaa1754c677149fb117c5b'

def patched(source):
    if hashlib.sha256(source.encode()).hexdigest()!=UPSTREAM:raise ValueError('Extension revision differs; review patch again')
    s="import { TalkController } from './rp-talk.mjs';\nconst rpTalk = new TalkController();\nlet rpGeneration = 0;\nconst rpRequests = {};\n"+source
    s=s.replace('async function loadLive2d(visible = true) {','async function loadLive2d(visible = true) {\n    rpGeneration++; rpTalk.cancelAll();')
    s=s.replace('        models[character] = model;', '''        if (extension_settings.live2d.characterModelsSettings[character][model_path].rp_animation?.authored_idle) {
            // This bundle already authors breathing/head/blink. Avoid the bundled
            // runtime's additional fixed-amplitude breathing/head oscillators.
            model.internalModel.breath = undefined;
            live2d.config.preserveExpressionOnMotion = true;
        }
        models[character] = model;''')
    s=s.replace('async function removeModel(character) {','async function removeModel(character) {\n    rpTalk.cancel(character);')
    s=s.replace('async function updateExpression(chat_id) {','async function updateExpression(chat_id) {\n    const generation = rpGeneration;')
    s=s.replace('    const expression = await getExpressionLabel(message.mes);', '''    const ticket = (rpRequests[character] || 0) + 1;
    rpRequests[character] = ticket;
    const expression = await getExpressionLabel(message.mes);
    if (generation !== rpGeneration || ticket !== rpRequests[character] || !models[character]) return;''')
    s=s.replace("    let model_expression = extension_settings.live2d.characterModelsSettings[character][model_path]['classify_mapping'][expression]['expression'];\n    let model_motion = extension_settings.live2d.characterModelsSettings[character][model_path]['classify_mapping'][expression]['motion'];", "    const mapping = extension_settings.live2d.characterModelsSettings[character][model_path].classify_mapping;\n    const selected = mapping[expression] || mapping.neutral || {expression:'none',motion:'none'};\n    let model_expression = selected.expression;\n    let model_motion = selected.motion;")
    # All unavailable/invalid classifications restore neutral rather than stale emotion.
    start=s.index('async function getExpressionLabel(');end=s.index('\nfunction moveModel(',start)
    block=s[start:end].replace('return FALLBACK_EXPRESSION;',"return 'neutral';")
    block=block.replace('return data.classification[0].label;',"return data?.classification?.[0]?.label || 'neutral';")
    end_brace=block.rfind('}')
    block=block[:end_brace]+"    return 'neutral'; // non-OK HTTP response\n"+block[end_brace:]
    s=s[:start]+block+s[end:]
    s=s.replace('async function playMessage(chat_id) {', """async function playMessage(chat_id) {
    const chat = getContext().chat;
    const current = chat[chat_id];
    const latest = chat.findLastIndex(m => !m.is_user && !m.is_system && m.name === current.name);
    if (latest !== chat_id) return; // delayed classifier must not start stale speech
""")
    s=s.replace("async function playTalk(character, text) {",'''async function playTalk(character, text) {
    const rpPath = extension_settings.live2d.characterModelMapping[character];
    const rpSettings = extension_settings.live2d.characterModelsSettings[character]?.[rpPath];
    if (rpSettings?.rp_animation?.smooth_text_talk) {
        return rpTalk.play(character, models[character], text, rpSettings);
    }''')
    return s

def apply(root):
    repo=Path(__file__).resolve().parents[1];root=root.resolve()
    if not root.is_relative_to(repo/'.cache') or not (root/'snapshot-hashes.json').is_file():
        raise ValueError('Only a prepare_st_smoke isolated copy under this repo .cache is allowed')
    ext=root/'data/default-user/extensions/Extension-Live2d'
    target=ext/'live2d.js'
    if target.is_symlink() or not target.resolve().is_relative_to(root):raise ValueError('Extension target escapes isolated copy')
    original=target.read_text();result=patched(original)
    backup=ext/'live2d.upstream.js'
    if backup.exists() or backup.is_symlink() or (ext/'rp-talk.mjs').exists() or (ext/'rp-talk.mjs').is_symlink():raise FileExistsError('Patch already applied; use a fresh isolated copy')
    backup.write_text(original)
    (ext/'rp-talk.mjs').write_bytes((repo/'integrations/sillytavern/rp-talk.mjs').read_bytes())
    target.write_text(result)
    (root/'phase3-patch.json').write_text(json.dumps(dict(upstream_sha256=UPSTREAM,patched_sha256=hashlib.sha256(result.encode()).hexdigest(),production_modified=False),indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('isolated_root',type=Path);apply(p.parse_args().isolated_root)
