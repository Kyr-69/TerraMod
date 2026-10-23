#!/usr/bin/env python3
"""
cli.py
TerraMod command-line interface.
Provides direct shell access to all TerraMod capabilities.
"""
import os
import sys
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from server import tool_teramod

def main():
    args = sys.argv[1:]
    if not args or args[0] in ['-h', '--help', 'help']:
        res = tool_teramod('help')
        print(f"\n=== {res['title']} ===\n")
        for cmd in res['available_commands']:
            print(f"  {cmd['command']:<38} {cmd['description']}")
        print()
        return

    subcmd = args[0]
    target = args[1] if len(args) > 1 else None
    extra = args[2] if len(args) > 2 else None
    
    res = tool_teramod(subcmd, target, extra)
    if isinstance(res, dict) and 'error' in res:
        print(f"Error: {res['error']}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(res, indent=2))

if __name__ == '__main__':
    main()
