#!/usr/bin/env python3
"""
server.py
TerraMod Model Context Protocol (MCP) Server.
Provides complete tModLoader 1.4 decompilation, knowledge graph access, and mod inspection.
Standard JSON-RPC 2.0 stdio transport (zero external dependencies).
"""
import os
import sys
import json
import sqlite3
import subprocess
from typing import Dict, Any, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "tmod_1_4.db")

# Import unpacker
sys.path.insert(0, SCRIPT_DIR)
from tmod_extractor import unpack_tmod

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- Tool Implementations ---

def tool_get_class_hooks(class_name: str) -> Dict[str, Any]:
    conn = get_db()
    cur = conn.cursor()
    pattern = f"%{class_name}"
    cur.execute('''
    SELECT n.id, n.name, n.data
    FROM edges e
    JOIN nodes n ON e.target_id = n.id
    WHERE e.source_id LIKE ? AND e.relationship = 'EXPOSES_HOOK'
    ORDER BY n.name ASC
    ''', (pattern,))
    rows = cur.fetchall()
    conn.close()
    hooks = []
    for r in rows:
        data = json.loads(r['data'])
        hooks.append({
            "hook": r['name'],
            "signature": data.get('signature', ''),
            "return_type": data.get('return_type', ''),
            "parameters": data.get('params', ''),
            "summary": data.get('summary', '')
        })
    return {
        "class_name": class_name,
        "hook_count": len(hooks),
        "hooks": hooks
    }

def tool_check_1_3_migration(code_or_symbol: str) -> Dict[str, Any]:
    conn = get_db()
    cur = conn.cursor()
    matches = []
    cur.execute("SELECT name, data FROM nodes WHERE label = 'Legacy13'")
    for r in cur.fetchall():
        name = r['name']
        data = json.loads(r['data'])
        if name.lower() in code_or_symbol.lower() or any(term.lower() in code_or_symbol.lower() for term in name.split('.')):
            matches.append({
                "legacy_pattern": name,
                "replaced_by": data.get('replaced_by', ''),
                "note": data.get('note', ''),
                "kind": data.get('kind', '')
            })
    conn.close()
    return {
        "query": code_or_symbol,
        "found_obsolete_patterns": len(matches) > 0,
        "replacements": matches
    }

