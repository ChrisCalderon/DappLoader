from setuptools import setup
import json

with open('config.json') as cfg:
    config = json.load(cfg)


def is_http(req):
    """Checks if a requirement is a link."""
    return req.startswith('http://') or req.startswith('https://')


def dep_sorter(rs, r):
    """Appends the requirement r to the proper list."""
    print rs, r
    if is_http(r):
        rs[1].append(r)
    else:
        rs[0].append(r)
    return rs

with open('requirements.txt') as reqs:
    requirements, links = reduce(dep_sorter,
                                 filter(None,
                                        [r.strip() for r in reqs]),
                                 [[],[]])

config['install_requires'] = requirements
config['dependency_links'] = links
setup(**config)
