"""RP acceptance from actual event-driven browser runs, separate from aesthetics."""
import json
from pathlib import Path

def evaluate(results):
    required={'rp','lifecycle','failure','race','visual'}
    failures=[]
    for mode in required:
        r=results.get(mode)
        if not r or r.get('status')!='pass':failures.append(mode+': missing/failed browser run');continue
        n=r.get('network_validation',{})
        if not n or any(n.get(k) for k in ['missing_successful_resources','unexpected_http_errors','uncaught_exceptions','caught_event_listener_errors']):
            failures.append(mode+': runtime/network/event errors')
    rp=results.get('rp',{})
    checks=rp.get('mapping_checks',{})
    if set(checks)!={'joy','sadness','anger','surprise','confusion','embarrassment','neutral'} or not all(v.get('checks') and all(c.get('accepted') for c in v['checks']) for v in checks.values()):
        failures.append('Incomplete classifier-to-expression proof')
    rest=rp.get('samples',{}).get('rest',[])
    if not rest or any(r['ParamMouthOpenY']>=.02 for r in rest):failures.append('Neutral mouth recovery unverified')
    for label in checks:
        rows=rp.get('samples',{}).get('message_'+label,[])
        if not rows or max(r['ParamMouthOpenY'] for r in rows)-min(r['ParamMouthOpenY'] for r in rows)<=.15:
            failures.append('No measured talking: '+label)
    lifecycle=results.get('lifecycle',{})
    if not lifecycle.get('idle_recovered') or not lifecycle.get('switch_removed'):failures.append('Idle/character cleanup unverified')
    if max(results.get('visual',{}).get('mouth_pixel_changes',{}).values(),default=0)<=20:
        failures.append('Visible mouth-region change unverified')
    return dict(schema_version=1,rp_integration='accepted-isolated-adapter' if not failures else 'rejected',
        failures=failures,classification='mock network labels, not classifier model inference',
        visual_animation='requires-independent-review',production_ready=False)


def load_results(directories):
    results={}
    for directory in directories:
        r=json.loads((Path(directory)/'result.json').read_text())['result']['value']
        if r['mode'] in results:raise ValueError('Duplicate scenario mode')
        results[r['mode']]=r
    return results
