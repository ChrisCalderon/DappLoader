import rlp
import os
import re
import sha3
from collections import OrderedDict
from load_contracts.preprocessors import macro_preprocessor, registry_preprocessor

MAX_GAS = '0x47e7c4'
ETH_ADDR = re.compile('^0x[0-9a-f]{40}$')


class CompilerError(Exception): pass


def path_to_name(path):
    """Turns a path into a name for the dapp namespace."""
    return os.path.basename(path).rstrip('.se')


def sanitized(contract_info):
    """Readies 'raw_code' for preprocessing."""
    dependencies = {}
    temp_code = []
    for line in contract_info['raw_code']:
        if line.startswith('import'):
            name, var_name = line.lstrip('import ').split(' as ')
            dependencies[var_name] = name
        else:
            temp_code.append(line)
    return {'dependencies': dependencies,
            'temp_code': temp_code,
            'signature': serpent.mk_signature('\n'.join(temp_code))}


def send_tx(rpc_client, tx):
    pass


def compile_dapp(sources, blocktime, , creator, controller):
    """Compiles a serpent dapp.

    Arguments:
    sources       --   A iterable of paths to Serpent contracts to compile.
    blocktime     --   Amount of time in seconds to wait before sending
                       each contract.
    rpc_client    --   An rpc client object connected to an Ethereum node.
    creator       --   Address to use for contract creation.
    controller    --   The owner of the registry and whitelist. If None,
                       no registry or whitelist are created and contracts
                       have addresses of dependencies added as macros. If
                       the name of a contract in the dapp, that contract
                       will control the registry and whitelist used by
                       the dapp. If a valid Ethereum address, the address
                       will control the registry and whitelist.
    """
    rpc_client = rpctools.rpc_client_factory(rpc_address)
    
    if creator is None:
        creator = rpc_client.eth_coinbase()['result']
        
    if ETH_ADDR.match(creator):
        raw_creator_address = creator[2:].decode('hex')
    else:
        err_msg = "Invalid creator address: {}"
        raise CompilerError(err_msg.format(creator))

    dapp_namespace = OrderedDict((path_to_name(p),{'path': p}) for p in sources)
    start_nonce = int(rpc_client.eth_getTransactionCount(creator)['result'][2:], 16)
    for i, name in enumerate(dapp_namespace):
        contract_info = dapp_namespace[name]
        addr_seed = rlp.encode([raw_creator_address, start_nonce + i])
        contract_info['address'] = '0x' + sha3.sha3_256(addr_seed).hexdigest()[24:]
        contract_info['raw_code'] = open(contract_info['path']).read().split('\n')
        
    for name in dapp_namespace:
        contract_info = dapp_namespace[name]
        contract_info.update(sanitized(contract_info))

    if controller is None:
        macro_preprocessor(dapp_namespace)
    else:
        if controller in dapp_namespace:
            controller = dapp_namespace[controller]['address']
        if ETH_ADDR.match(controller):
            registry_preprocessor(dapp_namespace, controller)
        else:
            raise CompilerError("Invalid controller: {}".format(controller))

    if controller is not None:
        # TODO: make python module for registry and use it here.
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
