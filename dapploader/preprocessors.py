"""This module defines functions which preprocess Serpent code.
It transforms import statments into the appropriate native Serpent mechanism.
"""
import serpent
# TODO: add registry to live network and put address here
REG_ADDR = "0x0"


class PreprocessorError(Exception): pass


class Preprocessor(object):
    """Processes imports statements into Serpent code."""

    def __init__(self, namespace):
        self.namespace = namespace

    def parse_dependencies(self):
        """Separates code and import statements."""
        for name in self.namespace:
            contract_info = self.namespace[name]
            path = contract_info['path']
            source = open(path)
            stripped_code = []
            dependencies = []
            for line in source:
                if line.startswith('import'):
                    parts = line.split(' ')
                    dep_name = parts[1]
                    code_alias = parts[3]
                    dependency_address = self[dep_name]['address']
                    dependencies.append((code_alias, dependency_address))
                else:
                    stripped_code.append(line)
            stripped_code = '\n'.join(stripped_code)
            self.namespace[]
            yield stripped_code, dependencies, serpent.mk_signature(stripped_code)


class MacroPreprocessor(Preprocessor):
    """Replaces import statements with Serpent macros."""
    def preprocess(self):
        for stripped_code, dependencies in self.sanitized():
            macro_code = []
            for alias, address, signature in dependencies:
                macro = 'macro {}: {}'.format(alias, address)
                macro_code.append(macro)
                macro_code.append(signature)
            macro_code = '\n'.join(macro_code)
            self.namespace

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


def preprocess(dapp_namespace, controller):
    """Chooses which preprocessor to use based on the controller."""

    if controller is None:
        return macro_preprocessor(dapp_namespace)

    if controller in dapp_namespace:
        controller = dapp_namespace[controller]['address']

    return registry_preprocessor(dapp_namespace, controller)
