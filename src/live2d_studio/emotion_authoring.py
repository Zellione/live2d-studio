"""Optional source-relative expression candidate; never promotes a reviewed model."""
import json
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
from .generic_rig import inspect, overview, objects, targets, axis_steps
from .manifest import load_validate, write_json, digest

CHANNELS = ('ParamBrowLIncline', 'ParamBrowRIncline', 'ParamBrowLRaise',
            'ParamBrowRRaise', 'ParamMouthSkew', 'ParamMouthDispleasure')


def bounds(rgba):
    y, x = np.nonzero(np.asarray(rgba)[..., 3] > 0)
    if len(x) < 4:
        raise ValueError('Insufficient facial support')
    return np.array([x.min(), y.min(), x.max()+1, y.max()+1], dtype=float)


def brow_shapes(brow, mouth, source_slope=0):
    """Inner end comes from source position, not anatomical side naming.

    y-down shear preserves width/thickness; its amplitude is a fraction of brow
    width. The separate raise axis translates the entire brow without inclination.
    """
    w, h = brow[2:] - brow[:2]
    center = (brow[:2]+brow[2:])/2
    nose_x = (mouth[0]+mouth[2])/2
    if w <= 0 or h <= 0 or abs(center[0]-nose_x) < .3*w:
        raise ValueError('Cannot identify inner eyebrow end')
    direction = 1 if center[0] < nose_x else -1
    # Positive inclination lowers the inner tip and draws the whole brow inward.
    slope = (direction*.25-source_slope)*.5*w/h
    controls = [-slope, -slope/3, slope/3, slope]
    inclination = [(v, [dict(type='curve', axis='y', controls=[c*v for c in controls]),
                         dict(type='translate', delta=[direction*.06*v, .06*w/h*v])])
                   for v in (-1, 1)]
    raising = [(v, [dict(type='translate', delta=[0, -.22*w/h*v])]) for v in (-1, 1)]
    return inclination, raising


def mouth_baseline(rgba):
    """Fit both disconnected source seam halves, never extrapolate one corner."""
    b=bounds(rgba);width=b[2]-b[0]
    a=np.asarray(rgba);support=a[...,3]>127;lum=a[...,:3].mean(2)
    low,high=np.quantile(lum[support],[.05,.9])
    y,x=np.nonzero(support & (lum<low+.5*(high-low)))
    xs=np.unique(x)
    if len(xs)<6 or xs.max()-xs.min()<.65*width:
        raise ValueError('Insufficient bilateral mouth contour')
    ys=np.array([np.mean(y[x==v]) for v in xs]);u=(xs-b[0])/width
    # A bounded quadratic avoids cubic extrapolation through the centre gap.
    poly=np.polyfit(u,ys,2);grid=np.linspace(0,1,41)
    from .transition_authoring import bernstein
    fit=np.linalg.lstsq(bernstein(grid),np.polyval(poly,grid),rcond=None)[0]
    if np.ptp(np.polyval(poly,grid))>.4*width:
        raise ValueError('Unsupported source mouth curvature')
    return fit,width,float(np.mean(ys))


def cheek_tint(face, eyes, mouth):
    """Gaussian tint on supported cheek interiors, located only from facial parts."""
    f = np.asarray(face)
    mb = bounds(mouth)
    eb = sorted([bounds(e) for e in eyes], key=lambda b: b[0])
    separation = (eb[1][0]+eb[1][2]-eb[0][0]-eb[0][2])/2
    my = (mb[1]+mb[3])/2
    if separation <= 0 or any(my <= e[3] for e in eb):
        raise ValueError('Eye/mouth ordering cannot locate cheeks')
    y, x = np.indices(f.shape[:2])
    safe = distance_transform_edt(f[..., 3] > 127)
    alpha = np.zeros(f.shape[:2]); centers = []
    for b in eb:
        cx = (b[0]+b[2])/2
        cy = b[3]+.43*(my-b[3])
        rx = min(.20*separation, .43*(b[2]-b[0]))
        ry = min(.085*separation, .23*(my-b[3]))
        if min(rx, ry) < 1 or safe[int(cy), int(cx)] < ry:
            raise ValueError('Insufficient supported cheek interior')
        a = 64*np.exp(-2*((x-cx)/rx)**2-2*((y-cy)/ry)**2)
        alpha = np.maximum(alpha, a)
        centers.append(dict(x=float(cx), y=float(cy), radius_x=float(rx), radius_y=float(ry)))
    # Smoothly fade before face alpha boundaries; never a rectangular patch.
    alpha *= np.clip(safe/max(1, separation*.025), 0, 1)
    rgba = np.zeros_like(f); rgba[..., :3] = [229, 100, 111]
    rgba[..., 3] = np.rint(alpha).astype(np.uint8)
    return Image.fromarray(rgba), centers