def tool_get_example_snippet(topic: str) -> Dict[str, Any]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
    SELECT id, name, data FROM nodes
    WHERE label = 'Snippet' AND (name LIKE ? OR id LIKE ?)
    LIMIT 5
    ''', (f"%{topic}%", f"%{topic}%"))
    rows = cur.fetchall()
    conn.close()
    snippets = []
    for r in rows:
        data = json.loads(r['data'])
        snippets.append({
            "file": data.get('file', ''),
            "code_preview": data.get('code', '')
        })
    return {
        "topic": topic,
        "matches_count": len(snippets),
        "snippets": snippets
    }

def tool_tmod_unpack(tmod_path: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
    return unpack_tmod(tmod_path, output_dir)

def tool_tmod_decompile(assembly_or_extracted_dir: str, output_source_dir: Optional[str] = None) -> Dict[str, Any]:
    dll_path = assembly_or_extracted_dir
    if os.path.isdir(assembly_or_extracted_dir):
        dlls = [os.path.join(assembly_or_extracted_dir, f) for f in os.listdir(assembly_or_extracted_dir) if f.endswith('.dll')]
        if not dlls:
            raise FileNotFoundError(f"No .dll found in directory {assembly_or_extracted_dir}")
        dll_path = dlls[0]
        
    if not os.path.exists(dll_path):
        raise FileNotFoundError(f"DLL not found: {dll_path}")
        
    if output_source_dir is None:
        base = os.path.splitext(dll_path)[0]
        output_source_dir = f"{base}_src"
        
    os.makedirs(output_source_dir, exist_ok=True)
    cmd = ["ilspycmd", "--disable-updatecheck", "--nested-directories", "-p", "-o", output_source_dir, dll_path]
    subprocess.run(cmd, capture_output=True, text=True, check=True)
    
    cs_files = []
    for r, _, files in os.walk(output_source_dir):
        for f in files:
            if f.endswith('.cs'):
                cs_files.append(os.path.relpath(os.path.join(r, f), output_source_dir))
                
    return {
        "assembly": dll_path,
        "output_dir": output_source_dir,
        "status": "decompiled",
        "cs_file_count": len(cs_files),
        "files_sample": cs_files[:25]
    }

def tool_tmod_scan(source_dir: str) -> Dict[str, Any]:
    if not os.path.exists(source_dir):
        raise FileNotFoundError(f"Directory not found: {source_dir}")
        
    items, npcs, projectiles, buffs, hjson_files = [], [], [], [], []
    for root, _, files in os.walk(source_dir):
        for f in files:
            if f.endswith('.cs'):
                fp = os.path.join(root, f)
                try:
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as src:
                        content = src.read()
                        if ': ModItem' in content:
                            items.append(f)
                        elif ': ModNPC' in content:
                            npcs.append(f)
                        elif ': ModProjectile' in content:
                            projectiles.append(f)
                        elif ': ModBuff' in content:
                            buffs.append(f)
                except Exception:
                    pass
            elif f.endswith('.hjson'):
                hjson_files.append(os.path.relpath(os.path.join(root, f), source_dir))
                
    return {
        "directory": source_dir,
        "summary": {
            "items_count": len(items),
            "npcs_count": len(npcs),
            "projectiles_count": len(projectiles),
            "buffs_count": len(buffs)
        },
        "mod_items": items,
        "mod_npcs": npcs,
        "mod_projectiles": projectiles,
        "mod_buffs": buffs,
        "localization_files": hjson_files
    }

TOOLS_METADATA = [
    {
        "name": "get_class_hooks",
        "description": "List all overridable 1.4 virtual/abstract hooks, signatures, and docs for a ModLoader class (e.g. ModItem, ModNPC, ModPlayer, ModSystem)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "class_name": {"type": "string", "description": "Target class name (e.g. ModItem, ModNPC, GlobalItem)"}
            },
            "required": ["class_name"]
        }
    },
    {
        "name": "check_1_3_migration",
        "description": "Check code or symbol against 260+ obsolete 1.3 patterns and receive exact 1.4 replacements (anti-hallucination)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "code_or_symbol": {"type": "string", "description": "Code snippet, method call, or property name to test"}
            },
            "required": ["code_or_symbol"]
        }
    },
    {
        "name": "get_example_snippet",
        "description": "Search ground-truth ExampleMod 1.4 C# implementations (e.g. Sword, Gun, Minion, Boss, Tile)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Topic keyword (e.g. Sword, Armor, Accessory, Minion)"}
            },
            "required": ["topic"]
        }
    },
    {
        "name": "tmod_unpack",
        "description": "Unpacks a binary .tmod file into assets, DLL assembly, and manifest",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tmod_path": {"type": "string", "description": "Path to .tmod archive"},
                "output_dir": {"type": "string", "description": "Optional output directory"}
            },
            "required": ["tmod_path"]
        }
    },
    {
        "name": "tmod_decompile",
        "description": "Decompiles a mod's .dll assembly into editable C# project files using ilspycmd",
        "inputSchema": {
            "type": "object",
            "properties": {
                "assembly_or_extracted_dir": {"type": "string", "description": "Path to .dll file or directory containing extracted mod files"},
                "output_source_dir": {"type": "string", "description": "Optional destination directory for decompiled C# source"}
            },
            "required": ["assembly_or_extracted_dir"]
        }
    },
    {
        "name": "tmod_scan",
        "description": "Scans decompiled mod source directory, summarizing all ModItems, ModNPCs, ModProjectiles, Buffs, and Hjson files",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source_dir": {"type": "string", "description": "Directory of decompiled mod C# project"}
            },
            "required": ["source_dir"]
        }
    }
]

DISPATCHER = {
    "get_class_hooks": lambda args: tool_get_class_hooks(args.get("class_name", "")),
    "check_1_3_migration": lambda args: tool_check_1_3_migration(args.get("code_or_symbol", "")),
    "get_example_snippet": lambda args: tool_get_example_snippet(args.get("topic", "")),
    "tmod_unpack": lambda args: tool_tmod_unpack(args.get("tmod_path", ""), args.get("output_dir")),
    "tmod_decompile": lambda args: tool_tmod_decompile(args.get("assembly_or_extracted_dir", ""), args.get("output_source_dir")),
    "tmod_scan": lambda args: tool_tmod_scan(args.get("source_dir", ""))
}

def send_response(resp: Dict[str, Any]):
    body = json.dumps(resp)
    sys.stdout.write(body + "\n")
    sys.stdout.flush()

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue
            
        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})
        
        if method == "initialize":
            send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "teramod", "version": "1.0.0"}
                }
            })
        elif method == "notifications/initialized":
            pass
        elif method == "ping":
            send_response({"jsonrpc": "2.0", "id": req_id, "result": {}})
        elif method == "tools/list":
            send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": TOOLS_METADATA}
            })
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            if tool_name not in DISPATCHER:
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Tool not found: {tool_name}"}
                })
            else:
                try:
                    res = DISPATCHER[tool_name](tool_args)
                    send_response({
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [{"type": "text", "text": json.dumps(res, indent=2)}],
                            "isError": False
                        }
                    })
                except Exception as e:
                    send_response({
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                            "isError": True
                        }
                    })
        else:
            if req_id is not None:
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                })

if __name__ == '__main__':
    main()
