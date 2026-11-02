"""Rebuild the original Phase 1 fixture through local PSD2Live MCP (stdlib only).

Requires a running PSD2Live 3.6.7 MCP server. Unsaved work is never discarded.
The destination must be new. PSD2LIVE_MCP_TOKEN is optional and never logged.
"""
import argparse
import json
import os
from pathlib import Path
import time
import urllib.parse
import urllib.request
import urllib.error
import uuid
from create_phase1_art import create

class MCP:
    def __init__(self, endpoint):
        if urllib.parse.urlparse(endpoint).hostname != '127.0.0.1':
            raise ValueError('MCP endpoint must be loopback 127.0.0.1')
        self.endpoint, self.session, self.counter = endpoint, None, 0
        self.rpc('initialize', {'protocolVersion':'2024-11-05','capabilities':{},
                               'clientInfo':{'name':'live2d-studio-phase1','version':'1'}})
        self.rpc('notifications/initialized', {}, notification=True)

    def rpc(self, method, params, notification=False):
        self.counter += 1
        message = {'jsonrpc':'2.0','method':method,'params':params}
        if not notification:
            message['id'] = self.counter
        headers = {'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
        if self.session:
            headers['Mcp-Session-Id'] = self.session
        token = os.environ.get('PSD2LIVE_MCP_TOKEN')
        if token:
            headers['Authorization'] = 'Bearer ' + token
        request = urllib.request.Request(self.endpoint, json.dumps(message).encode(), headers)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                self.session = response.headers.get('Mcp-Session-Id', self.session)
                body = response.read().decode()
        except urllib.error.HTTPError as error:
            if error.code == 401:
                raise RuntimeError('PSD2Live requires its MCP token: set PSD2LIVE_MCP_TOKEN locally; do not put it in the recipe or logs.') from None
            raise
        if notification:
            return None
        if body.lstrip().startswith('{'):
            result = json.loads(body)
        else:
            messages = [json.loads(line[5:].strip()) for line in body.splitlines() if line.startswith('data:')]
            result = next(item for item in messages if item.get('id') == self.counter)
        if 'error' in result:
            raise RuntimeError(result['error'])
        return result['result']

    def tool(self, name, arguments):
        response = self.rpc('tools/call', {'name':name,'arguments':arguments})
        value = response.get('structuredContent')
        if value is None:
            value = json.loads(next(c['text'] for c in response['content'] if c['type']=='text'))
        return value

def build(destination, endpoint):
    destination = destination.resolve()
    if destination.exists():
        raise FileExistsError('Use a fresh destination; existing models are never overwritten')
    client = MCP(endpoint)
    destination.mkdir(parents=True, exist_ok=False)
    art = create(destination/'art')
    log=[]
    def operation(name, fields):
        context = client.tool('workspace_inspect', {'request':{'scope':'project'}})
        if not context.get('ok'):
            raise RuntimeError(context)
        state=context['data']
        request={**fields, 'state':state['state'], 'project_id':state.get('project_id'),
                 'request_id':'phase1-'+str(uuid.uuid4())}
        response=client.tool('workspace_call', {'operation':name,'request':request,'wait_ms':20000})
        log.append({'operation':name,'request':request,'result':response})
        (destination/'mcp-transcript.json').write_text(json.dumps(log,indent=2)+'\n')
        if not response.get('ok'):
            raise RuntimeError(response)
        data=response['data']
        deadline=time.monotonic()+180
        while data.get('terminal') is False:
            if time.monotonic()>deadline:
                raise TimeoutError('Job still running; inspect job '+data['id']+' before retrying')
            response=client.tool('workspace_call', {'operation':'job_wait','request':{'id':data['id'],'timeout_ms':20000}})
            if not response.get('ok'):
                raise RuntimeError(response)
            data=response['data']
            log[-1]['completion']=response
            (destination/'mcp-transcript.json').write_text(json.dumps(log,indent=2)+'\n')
        if data.get('status') in ('failed','cancelled'):
            raise RuntimeError(data)
        print(name, data.get('status','ok'), flush=True)
        return data
    operation('project_create_artwork',art)
    recipe=Path(__file__).resolve().parents[1]/'tests/fixtures/phase1/rig-recipe.json'
    for step in json.loads(recipe.read_text()):
        operation(step['operation'],step['request'])
    operation('project_save_as',{'path':str(destination/'face.psd2live')})
    operation('project_export_psd',{'path':str(destination/'face.psd'),'scale':1})
    operation('project_open',{'path':str(destination/'face.psd2live')})
    operation('project_export_model',{'output_directory':str(destination/'runtime')})
    print(destination)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination',type=Path,required=True)
    parser.add_argument('--endpoint',default='http://127.0.0.1:23871/mcp')
    args=parser.parse_args()
    build(args.destination,args.endpoint)
