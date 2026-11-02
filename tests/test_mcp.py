"""Transport contract tests use dummy credentials; no user secrets or live editor."""
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

from live2d_studio.mcp import MCP, Operations, validate_import


class Response(io.BytesIO):
    headers={'Mcp-Session-Id':'local-session'}


class Transport:
    def __init__(self, sse=False):
        self.requests=[]
        self.sse=sse

    def open(self, request, timeout):
        self.requests.append(request)
        message=json.loads(request.data)
        result={'jsonrpc':'2.0','id':message.get('id'),'result':
            {'structuredContent':{'ok':True,'data':{'loaded':False}}}}
        content=json.dumps(result)
        if self.sse:
            content='event: message\ndata: '+content+'\n\n'
        return Response(content.encode())


class MCPTests(unittest.TestCase):
    def test_token_header_session_and_json_sse(self):
        for sse in (False,True):
            transport=Transport(sse)
            with patch.dict(os.environ,{'PSD2LIVE_MCP_TOKEN':'dummy-test-only'}), \
                 patch('urllib.request.build_opener',return_value=transport):
                client=MCP('http://127.0.0.1:23871/mcp')
                self.assertTrue(client.tool('workspace_inspect',{'request':{'scope':'project'}})['ok'])
            self.assertEqual(len(transport.requests),3)
            for request in transport.requests:
                self.assertEqual(request.get_header('Authorization'),'Bearer dummy-test-only')
                self.assertNotIn(b'dummy-test-only',request.data)
            self.assertEqual(transport.requests[-1].get_header('Mcp-session-id'),'local-session')

    def test_unauthorized_error_is_actionable_and_redacted(self):
        with patch('urllib.request.build_opener') as opener:
            opener.return_value.open.side_effect=urllib.error.HTTPError('http://127.0.0.1:23871/mcp',401,'private-server-message',{},None)
            with self.assertRaisesRegex(RuntimeError,'set PSD2LIVE_MCP_TOKEN locally'):
                MCP('http://127.0.0.1:23871/mcp')

    def test_remote_and_credential_urls_refused(self):
        for endpoint in ('https://evil.example/mcp','http://127.0.0.1.evil/mcp',
                         'http://user:secret@127.0.0.1/mcp','file:///tmp/mcp',
                         'http://127.0.0.1/mcp?token=secret'):
            with self.assertRaises(ValueError):
                MCP(endpoint)

    def test_redirect_refused(self):
        # Inspect the actual opener's redirect policy, without opening sockets.
        with patch.object(MCP,'rpc'):
            client=MCP('http://127.0.0.1:23871/mcp')
        handler=next(h for h in client.opener.handlers if hasattr(h,'redirect_request'))
        with self.assertRaisesRegex(RuntimeError,'redirects'):
            handler.redirect_request(None,None,302,'',{},'https://example.com')

    def test_job_failure_stops_following_mutations(self):
        class Client:
            def tool(self,name,args):
                if name=='workspace_inspect':
                    return {'ok':True,'data':{'state':'fresh','project_id':'new'}}
                if args['operation']=='job_wait':
                    return {'ok':True,'data':{'id':'job','terminal':True,'status':'failed'}}
                return {'ok':True,'data':{'id':'job','terminal':False,'status':'running'}}
        with tempfile.TemporaryDirectory() as temp:
            ops=Operations(Client(),Path(temp))
            with self.assertRaisesRegex(RuntimeError,'operation failed'):
                ops.call('project_create_artwork',{'layers':[]})
            self.assertEqual(len(ops.log),1)
            self.assertEqual(ops.log[0]['request']['state'],'fresh')

    def test_import_requires_mapping_and_parameters(self):
        request={'layers':[dict(name='face',role='face',side='none')]}
        overview={'ok':True,'data':dict(layers=dict(total=1,items=request['layers']),meshes=1,
            deformers=dict(total=1),parameters=dict(total=0,items=[]))}
        with self.assertRaisesRegex(ValueError,'parameters'):
            validate_import(request,overview)
