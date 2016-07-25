"""A class for holding contract metadata."""

class CodeInfo:
    __slots__ = ('address',
                 'serpent_sig',
                 'abi_sig',
                 'dependencies',
                 'path',
                 'code')
    def __init__(self):
        pass