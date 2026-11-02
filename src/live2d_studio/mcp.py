"""Loopback-only MCP transport. Token supplied via environment, never logged."""
import json
import os
import urllib.parse
import urllib.request
import urllib.error
import time
import uuid

class MCP:
    def __init__(self, endpoint):
        url = urllib.parse.urlparse(endpoint)
        if url.scheme != 'http' or url.hostname != '127.0.0.1' or url.username or url.password or url.query or url.fragment:
            raise ValueError('MCP endpoint must be loopback 127.0.0.1')
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                raise RuntimeError('MCP redirects are prohibited')
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
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
            with self.opener.open(request, timeout=60) as response:
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
        if response.get('isError'):
            raise RuntimeError('MCP tool failed: '+name)
        value = response.get('structuredContent')
        if value is None:
            value = json.loads(next(c['text'] for c in response['content'] if c['type']=='text'))
        return value


class Operations:
    """Same state/job protocol as Phase 1, with bounded waits and local evidence."""
    def __init__(self, client, output):
        self.client, self.output, self.log = client, output, []

    def call(self, name, fields):
        from .manifest import write_json
        context = self.client.tool('workspace_inspect', {'request':{'scope':'project'}})
        if not context.get('ok'):
            raise RuntimeError('MCP project inspection failed')
        state = context['data']
        request = dict(fields, state=state['state'], project_id=state.get('project_id'),
                       request_id='phase2-'+str(uuid.uuid4()))
        response = self.client.tool('workspace_call', {'operation':name,'request':request})
        entry = dict(operation=name, request=request, result=response)
        self.log.append(entry)
        write_json(self.output/'mcp-transcript.json', self.log)
        deadline = time.monotonic()+180
        while response.get('ok') and response['data'].get('terminal') is False:
            if time.monotonic()>deadline:
                raise TimeoutError('MCP job still running: '+response['data']['id'])
            response = self.client.tool('workspace_call', {'operation':'job_wait',
                'request':{'id':response['data']['id'],'timeout_ms':20000}})
            entry['completion'] = response
            write_json(self.output/'mcp-transcript.json', self.log)
        if not response.get('ok') or response['data'].get('status') in {'failed','cancelled'}:
            raise RuntimeError('MCP operation failed; inspect local diagnostics: '+name)
        return response['data']


def build(project, output, endpoint):
    from .manifest import artwork_request, write_json, load_validate
    from .bundle import validate
    data = load_validate(project)
    if data['schema_version']==2 and not data.get('rig_ready',False):
        raise ValueError('Neural decomposition has not passed animation-layer review; inspect missing variants and hidden geometry')
    from .pipeline import EXPECTED
    found = {(l['role'],l['side']) for l in data['layers']}
    if set(EXPECTED)-found or any(l['role']=='unknown' for l in data['layers']):
        raise ValueError('Incomplete/unresolved layers: inspect project before rig import')
    if output.exists():
        raise FileExistsError('Build output exists; choose a fresh directory')
    request = artwork_request(project)
    client = MCP(endpoint)
    output.mkdir(parents=True,exist_ok=False)
    ops = Operations(client,output)
    ops.call('project_create_artwork',request)
    # project_create_artwork generates meshes, deformers and basic parameters.
    overview = client.tool('workspace_overview',{'request':{}})
    write_json(output/'import-overview.json',overview)
    write_json(output/'import-validation.json', validate_import(request,overview))
    ops.call('project_save_as',{'path':str((output/'character.psd2live').resolve())})
    ops.call('project_export_psd',{'path':str((output/'character.psd').resolve()),'scale':1})
    ops.call('project_open',{'path':str((output/'character.psd2live').resolve())})
    ops.call('project_export_model',{'output_directory':str((output/'runtime').resolve())})
    models = list((output/'runtime').glob('*.model3.json'))
    if len(models)!=1:
        raise ValueError('Expected exactly one exported model')
    report = validate(models[0])
    write_json(output/'integrity.json',report)
    if report['status']!='pass':
        raise ValueError('Export integrity failed; inspect integrity.json')
    return report


def validate_import(request, overview):
    if not overview.get('ok'):
        raise ValueError('PSD2Live import inspection failed')
    data = overview['data']
    expected = {(l['name'],l['role'],l['side']) for l in request['layers']}
    imported = {(l['name'],l['role'],l['side']) for l in data['layers']['items']}
    if expected-imported or data['layers']['total'] != len(data['layers']['items']):
        raise ValueError('PSD2Live layer mapping missing or truncated')
    required = {'ParamEyeLOpen','ParamEyeROpen','ParamMouthOpenY','ParamAngleX','ParamAngleY','ParamAngleZ'}
    if required-{p['id'] for p in data['parameters']['items']}:
        raise ValueError('PSD2Live did not generate expected basic parameters')
    if data['meshes'] < len(expected) or data['deformers']['total'] == 0:
        raise ValueError('PSD2Live did not generate meshes/deformers')
    return dict(status='pass',input_layers=len(expected),imported_layers=data['layers']['total'],
                meshes=data['meshes'],deformers=data['deformers']['total'],
                parameter_count=data['parameters']['total'],animation_tested=False)
