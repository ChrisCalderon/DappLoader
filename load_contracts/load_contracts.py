#!/usr/bin/env python
"""Preprocesses and compiles a Serpent project, then uploads it to the Ethereum network."""
import warnings; warnings.simplefilter('ignore')
import serpent
from ethereum import tester as t
import pyrpctools as rpc
import os
import sys
import sha3
import json
import time
import shutil
import traceback
import argparse


def parse_args():
    """Parses command line options and positional arguments."""
    epilog = '''\
'''
    parser = argparse.ArgumentParser(description=__doc__,
                                     epilog=)
    parser.add_argument('-b', '--blocktime', type=float, default=12.0, metavar='T', help='Time to wait between contract submissions.')
    parser.add_argument('-c', '--contract', help='The name of a contract to recompile.')
    parser.add_argument('-C', '--chdir', help='Run the script as if from the supplied directory.')
    backend = parser.add_mutually_exclusive_group()
    backend.add_argument('-H', '--http', help='IPv4 address:port for the geth node to connect to.')
    backend.add_argument('-i', '--ipc', help='Path to your Ethereum node\'s ipc socket.')
    parser.add_argument('-s', '--source', help='The directory to search for Serpent code, or a config file')
    parser.add_argument('-t', '--testnet', help='Use the defaults for a geth node started with the testnet script.', action='store_true', default=False)
    parser.add_argument('-v', '--verbose', help='Prints all JSONRPC messages to stdout.')
    
        
def get_fullname(shortname):
    '''
    Takes a short name from an import statement and
    returns a real path to that contract. The term
    "fullname" is used to refer to the full path of
    the contract file throughout this code. The term
    "shortname" is used to refer to the contract name
    alone, without the rest of the path info.
    '''
    for directory, subdirs, files in os.walk(SOURCE):
        for f in files:
            if f == shortname + '.se':
                return os.path.join(directory, f)
    raise ValueError('No such name: '+shortname)

def get_shortname(fullname):
    # the [:-3] is because all file names end in ".se"
    return os.path.basename(fullname)[:-3]

def cost_estimate(code):
    s = t.state()
    c = s.abi_contract(code)
    return s.block.gas_used

def broadcast_code(evm, code, fullname):
    '''Sends compiled code to the network, and returns the address.'''
    result = RPC.eth_sendTransaction(
        sender=COINBASE,
        data=evm,
        gas=rpc.MAXGAS)

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
