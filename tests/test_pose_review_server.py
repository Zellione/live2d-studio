"""Loopback HTTP contracts with synthetic fixtures; no GPU or external service."""
import http.client
import json
import threading
import unittest
import test_pose_reviewer as fixtures
from live2d_studio.pose_review_server import make_server


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.ReviewerTests();self.fixture.setUp()
        self.server=make_server(self.fixture.store,0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.host=f'127.0.0.1:{self.server.server_port}'
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.fixture.tearDown()
    def request(self,method,path,body=None,headers=None):
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        c.request(method,path,body=body,headers=headers or {})
        r=c.getresponse();data=r.read();status=r.status;c.close();return status,data
    def test_fixed_assets_and_host_origin_guards(self):
        self.assertEqual(self.request('GET','/')[0],200)
        for path in ('/review.json','/asset/../review.json','/asset/%2e%2e/review.json','/asset/guide/right-lift/../../review.json'):
            self.assertIn(self.request('GET',path)[0],(400,404))
        for headers in ({'Host':'evil.example'},{'Origin':'http://evil.example'},{'Sec-Fetch-Site':'cross-site'}):
            self.assertEqual(self.request('GET','/api/state',headers=headers)[0],400)
    def test_csrf_and_selected_only_finish(self):
        status,raw=self.request('GET','/api/state');self.assertEqual(status,200)
        token=json.loads(raw)['csrf'];body=json.dumps({'action':'finish'})
        headers={'Content-Type':'application/json','Origin':'http://'+self.host,'X-Review-CSRF':token}
        for omit in ('Origin','X-Review-CSRF'):
            bad=dict(headers);del bad[omit];self.assertEqual(self.request('POST','/api/action',body,bad)[0],400)
        status,raw=self.request('POST','/api/action',body,headers)
        self.assertEqual(status,200);self.assertEqual(json.loads(raw)['selected'],{})
        self.assertEqual(self.request('POST','/api/action','[]',headers)[0],400)
        self.assertEqual(self.request('POST','/api/action','x'*16385,headers)[0],400)

if __name__=='__main__':unittest.main()
