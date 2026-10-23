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
        
    if subcmd == 'create' and isinstance(res, dict) and res.get('status') == 'interactive_plan_required':
        print(f"\n📋 TerraMod 1.4 Interactive Creation Menu")
        print("==========================================")
        for q in res.get('interview_questions', []):
            print(f"\n❓ {q['question']}")
            print("------------------------------------------")
            for opt in q.get('options', []):
                cmd_tag = f" [{opt['command']}]" if 'command' in opt else ""
                print(f"  • {opt['name']}{cmd_tag}")
                if 'summary' in opt:
                    print(f"    Info: {opt['summary']}")
                if 'idea' in opt:
                    print(f"    💡 Idea: {opt['idea']}")
                print()
        print("Syntax: teramod create <Type> <Name>")
        print("Examples:")
        print("  teramod create Mechanic HeatSystem")
        print("  teramod create UI ManaHUD")
        print("  teramod create Armor VoidSet")
        print("  teramod create Sword FrostBrand")
        print("  teramod create Project NewMod\n")
        return
        
    if subcmd == 'create' and isinstance(res, dict) and res.get('status') == 'created':
        print(f"\n✨ Generated {res.get('kind', 'Content')} '{res.get('name')}':")
        for f in res.get('files_created', [res.get('path')]):
            print(f"  • {f}")
        print(f"\n{res.get('preview', '')}\n")
        return
        
    print(json.dumps(res, indent=2))

if __name__ == '__main__':
    main()