def expression_entries(name, entries, blush=False):
    """Preserve the four unaffected poses and add explicit zero resets everywhere."""
    values = {k: 0 for k in CHANNELS}
    if blush:
        values['ParamBlush'] = 0
    changed = {
        'angry': dict(ParamMouthCurve=0, ParamMouthDispleasure=1, ParamBrowEmotion=0, ParamEyeLOpen=.88,
                      ParamEyeROpen=.88, ParamMouthOpenY=0,
                      ParamBrowLIncline=1, ParamBrowRIncline=1,
                      ParamBrowLRaise=-.15, ParamBrowRRaise=-.15),
        'confused': dict(ParamMouthCurve=0, ParamMouthDispleasure=.65, ParamBrowEmotion=0, ParamEyeLOpen=1,
                         ParamEyeROpen=.85, ParamMouthOpenY=.025,
                         ParamBrowLIncline=-.3, ParamBrowRIncline=.15,
                         ParamBrowLRaise=1, ParamBrowRRaise=-.3, ParamMouthSkew=.65),
        'embarrassed': dict(ParamMouthCurve=.6, ParamBrowEmotion=0, ParamEyeLOpen=.82,
                            ParamEyeROpen=.82, ParamMouthOpenY=.08,
                            ParamBrowLIncline=-.2, ParamBrowRIncline=-.2,
                            ParamBrowLRaise=.15, ParamBrowRRaise=.15, ParamMouthSkew=-.15),
    }.get(name, {})
    values.update(changed)
    if blush and name == 'embarrassed':
        values['ParamBlush'] = 1
    result = [dict(e, value=values.pop(e['parameter'], e['value'])) for e in entries]
    result += [dict(parameter=k, blend='ADD', value=v) for k, v in values.items()]
    return result


