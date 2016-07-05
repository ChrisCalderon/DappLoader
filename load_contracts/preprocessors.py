# TODO: add registry to live network and put address here
REG_ADDR = "0x0"


class PreprocessorError(Exception): pass


def macro_preprocessor(dapp_namespace):
    """Replaces import statements with an address macro."""
    for name in dapp_namespace:
        contract_info = dapp_namespace[name]
        dep_code = []
        for var_name in contract_info['dependencies']:
            dep_name = contract_info['dependencies'][var_name]
            dep_addr = dapp_namespace[dep_name]['address']
            dep_code.append(dapp_namespace[dep_name]['signature'])
            dep_code.append('macro {}: {}'.format(var_name, dep_addr))
        dep_code.extend(contract_info['temp_code'])
        contract_info['processed_code'] = '\n'.join(dep_code)


def registry_preprocessor(dapp_namespace, controller):
    """Replaces import statements with registry lookups + global variables.

    `controller` is an address which will own the registry used and be able
    to change/update the addresses."""
    lookup_fmt = '    {{}} = {}.lookup({}, "{{}}")'.format(REG_ADDR, controller)
    for name in dapp_namespace:
        contract_info = dapp_namespace[name]
        any_code = ['def any():']
        for var_name in contract_info['dependencies']:
            dep_key = contract_info['dependencies'][var_name]
            any_code.append(lookup_fmt.format(var_name, dep_key))

        any_code.extend(contract_info['temp_code'])
        contract_info['processed_code'] = '\n'.join(any_code)
