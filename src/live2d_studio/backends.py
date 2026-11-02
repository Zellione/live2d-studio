"""Backend boundary: the baseline stays in-process; neural inference is isolated."""
BACKENDS = ('deterministic', 'see-through')


def prepare(source, output, rights, backend='deterministic', decomposition=None):
    if backend == 'deterministic':
        if decomposition is not None:
            raise ValueError('The deterministic backend does not accept decomposition metadata')
        from .pipeline import prepare as baseline
        return baseline(source,output,rights)
    if backend == 'see-through':
        if decomposition is None:
            raise ValueError('Run the isolated See-through worker first and pass --decomposition its bridge directory')
        from .seethrough import import_decomposition
        return import_decomposition(source, output, rights, decomposition)
    raise ValueError('Unknown backend: '+backend)