def install(client, op, layers, output, blush=True):
    manifest = load_validate(layers)
    data = overview(client)['data']; items = objects(client)
    bindings = targets(data, items)
    def source(role, side='none'):
        found = [l for l in manifest['layers'] if l['role']==role and l['side']==side]
        if len(found)!=1:
            raise ValueError('Ambiguous expression source: '+role+':'+side)
        layer = found[0]
        imported = [l for l in data['layers']['items'] if l['name']==layer['id']]
        meshes = [o for o in items if len(imported)==1 and o.get('layerId')==imported[0]['id'] and o['target'].startswith('mesh:')]
        if len(meshes)!=1:
            raise ValueError('Ambiguous expression mesh')
        rgba = Image.new('RGBA', (manifest['canvas']['width'], manifest['canvas']['height']))
        rgba.paste(Image.open(layers/layer['rgba_path']).convert('RGBA'), (layer['x'], layer['y']))
        return layer, imported[0], meshes[0], rgba
    mouth = source('mouth'); mb = bounds(mouth[3])
    evidence = dict(version='independent-expressions-v1', brows=[], generated_artwork=None)
    steps = []
    for side, letter in [('left','L'), ('right','R')]:
        layer, imported, mesh, rgba = source('eyebrow', side)
        detail = inspect(client, dict(target=mesh['target']))
        parent = inspect(client, dict(target=bindings['eyebrow:'+side]))
        if mesh['parentId'] != bindings['eyebrow:'+side].split(':',1)[1]:
            raise ValueError('Independent brows require fresh source meshes on inspected brow parents')
        topology = client.tool('workspace_call', dict(operation='mesh_get_topology',request=dict(target=mesh['target'],limit=4096)))['data']
        if topology.get('next_offset') is not None:
            raise ValueError('Truncated eyebrow topology')
        # Mesh edit units are its bounds. Convert source width/height using the
        # actual imported margin so a thin raster does not cause excessive shear.
        settings = inspect(client, dict(scope='layers', limit=64))
        if settings.get('next') is not None: raise ValueError('Truncated layer settings')
        margin = next(l for l in settings['items'] if l['id']==imported['id'])['mesh']['outerMargin']
        b = bounds(rgba); padded = b + np.array([-margin,-margin,margin,margin])
        from .transition_authoring import ink_curve
        xs, ys = ink_curve(np.asarray(rgba), isolated=True)
        source_slope = float(np.polyfit(xs-xs.mean(), ys, 1)[0])
        inclination, raising = brow_shapes(padded, mb, source_slope)
        steps += axis_steps(mesh['target'], detail['axes'], 'ParamBrow'+letter+'Incline', inclination)
        steps += axis_steps(mesh['target'], dict(detail['axes'], **{'ParamBrow'+letter+'Incline':[-1,0,1]}), 'ParamBrow'+letter+'Raise', raising)
        evidence['brows'].append(dict(side=side, source_sha256=digest(layers/layer['rgba_path']),
            source_bounds=b.tolist(), source_slope=source_slope, mesh=detail, parent=parent, topology=topology, margin=margin,
            inclination=inclination, raising=raising))
    target = bindings['mouth:none']; detail=inspect(client, dict(target=target))
    steps += axis_steps(target, detail['axes'], 'ParamMouthSkew', [
        (v, [dict(type='curve',axis='y',controls=[-.16*v,-.0533*v,.0533*v,.16*v])]) for v in (-1,1)])
    # Correct the source seam's measured smile, rather than assuming zero means
    # a straight mouth. Apply the same source-relative frown to source/cavity art.
    from .transition_authoring import ink_curve, bernstein
    art=json.loads((layers/'facial-artwork.json').read_text())
    variants=[v for v in art['alternatives'] if v['feature']=='mouth' and v['kind'] in ('source-neutral','interior')]
    if not variants:raise ValueError('Source-aware displeasure requires explicit neutral/cavity mouth artwork')
    fit, width, center = mouth_baseline(np.asarray(mouth[3]))
    desired=np.array([.065,-.065,-.065,.065])*width+center
    displacement=desired-fit
    for variant in variants:
        name='facial-mouth-'+variant['kind']
        layer_ids={l['id'] for l in data['layers']['items'] if l['name']==name}
        matches=[o for o in items if o.get('layerId') in layer_ids and o['target'].startswith('mesh:')]
        if len(matches)!=1:raise ValueError('Missing explicit mouth alternative')
        t=matches[0]['target'];d=inspect(client,dict(target=t))
        image=Image.open(layers/variant['path']).convert('RGBA');b=bounds(image)
        settings=inspect(client,dict(scope='layers',limit=64))
        margin=next(l for l in settings['items'] if l['id']==matches[0]['layerId'])['mesh']['outerMargin']
        b=b+np.array([-margin,-margin,margin,margin])
        x=np.linspace(b[0],b[2],41)
        co=np.linalg.lstsq(bernstein((x-b[0])/(b[2]-b[0])),bernstein((x-mb[0])/width)@displacement/(b[3]-b[1]),rcond=None)[0]
        if np.max(np.abs(co))>2:raise ValueError('Unbounded mouth contour correction')
        steps += axis_steps(t,d['axes'],'ParamMouthDispleasure',[(1,[dict(type='curve',axis='y',controls=co.tolist())])])
    evidence['mouth_correction']=dict(source_fit=fit.tolist(),target_fit=desired.tolist(),displacement=displacement.tolist())
    write_json(output/'expression-inspection.json', evidence)
    write_json(output/'expression-rig-recipe.json', steps)
    for step in steps:
        op.call(step['operation'], step['request'])
    if blush:
        face = source('face')
        try:
            png, centers = cheek_tint(face[3], [source('eyelash',s)[3] for s in ('left','right')], mouth[3])
        except ValueError as error:
            evidence['blush_skip_reason'] = str(error)
        else:
            png.save(output/'blush.png')
            result=lambda d:d.get('result',d)
            ref=result(op.call('asset_prepare_reference',dict(layer_id=face[1]['id'],piece_id='expression-blush',background_color='#FFFFFF',
                target_anchors={'origin':dict(x=0,y=0),'extent':dict(x=manifest['canvas']['width'],y=manifest['canvas']['height'])})))
            asset=result(op.call('asset_import_png',dict(reference_id=ref['id'],png_path=str(output/'blush.png'),require_transparency=True)))
            reg=result(op.call('asset_register',dict(asset_id=asset['assetId'],mode='absolute',transform=dict(x=0,y=0,scale_x=1,scale_y=1))))
            lid='agent:expression-blush'
            op.call('layer_add_from_asset',dict(asset_id=asset['assetId'],registration_id=reg['id'],layer_id=lid,name='Generated cheek tint',
                semantic_tag='unknown',parent_deformer_id=face[2]['parentId'],insertion=dict(mode='above',reference_layer_id=face[1]['id'])))
            found=[o for o in objects(client) if o.get('layerId')==lid and o['target'].startswith('mesh:')]
            if len(found)!=1:raise ValueError('Ambiguous blush mesh')
            t=found[0]['target']
            op.call('parameter_create',dict(parameter_id='ParamBlush',name='Cheek tint',min=0,max=1,default=0))
            op.call('keyform_apply',dict(changes=[dict(op='set',target=t,key={'ParamBlush':v},channels=dict(opacity=v)) for v in (0,1)]))
            order=inspect(client,dict(target=face[2]['target']))['static']['draw_order']
            op.call('rig_edit_structure',dict(edits=[dict(action='static',kind='mesh',id=t.split(':',1)[1],draw_order=int(order)+5)]))
            evidence['generated_artwork']=dict(path='blush.png',sha256=digest(output/'blush.png'),landmarks=centers,
                method='Gaussian transparent cheek tint; procedural CC0-1.0; adapted from expressive.blush_png',
                max_alpha=64, target=t,parent=face[2]['parentId'],neutral_opacity=0,source_pixels_changed=False,
                uncertainty='Placement inferred from reviewed semantic eye/mouth/face support; not anatomical truth')
    write_json(output/'expression-inspection.json', evidence)
    return bool(evidence['generated_artwork'])
