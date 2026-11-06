"""Read saved project expressions and mouth dependencies without authoring changes."""
import argparse
from pathlib import Path
from live2d_studio.generic_rig import open_stage,overview,objects,inspect,locked_editor
from live2d_studio.mcp import MCP
from live2d_studio.manifest import write_json,digest

@locked_editor
def run(project,output):
 output.mkdir(parents=True,exist_ok=False)
 client=MCP('http://127.0.0.1:23871/mcp');open_stage(client,project.parent,output)
 view=overview(client)['data'];items=objects(client)
 expressions=client.tool('workspace_call',dict(operation='expression_list',request={}))
 if not expressions.get('ok'):raise RuntimeError('Cannot read expressions')
 details={o['target']:inspect(client,dict(target=o['target'])) for o in items}
 write_json(output/'inspection.json',dict(project_sha256=digest(project),overview=view,objects=items,details=details,expressions=expressions['data']))
 print(output)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.project.resolve(),a.output.resolve())
