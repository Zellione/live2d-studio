"""Read-only mouth geometry inspection of the current PSD2Live editor."""
import argparse,json
from pathlib import Path
from live2d_studio.mcp import MCP
from live2d_studio.generic_rig import inspect,overview,objects,targets
from live2d_studio.manifest import write_json
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if a.output.exists():raise FileExistsError('Choose a fresh inspection file')
c=MCP('http://127.0.0.1:23871/mcp');d=overview(c)['data'];items=objects(c);b=targets(d,items)
ls={l['id'] for l in d['layers']['items'] if 'mouth' in l['name'].lower()}
ts=[o['target'] for o in items if o.get('layerId') in ls]+[b['mouth:none']]
r={'parameters':[p for p in d['parameters']['items'] if 'Mouth' in p['id']], 'layers':[l for l in d['layers']['items'] if l['id'] in ls], 'objects':{},'topology':{}}
for t in ts:
 r['objects'][t]=inspect(c,dict(target=t))
 if t.startswith('mesh:'):r['topology'][t]=c.tool('workspace_call',dict(operation='mesh_get_topology',request=dict(target=t,limit=4096)))['data']
write_json(a.output,r)
print(json.dumps({k:dict(axes=v['axes'],parent=v.get('parent'),inherited=v.get('inherited')) for k,v in r['objects'].items()},indent=2))
