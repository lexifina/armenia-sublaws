"""Which ARLIS corpus the Armenian scripts work on.

    laws     (default)  Constitution, codes and laws          -> lexifina/armenia-law,     am/national/acts
    sublaws             normative government and prime-minister decisions and ministerial orders
                                                              -> lexifina/armenia-sublaws, am/national/sublaws

Every script takes `--set sublaws`; it is passed on to child processes in the environment variable ARMENIA_SET, so
the parser's worker processes read the same cache. With the default, every script behaves exactly as before.
"""
import os
import sys

NAME = os.environ.get('ARMENIA_SET', 'laws')


def from_argv() -> str:
    """Read `--set NAME` from the command line (before argparse runs) and export it for child processes."""
    global NAME
    argv = sys.argv
    for i, a in enumerate(argv):
        if a == '--set' and i + 1 < len(argv):
            NAME = argv[i + 1]
            del argv[i:i + 2]
            break
        if a.startswith('--set='):
            NAME = a.split('=', 1)[1]
            del argv[i]
            break
    if NAME not in ('laws', 'sublaws'):
        sys.exit(f'unknown set {NAME!r}: laws or sublaws')
    os.environ['ARMENIA_SET'] = NAME
    return NAME


# Read at import, so module-level paths (CACHE) see it; scripts call from_argv() again harmlessly.
from_argv()
SUBLAWS = NAME == 'sublaws'
