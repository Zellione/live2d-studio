"""Author Girl2 only, via authenticated loopback MCP; preserve the current editor."""
import argparse
import json
from pathlib import Path
from live2d_studio.animation import recipe, package
from live2d_studio.manifest import digest,write_json
from live2d_studio.mcp import MCP,Operations

def build(source,output,endpoint):
    source,output=source.resolve(),output.resolve()
    if output.exists():raise FileExistsError('Use a fresh directory')
    if not source.is_file():raise FileNotFoundError(source)
    if digest(source)!='f2642d678254f0e489bb6bbc4107db7705eeb1daa4c4348d560f4d7cbeefc2d4':
        raise ValueError('Source must be the accepted Phase 2.6 Girl2 project')
    client=MCP(endpoint)
    output.mkdir(parents=True)
    op=Operations(client,output)
    write_json(output/'input.json',dict(path=str(source),sha256=digest(source)))
    op.call('project_save_as',dict(path=str(output/'editor-snapshot.psd2live')))
    op.call('project_open',dict(path=str(source)))
    axes={side:client.tool('workspace_inspect',{'request':{'target':'warp:DeformBrowShape'+side}})['data']['axes'] for side in ['L','R']}
    steps=recipe(axes)
    # The checked-in recipe is a reviewed Girl2 contract, not a general rig recipe.
    reviewed=json.loads((Path(__file__).resolve().parents[1]/'recipes/girl2-animation.json').read_text())
    if steps!=reviewed:raise ValueError('Rig differs from the reviewed Girl2 recipe')
    write_json(output/'recipe.json',steps)
    for step in steps:op.call(step['operation'],step['request'])
    op.call('project_save_as',dict(path=str(output/'character.psd2live')))
    op.call('project_export_psd',dict(path=str(output/'character.psd'),scale=1))
    op.call('project_open',dict(path=str(output/'character.psd2live')))
    op.call('project_export_model',dict(output_directory=str(output/'export')))
    write_json(output/'validation.json',package(output/'export',output/'runtime'))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--endpoint',default='http://127.0.0.1:23871/mcp')
    a=p.parse_args();build(a.source,a.output,a.endpoint)
