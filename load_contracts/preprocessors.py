import os
import serpent


class PreProcessorError(Exception): pass


class SimplePreProcessor(object):
    """A simple address macro preprocessor."""
    def __init__(self, code_info, build_dir):
        """Make a preprocessor that maps imports to macros.

        Arguments:
        code_info - a list of dictionaries, containing the keys
                    'addr' and 'path'.
        build_dir - """
        self.build_dir = build_dir
        self.code_info = code_info
        self.name_to_info = {}
        for info in code_info:
            name = os.path.basename(info['path']).rstrip('.se')
            self.name_to_info[name] = info

    def do_preprocess(self):
        """Generates code that is ready to compile from known contract info."""
        dependencies = {}
        sanitized = {}
        signatures = {}
        # first pass generates signatures.
        for name, info in self.name_to_info.items():
            with open(info['path']) as original_code_file:
                original_code = original_code_file.read().split('\n')

            sanitized[name] = []
            dependencies[name] = []
            for line in original_code:
                if line.startswith('import'):
                    dependencies[name].append(line)
                else:
                    sanitized[name].append(line)

            sanitized_code = '\n'.join(sanitized[name])
            signatures[name] = serpent.mk_signature(sanitized_code)

        # second pass adds macros and signatures,
        # now that the signatures have been generated.
        for name, info in self.name_to_info:
            dep_code = []
            for dep in dependencies[name]:
                dep_name, macro = dep.lstrip('import ').split(' as ')
                sig = signatures[dep_name]
                addr = self.name_to_info[dep_name]['addr']
                dep_code.append(sig)
                dep_code.append('macro {}: {}'.format(macro, addr))
            
            dep_code.extend(sanitized_code[name])
            info['processed_code'] = '\n'.join(dep_code)
