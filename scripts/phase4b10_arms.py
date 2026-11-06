import argparse
from pathlib import Path
from live2d_studio.mcp import MCP
from live2d_studio.frontal_arms import author, export

if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--predecessor',type=Path,required=True)
    p.add_argument('--layers',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--amount',type=float,default=1)
    a=p.parse_args();a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=False)
    client=MCP('http://127.0.0.1:23871/mcp')
    author(client,a.predecessor.resolve(),a.layers.resolve(),a.output/'authoring',a.amount)
    print(export(client,a.output/'authoring',a.output/'exported'))
