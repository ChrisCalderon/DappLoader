#!/usr/bin/env python
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


class CompilerError(Exception): pass


class Compiler(object):
    gas = '0x2fefd8'
    testnet = {'ipc': os.path.join(os.environ['HOME'], '.testnet', 'geth.ipc'),
               'http': 'localhost:9090'}
    http = re.compile('^(?:\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|[\w.])+:\d{1,5}$')
    ethaddress = re.compile('^0x[0-9a-f]{40}$')
    
    def __init__(self, , creator=''):
        self.call_args = args
        self.parse_args()

        if self.args.address is not None:
            address = self.args.address
        else:
            address = self.testnet[self.args.testnet]

        if os.path.isfile(address) and stat.S_ISSOCK(os.stat(address).st_mode):
            self.rpc_client = rpctools.IPCRPCClient(address)
        elif http.match(address):
            self.rpc_client = rpctools.HTTPRPCClient(address)
        else:
            raise CompilerError('Invalid rpc address: {}'.format(address))

        if not ethaddress.match(creator):
            self.creator_address = self.rpc_client.eth_coinbase()['result']
        else:
            self.creator_address = creator

        self.raw_creator_address = self.creator_address[2:].decode('hex')

        self.contract_info = []
        
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
        for src_dir in self.args.source:
            if self.args.chdir:
                src_dir = os.path.normpath(os.path.join(self.args.chdir, src_dir))

            if not os.path.isdir(src_dir):
                raise CompilerError('Source path is not a directory: {}'.format(directory))

            if self.args.recursive:
                for directory, subdirs, files in os.walk(src_dir):
                    for f in files:
                        self.add_source_path(directory, f)
            else:
                for path in os.path.listdir(src_dir):
                    self.add_source_path(src_dir, path)

    def assign_addresses(self):
        '''Computed the address address for each source file.'''
        tx_nonce = self.rpc.eth_getTransactionCount(self.creator_address)['result']
        for i, c_info in enumerate(self.contract_info):
            seed_data = rlp.encode([self.raw_creator_address, tx_nonce + i])
            address = '0x' + sha3.sha3_256(seed_data).digest()[12:].encode('hex')
            c_info['address'] = address

    def preprocess_code(self):
        ''''''


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
