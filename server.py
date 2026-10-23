#!/usr/bin/env python3
"""
teramod_mcp.py
TerraMod Model Context Protocol (MCP) Server.
Provides: 
- Knowledge graph queries (hooks, classes, anti-hallucination migration rules, snippets)
- .tmod file unpacking
- Mod assembly decompilation via ilspycmd
- Mod scanning & inspection
- Mod building & validation
"""
import os
import sys
import json
import sqlite3
import subprocess
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "tmod_1_4.db")

# Import unpacker from local repo
sys.path.insert(0, SCRIPT_DIR)
from tmod_extractor import unpack_tmod

mcp = FastMCP("TerraMod", dependencies=["mcp", "pydantic"])

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@mcp.tool()
def get_class_hooks(class_name: str) -> Dict[str, Any]:
    """
    List all overridable 1.4 virtual/abstract hooks, signatures, and documentation for a ModLoader class
    (e.g., 'ModItem', 'ModNPC', 'ModProjectile', 'GlobalItem', 'ModPlayer', 'ModSystem').
    """
    conn = get_db()
    cur = conn.cursor()
    
    # Match with or without namespace
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

@mcp.tool()
def check_1_3_migration(code_or_symbol: str) -> Dict[str, Any]:
    """
    Checks whether a symbol, method, or code line contains obsolete 1.3 patterns
    (e.g., 'item.melee', 'StrikeNPC', 'OnHitNPC', 'ModRecipe') and provides the canonical 1.4 replacement.
    """
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

@mcp.tool()
def get_example_snippet(topic: str) -> Dict[str, Any]:
    """
    Search ground-truth tModLoader 1.4 ExampleMod implementation snippets (e.g. 'Sword', 'Minion', 'Boss', 'Gun', 'Accessory').
    """
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

@mcp.tool()
def tmod_unpack(tmod_path: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Unpacks a Terraria .tmod archive file into its constituent DLLs, textures, sounds, and localization files.
    """
    try:
        return unpack_tmod(tmod_path, output_dir)
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def tmod_decompile(assembly_or_extracted_dir: str, output_source_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Decompiles a mod's .dll assembly into editable C# source files using ilspycmd.
    """
    dll_path = assembly_or_extracted_dir
    if os.path.isdir(assembly_or_extracted_dir):
        dlls = [os.path.join(assembly_or_extracted_dir, f) for f in os.listdir(assembly_or_extracted_dir) if f.endswith('.dll')]
        if not dlls:
            return {"error": f"No .dll found in directory {assembly_or_extracted_dir}"}
        dll_path = dlls[0]
        
    if not os.path.exists(dll_path):
        return {"error": f"DLL not found: {dll_path}"}
        
    if output_source_dir is None:
        base = os.path.splitext(dll_path)[0]
        output_source_dir = f"{base}_src"
        
    os.makedirs(output_source_dir, exist_ok=True)
    cmd = ["ilspycmd", "--disable-updatecheck", "--nested-directories", "-p", "-o", output_source_dir, dll_path]
    
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Count generated .cs files
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
            "files_sample": cs_files[:20]
        }
    except subprocess.CalledProcessError as e:
        return {"error": f"ilspycmd failed: {e.stderr}"}

@mcp.tool()
def tmod_scan(source_dir: str) -> Dict[str, Any]:
    """
    Scans an extracted or decompiled mod project, summarizing all Items, NPCs, Projectiles, Buffs, and Recipes.
    """
    if not os.path.exists(source_dir):
        return {"error": f"Directory not found: {source_dir}"}
        
    items = []
    npcs = []
    projectiles = []
    buffs = []
    hjson_files = []
    
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
        "mod_items": items,
        "mod_npcs": npcs,
        "mod_projectiles": projectiles,
        "mod_buffs": buffs,
        "localization_files": hjson_files,
        "summary": {
            "items_count": len(items),
            "npcs_count": len(npcs),
            "projectiles_count": len(projectiles),
            "buffs_count": len(buffs)
        }
    }

if __name__ == '__main__':
    mcp.run()
