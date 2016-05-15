from serpent_tests import Tester
import rpctools
import rlp
import os
import stat
import re
import sys
import sha3
import time
import traceback
import socket


class CompilerError(Exception): pass


class Compiler(object):

    gas = '0x2fefd8' # pi million :^)
    http_pattern = re.compile('((?P<ip>^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})|(?P<host>^\w+)):(?P<port>\d{1,5}$)')
    ethaddr_pattern = re.compile('^0x[0-9a-f]{40}$')
    import_pattern = re.compile('^import (?P<module>\S+) as (?P<name>\S+)$')
    
    def __init__(self, rpc_address, sources=('src',), recursive=True, blocktime=12.0, build='build', chdir=None, creator='', controller=''):
        '''Compiles a group of Serpent contracts.

        Arguments:
        rpcAddress -- The address of an Ethereum node to connect to. Only paths to UDSes and host:port strings are acceptable.
        sources -- A list of paths to search for Serpent contracts.
        recursive -- Search the sources recursively for contracts.
        blocktime -- Amount of time in seconds to wait before sending each contract. Can be float.
        build -- Name of the directory to write build data to.
        chdir -- Relative paths in the "sources" argument are relative to this path.
        creator -- Ethereum address to use for creating the contracts.
        controller -- Specifies how to control access to contracts.

        The "controller" argument changes the behavior of the Compiler class a lot depending on it's value.
        There are three ways intra-contract access can work in a Dapp. The first, simplest way is that each contract
        can contain the address of every other contract in the Dapp that it needs to use. In this scenario, each
        "import <contract> as <name>" line gets translated into "macro <name>: <contract address>" before the contracts are compiled.
        This is the default behavior, and this is what happens when the "controller" isn't specified. Another supported way of 
        organizing intra-contract access is to use a registry contract to hold key -> address mappings which are owned by a single address.
        These mappings are then used by each contract to look up the address of every other contract in the Dapp which they need to 
        access. If the "controller" is an address, then it is used in conjunction with a registry contract in the way just described,
        with the specified address used as the owner. A JSON file filled with the neccesary transactions is then put into a file called 
        registry.json which the owner of the "controller" address must use to set the proper entries in the registry in order for the
        contracts to work. If, instead of an address, the "controller" is the name of a contract in the Dapp, then that contract's address
        will be used as the owner, and it will have code added to it "init" function which set's up it's registry.

        If there is no contract named "registry.se" in the Dapp and the Ethereum node is running on the main network, then a registry
        contract on the main network is used. If it is running on a test network, then a registry contract is downloaded and added to the
        Dapp.
        '''
        
        m = Compiler.http_pattern.match(rpc_address)
        if m:
            d = m.groupdict()
            ip = d['ip']
            addr = ip if ip else d['host'], int(d['port'])
            self.rpc_address = addr
            self.RpcClass = rpctools.HTTPRPCClient
        elif Compiler.is_uds_addr(rpc_address): 
            self.rpc_address = rpc_address
            self.RpcClass = rpctools.IPCRPCClient
        else:
            raise CompilerError('Invalid rpc address: {}'.format(rpc_address))
        self.rpc_client = None

        if ethaddress.match(creator):
            self.creator_address = creator
            self.raw_creator_address = creator[2:].decode('hex')
        else:
            self.creator_address = None
            self.raw_creator_address = None

        self.sources = sources
        self.recursive = recursive
        self.build = build
        self.chdir = chdir
        self.blocktime = blocktime

        self.contract_info = []
        self.shortcuts = {}

    def get_creator_address(self):
        creator = self.rpc_client.eth_coinbase()['result']
        self.creator_address = creator
        self.raw_creator_address = creator[2:].decode('hex')

    def normalize_paths(self):
        '''Makes all paths in sources point to absolute paths.'''
        # This is called at the start of the compiling process to make sure all the
        # paths exist and to make them easier to work with.
        chdir = self.chdir
        if chdir and os.path.isdir(chdir):
            chdir = self.chdir = os.path.realpath(chdir)
        elif chdir:
            raise CompilerError('chdir path does not exist: {}'.format(repr(chdir)))
        else:
            chdir = self.chdir = os.getcwd()

        sources = []
        for src_dir in self.sources:
            if not src_dir.startswith('/'):
                sources.append(os.path.join(chdir, src_dir))
            else:
                sources.append(src_dir)

        if all(map(os.path.isdir, sources)):
            self.sources = map(os.path.realpath, sources)
        else:
            bad_paths = ', '.join(map(repr,
                                      filter(lambda p: not os.path.isdir(p),
                                             sources)))
            raise CompilerError('These source paths aren\'t directories: {}'.format(bad_paths))

    @staticmethod
    def is_uds_addr(path):
        '''True if path is the location of an existing Unix Domain Socket.'''
        return os.path.isfile(path) and stat.S_ISSOCK(os.stat(path).st_mode)

    @staticmethod
    def gas_estimate(code):
        '''Estimates the gas cost of putting Serpent code on the blockchain.'''
        return Tester(code).gas_cost

    def add_source_path(self, dirname, basename):
        if basename.endswith('.se'):
            path = os.path.join(dirname, basename)
            if os.path.isfile(path):
                c_info = {'path': path}
                self.contract_info.append(c_info)

    def get_source_paths(self):
        '''Finds the paths in the supplied source directories that are Serpent contracts.'''
        for src_dir in self.sources:
            if self.recursive:
                for directory, subdirs, files in os.walk(src_dir):
                    for f in files:
                        self.add_source_path(directory, f)
            else:
                for path in os.path.listdir(src_dir):
                    self.add_source_path(src_dir, path)

    def assign_addresses(self):
        '''Computed the address address for each source file.'''
        tx_nonce = self.rpc_client.eth_getTransactionCount(self.creator_address)['result']
        for i, c_info in enumerate(self.contract_info):
            seed_data = rlp.encode([self.raw_creator_address, tx_nonce + i])
            address = '0x' + sha3.sha3_256(seed_data).digest()[12:].encode('hex')
            c_info['address'] = address

    def populate_shortcuts(self):
        for c_info in self.contract_info:
            shortcut = os.path.basename(c_info['path'])[:-3]
            self.shortcuts[shortcut] = c_info

    def preprocess_with_macros(self):
        '''Default strategy for dealing with intra-Dapp contract access.'''
        for c_info in self.contract_info:
            with open(c_info['path']) as f:
                new_code = []
                for line in f:
                    m = Compiler.import_pattern.match(line)
                    if m:
                        d = m.groupdict()
                        shortcut = d['module']
                        macro = d['name']
                        address = self.shortcuts[shortcut]['address']
                        new_line = 'macro {}: {}\n'.format(macro, address)
                        new_code.append(new_line)
                    else:
                        new_code.append(line)
                c_info['new_code'] = ''.join(new_code)
        
    def preprocess_with_controller_address(self):
        pass

    def preprocess_with_controller_contract(self):
        pass

