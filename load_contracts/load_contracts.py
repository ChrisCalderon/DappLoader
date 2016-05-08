#!/usr/bin/env python
"""Preprocesses and compiles Serpent projects, then uploads them to the Ethereum network."""
from serpent_tests import Tester
import rpctools
import os
import stat
import re
import sys
import sha3
import time
import shutil
import traceback
import argparse


class CompilerError(Exception): pass


class Compiler(object):
    gas = '0x2fefd8'
    testnet = {'ipc': os.path.join(os.environ['HOME'], '.testnet', 'geth.ipc'),
               'http': 'localhost:9090'}
    http = re.compile('^(?:\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|[\w.])+:\d{1,5}$')
    ethaddress = re.compile('^x[0-9a-f]{40}$')
    
    def __init__(self, args, creator=''):
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
            raise CompilerError('Invalid address for rpc client: {}'.format(address))

        if not eth.match(creator):
            self.creator_address = self.rpc_client.eth_coinbase()['result']
        else:
            self.creator_address = creator
            
    def parse_args(self):
        """Parses command line options and positional arguments."""
        parser = argparse.ArgumentParser(description=__doc__)
        backend = parser.add_mutually_exclusive_group(required=True)
        backend.add_argument('-a', '--address', help='Address for JSON  RPC server. Must be either host:port or path/to/geth.ipc', default=None)
        backend.add_argument('-t', '--testnet', help='Use the defaults for a geth node started with the testnet script.', choices=['ipc', 'http'], default='ipc')
        parser.add_argument('-b', '--blocktime', type=float, default=12.0, metavar='T', help='Time to wait between contract submissions.')
        parser.add_argument('-B', '--build', help='Specifies the name of the build directory.', default='build')
        parser.add_argument('-c', '--contract', help='The name of a contract to recompile.')
        parser.add_argument('-C', '--chdir', help='Run the script as if from the supplied directory.')
        parser.add_argument('-R', '--recursive', help='Search the supplied source directories recursively for contracts.', default=False, action='store_true')
        parser.add_argument('-s', '--source', help='The directory to search for Serpent code, or a config file', action='append')
        parser.add_argument('-v', '--verbose', help='Prints all JSONRPC messages to stdout.')
        self.args = parser.parse_args(self.call_args)
        
    @staticmethod
    def gas_estimate(code):
        '''Estimates the gas cost of putting Serpent code on the blockchain.'''
        return Tester(code).gas_cost

    def get_contract_info(self):
        #TODO: iterate through self.args.source and search each directory for .se files
        pass
    
def broadcast_code(rpc_client, evm, creator_address, gas):
    '''Sends compiled code to the network, and returns the address.'''
    tx = {'from':creator_address, 'data':evm, 'gas':gas}
    result = rpc_client.eth_sendTransaction(tx)
    if 'error' in result:
        code = result['error']['code']
        message = result['error']['message']
        if code == -32603 and message == 'Exceeds block gas limit':
            if cost_estimate(code) < rpc.MAXGAS:
                time.sleep(BLOCKTIME)
                return broadcast_code(evm, code, fullname)
            else:
                print '%s costs too much to compile!' % fullname
        else:
            print 'UNKNOWN ERROR'
            print json.dumps(result, indent=4, sort_keys=True)
        print 'ABORTING'
        print 'code:'
        print code
        print 'DB:'
        print json.dumps(DB, indent=4, sort_keys=True)
        dump = open('load_contracts_FATAL_dump.json', 'w')
        print>>dump, json.dumps(DB, indent=4, sort_keys=True)
        sys.exit(1)
            
    txhash = result['result']
    tries = 0
    while tries < TRIES:
        time.sleep(BLOCKTIME)
        receipt = RPC.eth_getTransactionReceipt(txhash)["result"]
        if receipt is not None:
            check = RPC.eth_getCode(receipt["contractAddress"])['result']
            if check != '0x' and check[2:] in evm:
                return receipt["contractAddress"]
        tries += 1
    user_input = raw_input("broadcast failed after %d tries! Try again? [Y/n]" % tries)
    if user_input in 'Yy':
        return broadcast_code(evm, code, fullname)
    print 'ABORTING'
    print json.dumps(DB, indent=4, sort_keys=True)
    sys.exit(1)

            
def optimize_deps(deps, contract_nodes):
    '''When a contract is specified for recompiling with -c, this is called
    to filter the compile order of the contracts so that only the specified
    contract, and every contract dependent on it, are recompiled.'''
    new_deps = [CONTRACT]

    for i in range(deps.index(CONTRACT) + 1, len(deps)):
        node = deps[i]
        for new_dep in new_deps:
            if new_dep in contract_nodes[node]:
                new_deps.append(node)
                break

    return new_deps


def main():
    read_options()
    deps, nodes = get_compile_order()
    if TRANSLATE:
        global SOURCE
        shutil.copytree(SOURCE, TRANSLATE)
        SOURCE = TRANSLATE
        for fullname in map(get_fullname, deps):
            print 'translating', fullname
            new_code = process_imports(fullname)
            with open(fullname, 'w') as f:
                f.write(new_code)
        return 0
    if CONTRACT is not None:
        deps = optimize_deps(deps, nodes)
    for fullname in map(get_fullname, deps):
        print "compiling", fullname
        sys.stdout.flush()
        compile(fullname)
    rpc.save_db(DB)

if __name__ == '__main__':
    sys.exit(main())
