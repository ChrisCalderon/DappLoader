from collections import OrderedDict
from os.path import basename
import rlp
import sha3

class Namespace(OrderedDict):
    """A namespace for a dapp."""
    def __init__(self, creator):
        self.creator = creator

    def add_source(self, path):
        """Add a source file to the namespace."""
        code_name = basename(path).rstrip('.se')
        address_seed = rlp.encode([self.creator, len(self)])
        address = '0x' + sha3.sha3_256(address_seed).hexdigest()[24:]
        self[code_name] = {'path': path, 'address': address}