# Code that needs to be rewritten

# def broadcast_code(rpc_client, evm, creator_address, gas):
#     '''Sends compiled code to the network, and returns the address.'''
#     tx = {'from':creator_address, 'data':evm, 'gas':gas}
#     result = rpc_client.eth_sendTransaction(tx)

#     if 'error' in result:
#         code = result['error']['code']
#         message = result['error']['message']
#         if code == -32603 and message == 'Exceeds block gas limit':
#             if cost_estimate(code) < rpc.MAXGAS:
#                 time.sleep(BLOCKTIME)
#                 return broadcast_code(evm, code, fullname)
#             else:
#                 print '%s costs too much to compile!' % fullname
#         else:
#                 print 'UNKNOWN ERROR'
#                 print json.dumps(result, indent=4, sort_keys=True)
#                 print 'ABORTING'
#                 print 'code:'
#                 print code
#                 print 'DB:'
#                 print json.dumps(DB, indent=4, sort_keys=True)
#                 dump = open('load_contracts_FATAL_dump.json', 'w')
#                 print>>dump, json.dumps(DB, indent=4, sort_keys=True)
#                 sys.exit(1)
                
#     txhash = result['result']
#                 tries = 0
#     while tries < TRIES:
#                 time.sleep(BLOCKTIME)
#                 receipt = RPC.eth_getTransactionReceipt(txhash)["result"]
#         if receipt is not None:
#                 check = RPC.eth_getCode(receipt["contractAddress"])['result']
#             if check != '0x' and check[2:] in evm:
#                 return receipt["contractAddress"]
#                 tries += 1
#                 user_input = raw_input("broadcast failed after %d tries! Try again? [Y/n]" % tries)
#     if user_input in 'Yy':
#         return broadcast_code(evm, code, fullname)
#                 print 'ABORTING'
#                 print json.dumps(DB, indent=4, sort_keys=True)
#                 sys.exit(1)

            
# def optimize_deps(deps, contract_nodes):
#                 '''When a contract is specified for recompiling with -c, this is called
#     to filter the compile order of the contracts so that only the specified
#     contract, and every contract dependent on it, are recompiled.'''
#                 new_deps = [CONTRACT]

#     for i in range(deps.index(CONTRACT) + 1, len(deps)):
#                 node = deps[i]
#         for new_dep in new_deps:
#             if new_dep in contract_nodes[node]:
#                 new_deps.append(node)
#                 break

#     return new_deps
