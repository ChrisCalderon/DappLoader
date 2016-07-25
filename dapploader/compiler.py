MAX_GAS = '0x47e7c4'
ETH_ADDR = re.compile('^0x[0-9a-f]{40}$')


class CompilerError(Exception): pass


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


def compile_dapp(sender, namespace, preprocessor):
    """Compiles a Serpent Dapp.

    Arguments:
    sender -- A sender object for sending transactions to the network.
    namespace -- A Namespace object for the contracts in the Dapp.
    preprocessor -- A Preprocessor object for translating import statements.
    """
        




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
