// Execute the installed extension's unmodified Cubism Core. No browser/render claim.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const [coreFile, mocFile] = process.argv.slice(2);
if (!coreFile || !mocFile) {
    console.error('Usage: node scripts/probe_core.cjs CORE_JS MODEL_MOC3');
    process.exit(2);
}
const coreSource = fs.readFileSync(coreFile);
const sandbox = {console: {...console, log: console.error}, require, process, Buffer,
    __dirname: path.dirname(path.resolve(coreFile)), __filename: path.resolve(coreFile),
    setTimeout, clearTimeout};
vm.createContext(sandbox);
vm.runInContext(coreSource.toString(), sandbox, {timeout: 10000});
setTimeout(() => {
    let moc, model;
    const report = {stage: 'cubism-core-only', render_tested: false,
        core_sha256: crypto.createHash('sha256').update(coreSource).digest('hex')};
    try {
        const core = sandbox.Live2DCubismCore;
        report.core_version = core.Version.csmGetVersion();
        report.latest_moc_version = core.Version.csmGetLatestMocVersion();
        const bytes = fs.readFileSync(mocFile);
        report.moc_sha256 = crypto.createHash('sha256').update(bytes).digest('hex');
        const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
        moc = core.Moc.fromArrayBuffer(buffer);
        if (!moc) throw Error('Installed Core rejected MOC');
        report.moc_version = core.Version.csmGetMocVersion(moc, buffer);
        model = core.Model.fromMoc(moc);
        if (!model) throw Error('Installed Core could not instantiate model');
        model.update();
        report.parameters = Array.from(model.parameters.ids);
        const required = ['ParamAngleX', 'ParamAngleY', 'ParamAngleZ', 'ParamBodyAngleX',
            'ParamBreath', 'ParamEyeBallX', 'ParamEyeBallY', 'ParamMouthOpenY',
            'ParamEyeLOpen', 'ParamEyeROpen'];
        report.missing_parameters = required.filter(id => !report.parameters.includes(id));
        if (report.missing_parameters.length) throw Error('Missing expected MVP parameter IDs');
        report.drawables = model.drawables.count;
        report.drawable_ids = Array.from(model.drawables.ids);
        if (!report.drawables) throw Error('No drawables');
        report.status = 'pass';
    } catch (error) {
        report.status = 'fail'; report.error = String(error); process.exitCode = 1;
    } finally {
        model?.release(); moc?._release();
        console.log(JSON.stringify(report, null, 2));
    }
}, 1000);
