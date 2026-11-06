"""CPU-only reviewer transaction tests; synthetic images are never user evidence."""
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import subprocess
import sys
import unittest
from PIL import Image,ImageDraw
from live2d_studio.pose_review import REPO,Store,initialize,digest,write,fresh_seeds,fingerprint
from live2d_studio.pose_guides import fit,layout

PRESET={'long_edge':1024,'steps':20,'cfg':4.0,'shift':3.0,'denoise':1.0,'sampler':'euler',
        'scheduler':'simple','latent':'source','mask':'none','guidance':'skeleton','cfg_norm':False}


def synthetic_worker(argv,**kwargs):
    plan_file=Path(argv[-1]);plan=json.loads(plan_file.read_text())
    report={'status':'completed','tasks':[]}
    for t in plan['tasks']:
        folder=plan_file.parent/t['id'];folder.mkdir()
        Image.new('RGB',(32,48),(t['seed']%255,(t['seed']//255)%255,100)).save(folder/'image.png')
        row={'id':t['id'],'seed':t['seed'],'config':t['config'],'prompt':t['prompt'],
             'guide_sha256':plan['inputs']['guide.png'],'image_sha256':digest(folder/'image.png'),
             'output_size':[32,48],'seconds':0.0,'synthetic_test_fixture':True}
        write(folder/'result.json',row);report['tasks'].append(row)
    write(plan_file.parent/'report.json',report);return SimpleNamespace(returncode=0)


class ReviewerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=REPO/'runs',prefix='pose-test-');self.folder=Path(self.temp.name)
        self.source=self.folder/'original.png';im=Image.new('RGBA',(120,240));ImageDraw.Draw(im).rectangle((20,10,100,239),fill='#80a0b0');im.save(self.source)
        self.store=initialize(self.folder/'review',self.source,{'test':PRESET},'Synthetic test fixture')
    def tearDown(self):self.temp.cleanup()
    def batch(self,pose='right-lift'):
        b,fd=self.store.reserve(pose,'test');self.store.execute(b,fd,synthetic_worker);return self.store.state()['batches'][-1]
    def test_five_unique_fresh_browser_exact_seeds(self):
        a=self.batch();b=self.batch();seeds=[c['seed'] for batch in (a,b) for c in batch['candidates']]
        self.assertEqual(len(seeds),10);self.assertEqual(len(set(seeds)),10);self.assertTrue(all(0<=v<2**53 for v in seeds))
        with self.assertRaises(ValueError):fresh_seeds([],4)
        stream=iter([1,1,2,3,4,5,6]);self.assertEqual(fresh_seeds([1],random=lambda _:next(stream)),[2,3,4,5,6])
    def test_parameter_pins_and_exact_plan(self):
        b=self.batch();plan=json.loads(self.store.safe(b['directory']+'/plan.json').read_text())
        self.assertEqual({fingerprint(t['config']) for t in plan['tasks']},{fingerprint(PRESET)})
        with self.store.transaction() as s:s['presets']['test']['steps']=21
        with self.assertRaises(ValueError):self.store.reserve('wave','test')

    def test_explicit_new_preset_keeps_old_batches_and_approval(self):
        b=self.batch();self.store.decide('accept','right-lift',b['candidates'][0]['id'])
        before=self.store.state();cfg=dict(PRESET,steps=30,prompt_suffix='Keep both hands visible.')
        self.store.add_preset('new-prompt-30',cfg)
        after=self.store.state();self.assertEqual(before['batches'],after['batches'])
        self.assertEqual(before['poses'],after['poses'])
        with self.assertRaises(ValueError):self.store.add_preset('test',cfg)
        b,fd=self.store.reserve('wave','new-prompt-30')
        plan=json.loads(self.store.safe(b['directory']+'/plan.json').read_text());os.close(fd)
        self.assertTrue(all(t['prompt'].endswith(cfg['prompt_suffix']) for t in plan['tasks']))
    def test_selection_persists_and_approved_pose_is_immutable(self):
        b=self.batch();cid=b['candidates'][2]['id'];self.store.decide('accept','right-lift',cid,reviewer='Test human')
        reopened=Store(self.store.root);self.assertEqual(reopened.state()['poses']['right-lift']['selected'],cid)
        before=reopened.state()['poses']['right-lift'];self.batch('wave')
        self.assertEqual(before,reopened.state()['poses']['right-lift'])
        with self.assertRaises(ValueError):reopened.reserve('right-lift','test')
        with self.assertRaises(ValueError):reopened.decide('unsupported','right-lift')
    def test_rejection_unsupported_and_selected_only_export(self):
        b=self.batch();self.store.decide('reject','right-lift',b['candidates'][0]['id'],'bad hands')
        self.store.decide('unsupported','left-lift',reason='Outside framing')
        with self.assertRaises(ValueError):self.store.reserve('left-lift','test')
        w=self.batch('wave');self.store.decide('accept','wave',w['candidates'][0]['id'])
        result=self.store.finish();self.assertEqual(set(result['selected']),{'wave'})
        self.assertEqual(result['poses']['right-lift'],'rejected');self.assertEqual(result['poses']['left-lift'],'unsupported')
        self.assertFalse(result['selected']['wave']['independently_verified_source_pixels'])
    def test_candidate_tamper_blocks_accept_and_export(self):
        b=self.batch();c=b['candidates'][0];self.store.safe(c['image']).write_bytes(b'changed')
        with self.assertRaises(ValueError):self.store.decide('accept','right-lift',c['id'])
        good=b['candidates'][1];self.store.decide('accept','right-lift',good['id']);self.store.safe(good['image']).write_bytes(b'changed')
        with self.assertRaises(ValueError):self.store.finish()
    def test_source_guide_and_path_guards(self):
        for path in ('../outside','/etc/passwd','assets/../../outside','assets\\file'):
            with self.assertRaises(ValueError):self.store.safe(path)
        (self.store.root/'escape').symlink_to('/tmp')
        with self.assertRaises(ValueError):self.store.safe('escape/file')
        self.store.safe('assets/source.png').write_bytes(b'changed')
        with self.assertRaises(ValueError):self.store.reserve('wave','test')
    def test_cross_process_gpu_lock_serializes_and_is_released(self):
        b,fd=self.store.reserve('wave','test')
        try:
            with self.assertRaises(ValueError):Store(self.store.root).reserve('right-lift','test')
            code='from live2d_studio.pose_review import Store; import sys; Store(sys.argv[1]).gpu_lock()'
            child=subprocess.run([sys.executable,'-c',code,str(self.store.root)],capture_output=True)
            self.assertNotEqual(child.returncode,0)
            self.assertIn(b'GPU batch is already running',child.stderr)
            self.assertEqual(self.store.state()['batches'][0]['status'],'running')
        finally:os.close(fd)
        self.assertEqual(Store(self.store.root).state()['batches'][0]['status'],'interrupted')
    def test_interrupted_batch_resumes_without_reusing_completed_candidate(self):
        b,fd=self.store.reserve('wave','test');planfile=self.store.safe(b['directory']+'/plan.json');plan=json.loads(planfile.read_text())
        partial=planfile.parent/'partial';partial.mkdir();one=dict(plan,tasks=plan['tasks'][:1]);write(partial/'plan.json',one)
        synthetic_worker(['fake',str(partial/'plan.json')]);(partial/'c1').rename(planfile.parent/'c1');os.close(fd)
        state=self.store.state();first=state['batches'][0]['candidates'][0];before=first['sha256']
        resumed,fd=self.store.resume(b['id'],background=False);self.store.execute(resumed,fd,synthetic_worker)
        final=self.store.state()['batches'][0];self.assertEqual(final['status'],'completed')
        self.assertEqual(final['candidates'][0]['sha256'],before);self.assertEqual(len(self.store.state()['used_seeds']),5)
        self.assertEqual(len(json.loads(self.store.safe(final['execution_directory']+'/plan.json').read_text())['tasks']),4)
    def test_deterministic_saved_task_replay(self):
        b=self.batch();source=self.store.safe(b['directory']);target=self.folder/'replay';target.mkdir()
        plan=json.loads((source/'plan.json').read_text());write(target/'plan.json',plan);synthetic_worker(['fake',str(target/'plan.json')])
        for c in b['candidates']:self.assertEqual(c['sha256'],digest(target/c['task_id']/'image.png'))
    def test_wrong_pose_selection_and_unknown_candidate_rejected(self):
        b=self.batch()
        with self.assertRaises(ValueError):self.store.decide('accept','wave',b['candidates'][0]['id'])
        with self.assertRaises(ValueError):self.store.asset('review.json')
    def test_aspect_ratio_uses_uniform_scale_and_padding(self):
        dims,s,offset=layout((1078,2089),1536);self.assertEqual(dims,(800,1536))
        self.assertAlmostEqual(s,1536/2089);self.assertGreater(offset[0],0)
        self.assertEqual(fit(Image.new('RGBA',(1078,2089),'red'),1536).size,dims)
    def test_invalid_presets_fail_before_run_creation(self):
        with self.assertRaises(ValueError):initialize(self.folder/'invalid',self.source,{'bad':dict(PRESET,steps=10000)},'fixture')
        self.assertFalse((self.folder/'invalid').exists())

    def test_worker_prompt_tamper_is_rejected(self):
        b,fd=self.store.reserve('wave','test');folder=self.store.safe(b['directory'])
        synthetic_worker(['fake',str(folder/'plan.json')]);file=folder/'c1/result.json'
        row=json.loads(file.read_text());row['prompt']='wrong prompt';write(file,row);os.close(fd)
        with self.assertRaises(ValueError):self.store.state()

    def test_timeout_releases_gpu_and_marks_failure(self):
        b,fd=self.store.reserve('wave','test')
        def timeout(argv,**kwargs):
            self.assertEqual(kwargs['timeout'],3600)
            raise subprocess.TimeoutExpired(argv,3600)
        self.assertFalse(self.store.execute(b,fd,timeout))
        self.assertEqual(self.store.state()['batches'][0]['status'],'failed')
        fd=self.store.gpu_lock();os.close(fd)

    def test_other_pose_review_during_generation(self):
        b=self.batch();active,fd=self.store.reserve('wave','test')
        try:
            self.store.decide('accept','right-lift',b['candidates'][0]['id'])
            self.assertEqual(self.store.state()['poses']['right-lift']['status'],'approved')
            with self.assertRaises(ValueError):self.store.decide('unsupported','wave')
        finally:os.close(fd)


if __name__=='__main__':unittest.main()
