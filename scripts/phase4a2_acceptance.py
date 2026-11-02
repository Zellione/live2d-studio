"""Btrfs disposable acceptance. Production is read-only public source, never data.

Run with uv run --frozen python scripts/phase4a2_acceptance.py --run-id NEW_ID.
The fixed /home test base is intentionally outside the production installation.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

from live2d_studio import target_recovery as tx, target_transaction as installer
from live2d_studio.packaging import REPO, EXT, files, digest, verify, write_json
from live2d_studio.production_audit import save_audit
from phase4a_acceptance import wait_url, stop

SOURCE=Path('/home/zelli/tools/ai/SillyTavern')
PACKAGE=REPO/'runs/phase4a-acceptance-v4/girl2'


def run(args):
    if not re.fullmatch('[a-z0-9-]+',args.run_id):raise ValueError('Invalid run ID')
    output=REPO/'runs'/('phase4a2-'+args.run_id);output.mkdir()
    save_audit(SOURCE,PACKAGE,output/'production-before.json')
    verify(PACKAGE)
    report=dict(phase='4A.2',production_enabled=False,real_llm_inference=False,classifier_integration='blocked',scenarios={},restoration={})
    def command(argv,label,expected=0):
        with (output/(label+'.log')).open('w') as log:
            p=subprocess.run(argv,cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
        if p.returncode!=expected:raise RuntimeError(f'{label}: exit {p.returncode}, expected {expected}')
    try:
        for variant in ['upstream','adapter']:
            runroot=tx.TEST_BASES[0]/(args.run_id+'-'+variant)
            root=runroot/'instance';record=runroot/'transactions/girl2'
            command(['python3','scripts/prepare_st_smoke.py','--source',str(SOURCE),'--extension',str(SOURCE/EXT),'--destination',str(root)],variant+'-prepare')
            (root/tx.MARKER).write_text(json.dumps(dict(root=str(root),purpose='phase4a2-disposable')))
            rootdev=root.stat().st_dev;pkgdev=PACKAGE.stat().st_dev
            fs=subprocess.check_output(['findmnt','-n','-o','FSTYPE','-T',str(root)],text=True).strip()
            if rootdev==pkgdev or fs!='btrfs':raise ValueError('Real ext4-to-Btrfs test requires separate devices and Btrfs target')
            report['filesystems']=dict(source_device=pkgdev,target_device=rootdev,target_fstype=fs)
            baseline=files(root/EXT);assets=files(root/tx.ASSETS)
            original=tx.snapshot(root/EXT/'live2d.js')
            dry=installer.deploy(PACKAGE,root,record,name='phase3',adapter=variant=='adapter')
            write_json(output/(variant+'-plan.json'),dry)
            assert not record.exists()
            installer.deploy(PACKAGE,root,record,name='phase3',adapter=variant=='adapter',execute=True)
            serverlog=(output/(variant+'-server.log')).open('w');chromelog=(output/(variant+'-chrome.log')).open('w')
            server=subprocess.Popen(['node','server.js','--listen','false','--port',str(args.port),'--browserLaunchEnabled','false'],cwd=root,stdout=serverlog,stderr=subprocess.STDOUT)
            chrome=None
            try:
                wait_url(f'http://127.0.0.1:{args.port}/',server)
                profile=runroot/'chrome'
                chrome=subprocess.Popen(['/opt/google/chrome/chrome','--headless=new',f'--user-data-dir={profile}',
                    '--remote-debugging-address=127.0.0.1',f'--remote-debugging-port={args.cdp_port}',
                    '--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-component-update',
                    '--disable-sync','--enable-unsafe-swiftshader','--use-angle=swiftshader','--window-size=1280,900','about:blank'],stdout=chromelog,stderr=subprocess.STDOUT)
                wait_url(f'http://127.0.0.1:{args.cdp_port}/json/version',chrome)
                modes=['rp','lifecycle','failure','llm-blocked']
                if variant=='adapter':modes+=['race','visual','expressions']
                for mode in modes:
                    label=variant+'-'+mode;dest=output/label
                    command(['node','scripts/cdp_smoke.mjs',f'http://127.0.0.1:{args.cdp_port}',
                        f'http://127.0.0.1:{args.port}/?qaAsset=phase3&mode={mode}&adapter={int(variant=="adapter")}',
                        'scripts/phase3_browser_scenario.js',str(dest),'--mock-startup-classifier'],label,
                        expected=1 if variant=='upstream' and mode=='failure' else 0)
                    result=json.loads((dest/'result.json').read_text())['result']['value']
                    report['scenarios'][label]={k:result.get(k) for k in ['status','network_validation','mapping_checks','idle_recovered','switch_removed','provider_preserved','actual_fallback','mouth_pixel_changes']}
            finally:
                if chrome:stop(chrome)
                stop(server);serverlog.close();chromelog.close()
            # No browser data reset needed: transaction must preserve even newly created settings.
            settings=files(root/'data/default-user');settings={k:v for k,v in settings.items() if not k.startswith(('assets/','extensions/'))}
            command(['python3',str(record/'recover.py'),'--dry-run'],variant+'-recovery-dry-run')
            # Actually hide the entire project mount from the standalone helper.
            command(['bwrap','--die-with-parent','--ro-bind','/','/','--tmpfs','/data','--bind',str(runroot),str(runroot),
                     '--chdir','/tmp','/usr/bin/python3','-I',str(record/'recover.py'),'--execute'],variant+'-recovery-without-data')
            assert files(root/EXT)==baseline and files(root/tx.ASSETS)==assets
            assert tx.snapshot(root/EXT/'live2d.js')==original
            current=files(root/'data/default-user');current={k:v for k,v in current.items() if not k.startswith(('assets/','extensions/'))}
            assert current==settings
            report['restoration'][variant]=dict(file_hashes=True,original_extension_metadata=True,
                browser_created_settings_preserved=True,project_hidden_by_mount_namespace=True,
                transaction=str(record))
        report['status']='pass-with-classifier-blocker'
    finally:
        # A failed browser assertion must not leave an installed disposable package.
        # Use the immutable helper shipped with that transaction's engine version.
        for variant in ['upstream','adapter']:
            pending=tx.TEST_BASES[0]/(args.run_id+'-'+variant)/'transactions/girl2'
            journal=pending/'journal.json'
            if journal.exists() and json.loads(journal.read_text())['status']!='rolled-back':
                command(['python3',str(pending/'recover.py'),'--execute'],variant+'-failure-recovery')
        save_audit(SOURCE,PACKAGE,output/'production-after.json')
        write_json(output/'integration.json',report)
    print(output)


def verify_removal(args):
    output=REPO/'runs'/('phase4a2-'+args.run_id)
    for variant in ['upstream','adapter']:
        runroot=tx.TEST_BASES[0]/(args.run_id+'-'+variant)
        root=runroot/'instance'; record=runroot/'transactions/girl2'
        tx.guard(root,record)
        if json.loads((record/'journal.json').read_text())['status']!='rolled-back':raise ValueError('Rollback required')
        dest=output/(variant+'-uninstall');dest.mkdir()
        serverlog=(dest/'server.log').open('w');chromelog=(dest/'chrome.log').open('w')
        server=subprocess.Popen(['node','server.js','--listen','false','--port',str(args.port),'--browserLaunchEnabled','false'],cwd=root,stdout=serverlog,stderr=subprocess.STDOUT)
        chrome=None
        try:
            wait_url(f'http://127.0.0.1:{args.port}/',server)
            chrome=subprocess.Popen(['/opt/google/chrome/chrome','--headless=new',f'--user-data-dir={runroot / "chrome-uninstall"}',
                '--remote-debugging-address=127.0.0.1',f'--remote-debugging-port={args.cdp_port}',
                '--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-component-update',
                '--disable-sync','--enable-unsafe-swiftshader','--use-angle=swiftshader','--window-size=1280,900','about:blank'],stdout=chromelog,stderr=subprocess.STDOUT)
            wait_url(f'http://127.0.0.1:{args.cdp_port}/json/version',chrome)
            with (dest/'cdp.log').open('w') as log:
                subprocess.run(['node','scripts/cdp_smoke.mjs',f'http://127.0.0.1:{args.cdp_port}',f'http://127.0.0.1:{args.port}/',
                    'scripts/phase4a_uninstall_scenario.js',str(dest/'browser'),'--mock-startup-classifier'],cwd=REPO,stdout=log,stderr=subprocess.STDOUT,check=True)
        finally:
            if chrome:stop(chrome)
            stop(server);serverlog.close();chromelog.close()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-id',required=True)
    p.add_argument('--port',type=int,default=8772);p.add_argument('--cdp-port',type=int,default=9232)
    p.add_argument('--verify-removal-only',action='store_true')
    args=p.parse_args()
    if not args.verify_removal_only:run(args)
    verify_removal(args)
