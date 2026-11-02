"""Fresh isolated install/browser/uninstall acceptance; generated output stays local.

Run with uv run --frozen python scripts/phase4a_acceptance.py --run-id NAME.
Production is only read for copying code and SHA-256 comparisons.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import urllib.request

from live2d_studio.packaging import REPO, EXT, CORE, digest, files, write_json
from live2d_studio.rp_qa import evaluate
from live2d_studio.deployment import isolated


def snapshot_production(source):
    # Hash only: never deserialize production settings, chats or credentials.
    roots = [source / 'src', source / 'public', source / EXT, source / 'data/default-user/assets/live2d']
    result = {}
    for root in roots:
        if root.exists():
            for p in sorted(root.rglob('*')):
                if p.is_file() and '.git' not in p.parts:
                    result[str(p.relative_to(source))] = digest(p)
    for name in ['package.json', 'data/default-user/settings.json']:
        p=source/name
        if p.exists(): result[name]=digest(p)
    return result


def wait_url(url, process):
    for _ in range(120):
        if process.poll() is not None: raise RuntimeError('Server/browser exited; see log')
        try:
            with urllib.request.urlopen(url, timeout=1) as r:
                if r.status == 200: return
        except OSError: pass
        time.sleep(.5)
    raise RuntimeError('Local service did not become ready')


def stop(proc):
    proc.terminate()
    try: proc.wait(timeout=10)
    except subprocess.TimeoutExpired: proc.kill(); proc.wait()


def verify_uninstall(args):
    """Reboot restored copies and query the real asset API; restore test-only data."""
    output=REPO/'runs'/('phase4a-'+args.run_id)
    for variant in ['upstream','adapter']:
        root=isolated(REPO/'.cache'/f'phase4a-{args.run_id}-{variant}')
        if (root/'.phase4a-active.json').exists():raise ValueError('Rollback must finish first')
        result=output/(variant+'-uninstall');result.mkdir()
        baseline=files(root/'data')
        shutil.copytree(root/'data',result/'data-before')
        server_log=(result/'server.log').open('w');browser_log=(result/'chrome.log').open('w')
        server=subprocess.Popen(['node','server.js','--listen','false','--port',str(args.port),'--browserLaunchEnabled','false'],cwd=root,stdout=server_log,stderr=subprocess.STDOUT)
        browser=None
        try:
            wait_url(f'http://127.0.0.1:{args.port}/',server)
            profile=REPO/'.cache'/f'phase4a-{args.run_id}-{variant}-uninstall-chrome'
            if profile.exists():raise FileExistsError(profile)
            browser=subprocess.Popen(['/opt/google/chrome/chrome','--headless=new',f'--user-data-dir={profile}',
                '--remote-debugging-address=127.0.0.1',f'--remote-debugging-port={args.cdp_port}',
                '--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-component-update',
                '--disable-sync','--enable-unsafe-swiftshader','--use-angle=swiftshader','--window-size=1280,900','about:blank'],stdout=browser_log,stderr=subprocess.STDOUT)
            wait_url(f'http://127.0.0.1:{args.cdp_port}/json/version',browser)
            with (result/'cdp.log').open('w') as log:
                subprocess.run(['node','scripts/cdp_smoke.mjs',f'http://127.0.0.1:{args.cdp_port}',f'http://127.0.0.1:{args.port}/',
                    'scripts/phase4a_uninstall_scenario.js',str(result/'browser'),'--mock-startup-classifier'],cwd=REPO,stdout=log,stderr=subprocess.STDOUT,check=True)
        finally:
            if browser:stop(browser)
            stop(server);server_log.close();browser_log.close()
            # Only this marked disposable instance; retain all data rather than delete it.
            os.rename(root/'data',result/'data-after')
            shutil.copytree(result/'data-before',root/'data')
        assert files(root/'data')==baseline
        write_json(result/'restoration.json',dict(exact_data_hashes=True,browser_fixture_reset=True))


def run(args):
    os.environ.setdefault('UV_CACHE_DIR',str(REPO/'.cache/uv'))
    output=REPO/'runs'/('phase4a-'+args.run_id)
    output.mkdir()
    before=snapshot_production(args.source)
    write_json(output/'production-before.json',before)
    commands=[]
    def command(argv, label, expected=0):
        commands.append(argv)
        with (output/(label+'.log')).open('w') as log:
            p=subprocess.run(argv,cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
        if p.returncode!=expected:raise RuntimeError(f'{label}: exit {p.returncode}, expected {expected}')
    cli=['uv','run','--frozen','live2d-studio']
    command(['uv','run','--frozen','python','-m','unittest','discover','-s','tests','-v'],'regression-python')
    command(['node','tests/test_rp_talk.mjs'],'regression-js')
    package=output/'girl2'
    command([*cli,'package','--output',str(package),'--core',str(args.source/CORE)],'package')
    command([*cli,'package','--output',str(output/'girl2-replay'),'--core',str(args.source/CORE)],'package-replay')
    assert files(package)==files(output/'girl2-replay')
    report=dict(phase='4A',starting_commit='a106c5f',package_reproducible=True,production_authorized=False,
                real_classifier_inference=False,audio_lipsync=False,scenarios={},restoration={})
    try:
        for variant in ['upstream','adapter']:
            root=REPO/'.cache'/f'phase4a-{args.run_id}-{variant}'
            command(['python3','scripts/prepare_st_smoke.py','--phase4a','--source',str(args.source),
                     '--extension',str(args.source/EXT),'--destination',str(root)],variant+'-prepare')
            # The legacy goldens run against this independent unmodified copy.
            shutil.copytree(REPO/'tests/fixtures/phase1/final/runtime',root/'data/default-user/assets/live2d/phase1')
            pristine=files(root/'data')
            record=output/(variant+'-deployment')
            deploy=[*cli,'deploy','--package',str(package),'--target',str(root),'--record',str(record),'--name','phase3']
            if variant=='adapter':deploy+=['--adapter']
            command([*deploy,'--dry-run'],variant+'-dry-run')
            assert files(root/'data')==pristine and not record.exists()
            command([*deploy,'--execute'],variant+'-deploy')
            deployed=files(root/'data')
            # Browser-created state belongs to the disposable test fixture, not the installer.
            # Preserve it, then reset only non-assets/non-extension data before uninstall.
            user=root/'data/default-user'
            fixture=output/(variant+'-fixture-before-browser')
            shutil.copytree(root/'data',fixture)
            server_log=(output/(variant+'-server.log')).open('w')
            browser_log=(output/(variant+'-chrome.log')).open('w')
            server=subprocess.Popen(['node','server.js','--listen','false','--port',str(args.port),'--browserLaunchEnabled','false'],cwd=root,stdout=server_log,stderr=subprocess.STDOUT)
            browser=None
            try:
                wait_url(f'http://127.0.0.1:{args.port}/',server)
                profile=REPO/'.cache'/f'phase4a-{args.run_id}-{variant}-chrome'
                if profile.exists():raise FileExistsError(profile)
                browser=subprocess.Popen(['/opt/google/chrome/chrome','--headless=new',f'--user-data-dir={profile}',
                    '--remote-debugging-address=127.0.0.1',f'--remote-debugging-port={args.cdp_port}',
                    '--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-component-update',
                    '--disable-sync','--enable-unsafe-swiftshader','--use-angle=swiftshader','--window-size=1280,900','about:blank'],stdout=browser_log,stderr=subprocess.STDOUT)
                wait_url(f'http://127.0.0.1:{args.cdp_port}/json/version',browser)
                modes=['rp','lifecycle','failure','race','visual','expressions'] if variant=='adapter' else ['rp','lifecycle','failure']
                for mode in modes:
                    dest=output/(variant+'-'+mode)
                    command(['node','scripts/cdp_smoke.mjs',f'http://127.0.0.1:{args.cdp_port}',
                        f'http://127.0.0.1:{args.port}/?qaAsset=phase3&mode={mode}&adapter={int(variant=="adapter")}',
                        'scripts/phase3_browser_scenario.js',str(dest),'--mock-startup-classifier'],variant+'-'+mode,
                        expected=1 if variant=='upstream' and mode=='failure' else 0)
                    r=json.loads((dest/'result.json').read_text())['result']['value']
                    report['scenarios'][variant+'-'+mode]=dict(status=r['status'],network=r['network_validation'],
                        mapping_count=len(r.get('mapping_checks',{})),idle_recovered=r.get('idle_recovered'),switch_removed=r.get('switch_removed'),
                        raw_opacity_excursions=sum(g['rawOpacityExcursions'] for g in r['geometry'].values()),
                        mouth_pixel_changes=r.get('mouth_pixel_changes'),evidence=str(dest.relative_to(REPO)))
                if variant=='upstream':
                    failure=report['scenarios']['upstream-failure']
                    assert failure['status']=='fail' and failure['network']['caught_event_listener_errors']>0
                    for phase,script in [('phase0','st_browser_scenario.js'),('phase1','phase1_browser_scenario.js')]:
                        command(['node','scripts/cdp_smoke.mjs',f'http://127.0.0.1:{args.cdp_port}',f'http://127.0.0.1:{args.port}/',
                                 'scripts/'+script,str(output/phase),'--mock-startup-classifier'],phase)
                else:
                    results={m:json.loads((output/('adapter-'+m)/'result.json').read_text())['result']['value'] for m in ['rp','lifecycle','failure','race','visual']}
                    report['rp_acceptance']=evaluate(results)
                    assert not report['rp_acceptance']['failures']
            finally:
                if browser:stop(browser)
                stop(server);server_log.close();browser_log.close()
            # Preserve all browser changes. Restore only fixture-owned non-deployment state.
            shutil.copytree(root/'data',output/(variant+'-browser-data-after'))
            for child in list((root/'data').iterdir()):
                if child.name=='default-user':
                    for p in list(child.iterdir()):
                        if p.name not in {'assets','extensions'}:
                            if p.is_dir():shutil.rmtree(p)
                            else:p.unlink()
                elif child.is_dir():shutil.rmtree(child)
                else:child.unlink()
            for child in fixture.iterdir():
                if child.name=='default-user':
                    for p in child.iterdir():
                        if p.name not in {'assets','extensions'}:
                            dest=user/p.name
                            if p.is_dir():shutil.copytree(p,dest)
                            else:shutil.copy2(p,dest)
                elif child.is_dir():shutil.copytree(child,root/'data'/child.name)
                else:shutil.copy2(child,root/'data'/child.name)
            command([*cli,'rollback','--record',str(record),'--dry-run'],variant+'-rollback-dry-run')
            assert files(root/'data')==deployed
            command([*cli,'rollback','--record',str(record),'--execute'],variant+'-rollback')
            assert files(root/'data')==pristine
            report['restoration'][variant]=dict(data_files_exact=True,model_absent=not(root/'data/default-user/assets/live2d/phase3').exists(),
                upstream_live2d_sha256=digest(root/EXT/'live2d.js'),browser_fixture_reset=True,
                settings_written_by_installer=False)
        verify_uninstall(args)
        report['status']='pass'
    finally:
        after=snapshot_production(args.source)
        write_json(output/'production-after.json',after)
        report['production_hashes_unchanged']=before==after
        report['production_files_checked']=len(before)
        write_json(output/'commands.json',commands)
        write_json(output/'integration.json',report)
    assert report['production_hashes_unchanged']
    print(output)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=Path('/home/zelli/tools/ai/SillyTavern'))
    p.add_argument('--run-id',required=True)
    p.add_argument('--port',type=int,default=8766)
    p.add_argument('--cdp-port',type=int,default=9227)
    p.add_argument('--verify-uninstall-only',action='store_true')
    args=p.parse_args()
    args.source=args.source.resolve()
    import re
    if not re.fullmatch('[a-z0-9-]+',args.run_id):p.error('Simple lowercase run ID required')
    if args.verify_uninstall_only:verify_uninstall(args)
    else:run(args)
