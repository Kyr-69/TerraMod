#!/usr/bin/env python3
"""
server.py
TerraMod Model Context Protocol (MCP) Server.
Provides complete tModLoader 1.4 decompilation, knowledge graph access, mod inspection, build diagnostics, and /teramod prompt workflows.
Standard JSON-RPC 2.0 stdio transport (zero external dependencies).
"""
import os
import sys
import re
import json
import sqlite3
import subprocess
from typing import Dict, Any, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "tmod_1_4.db")
TMODLOADER_STEAM_DIR = "/home/Kyr/.local/share/Steam/steamapps/common/tModLoader"

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
    obsolete_patterns_found = []
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name, data FROM nodes WHERE label = 'Legacy13'")
    legacy_rules = [(r['name'], json.loads(r['data'])) for r in cur.fetchall()]
    conn.close()

    for root, _, files in os.walk(source_dir):
        for f in files:
            if f.endswith('.cs'):
                fp = os.path.join(root, f)
                rel_fp = os.path.relpath(fp, source_dir)
                try:
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as src:
                        content = src.read()
                        if ': ModItem' in content:
                            items.append(rel_fp)
                        elif ': ModNPC' in content:
                            npcs.append(rel_fp)
                        elif ': ModProjectile' in content:
                            projectiles.append(rel_fp)
                        elif ': ModBuff' in content:
                            buffs.append(rel_fp)
                            
                        for pat, meta in legacy_rules:
                            if pat in content:
                                obsolete_patterns_found.append({
                                    "file": rel_fp,
                                    "pattern": pat,
                                    "replaced_by": meta.get('replaced_by', ''),
                                    "note": meta.get('note', '')
                                })
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
            "buffs_count": len(buffs),
            "obsolete_patterns_count": len(obsolete_patterns_found)
        },
        "mod_items": items,
        "mod_npcs": npcs,
        "mod_projectiles": projectiles,
        "mod_buffs": buffs,
        "localization_files": hjson_files,
        "obsolete_1_3_findings": obsolete_patterns_found[:30]
    }

def tool_tmod_build(project_dir: str) -> Dict[str, Any]:
    """Runs dotnet build on a mod project, diagnosing compiler errors with 1.4 knowledge graph mappings."""
    if not os.path.exists(project_dir):
        raise FileNotFoundError(f"Directory not found: {project_dir}")
        
    csproj_files = [f for f in os.listdir(project_dir) if f.endswith('.csproj')] if os.path.isdir(project_dir) else []
    cmd = ["dotnet", "build", project_dir, "-c", "Debug"]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    stdout = res.stdout
    stderr = res.stderr
    
    # Parse errors: e.g. path(line,col): error CSxxxx: message
    error_lines = []
    for line in stdout.splitlines() + stderr.splitlines():
        if ': error CS' in line:
            error_lines.append(line.strip())
            
    # Cross-reference with legacy migration rules
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name, data FROM nodes WHERE label = 'Legacy13'")
    rules = [(r['name'], json.loads(r['data'])) for r in cur.fetchall()]
    conn.close()
    
    diagnostics = []
    for err in error_lines:
        diag = {"error": err, "matched_fix": None}
        for pat, meta in rules:
            if pat.lower() in err.lower():
                diag["matched_fix"] = {
                    "deprecated": pat,
                    "replaced_by": meta.get('replaced_by', ''),
                    "guidance": meta.get('note', '')
                }
                break
        diagnostics.append(diag)
        
    return {
        "project_dir": project_dir,
        "success": res.returncode == 0,
        "return_code": res.returncode,
        "error_count": len(error_lines),
        "diagnostics": diagnostics,
        "raw_output_tail": stdout.splitlines()[-15:] if stdout else []
    }

def tool_tmod_migrate(file_or_dir: str, dry_run: bool = False) -> Dict[str, Any]:
    """Batch refactors known 1.3 deprecated patterns into canonical 1.4 code."""
    if not os.path.exists(file_or_dir):
        raise FileNotFoundError(f"Path not found: {file_or_dir}")
        
    targets = []
    if os.path.isfile(file_or_dir):
        targets.append(file_or_dir)
    else:
        for root, _, files in os.walk(file_or_dir):
            for f in files:
                if f.endswith('.cs'):
                    targets.append(os.path.join(root, f))
                    
    # Safe regex replacements for standard 1.3 to 1.4 conversions
    replacements_map = [
        (r'\bitem\.melee\s*=\s*true\s*;', 'Item.DamageType = DamageClass.Melee;'),
        (r'\bitem\.magic\s*=\s*true\s*;', 'Item.DamageType = DamageClass.Magic;'),
        (r'\bitem\.ranged\s*=\s*true\s*;', 'Item.DamageType = DamageClass.Ranged;'),
        (r'\bitem\.summon\s*=\s*true\s*;', 'Item.DamageType = DamageClass.Summon;'),
        (r'\bitem\.thrown\s*=\s*true\s*;', 'Item.DamageType = DamageClass.Throwing;'),
        (r'\bitem\.knockBack\b', 'Item.knockBack'),
        (r'\bmod\.ItemType\(([^)]+)\)', r'ModContent.ItemType<\1>()'),
        (r'\bmod\.NPCType\(([^)]+)\)', r'ModContent.NPCType<\1>()'),
        (r'\bmod\.ProjectileType\(([^)]+)\)', r'ModContent.ProjectileType<\1>()'),
        (r'\bmod\.BuffType\(([^)]+)\)', r'ModContent.BuffType<\1>()'),
    ]
    
    modified_files = []
    for path in targets:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                original = f.read()
            modified = original
            changes = []
            for pat, repl in replacements_map:
                if re.search(pat, modified):
                    modified = re.sub(pat, repl, modified)
                    changes.append(f"{pat} -> {repl}")
                    
            if modified != original:
                if not dry_run:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(modified)
                modified_files.append({
                    "file": path,
                    "changes_count": len(changes),
                    "changes": changes
                })
        except Exception:
            pass
            
    return {
        "dry_run": dry_run,
        "scanned_files_count": len(targets),
        "modified_files_count": len(modified_files),
        "modified_files": modified_files
    }

def tool_tmod_create(kind: str, name: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
    """Scaffolds a compliant 1.4 ModItem, ModNPC, ModProjectile, or Boss file."""
    if output_dir is None:
        output_dir = os.getcwd()
    os.makedirs(output_dir, exist_ok=True)
    
    kind_lower = kind.lower()
    file_path = os.path.join(output_dir, f"{name}.cs")
    
    if kind_lower in ['item', 'sword', 'weapon']:
        content = f"""using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace MyMod.Items
{{
    public class {name} : ModItem
    {{
        public override void SetDefaults()
        {{
            Item.width = 40;
            Item.height = 40;
            Item.useTime = 20;
            Item.useAnimation = 20;
            Item.useStyle = ItemUseStyleID.Swing;
            Item.knockBack = 6f;
            Item.value = Item.buyPrice(gold: 1);
            Item.rare = ItemRarityID.Green;
            Item.UseSound = SoundID.Item1;
            Item.autoReuse = true;

            // Modern 1.4 DamageClass
            Item.DamageType = DamageClass.Melee;
            Item.damage = 25;
        }}

        public override void AddRecipes()
        {{
            // Modern 1.4 fluent recipe registration
            CreateRecipe()
                .AddIngredient(ItemID.Wood, 10)
                .AddTile(TileID.WorkBenches)
                .Register();
        }}
    }}
}}
"""
    elif kind_lower in ['npc', 'enemy', 'boss']:
        content = f"""using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace MyMod.NPCs
{{
    public class {name} : ModNPC
    {{
        public override void SetStaticDefaults()
        {{
            Main.npcFrameCount[NPC.type] = 4;
        }}

        public override void SetDefaults()
        {{
            NPC.width = 32;
            NPC.height = 32;
            NPC.damage = 20;
            NPC.defense = 6;
            NPC.lifeMax = 100;
            NPC.HitSound = SoundID.NPCHit1;
            NPC.DeathSound = SoundID.NPCDeath1;
            NPC.value = 60f;
            NPC.knockBackResist = 0.5f;
            NPC.aiStyle = -1; // Custom AI or 3 for Fighter
        }}
    }}
}}
"""
    else:
        content = f"""using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace MyMod.Projectiles
{{
    public class {name} : ModProjectile
    {{
        public override void SetDefaults()
        {{
            Projectile.width = 16;
            Projectile.height = 16;
            Projectile.friendly = true;
            Projectile.DamageType = DamageClass.Ranged;
            Projectile.penetrate = 1;
            Projectile.timeLeft = 600;
        }}
    }}
}}
"""

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
        
    return {
        "name": name,
        "kind": kind,
        "path": file_path,
        "status": "created",
        "preview": content[:200] + "..."
    }

def tool_teramod(command: str = "help", target: Optional[str] = None, extra: Optional[str] = None) -> Dict[str, Any]:
    """Unified master command router for TerraMod."""
    cmd = (command or "help").strip().lower()
    
    if cmd in ["help", "info", "list"]:
        return {
            "title": "TerraMod 1.4+ Modding Hub",
            "available_commands": [
                {"command": "/teramod", "description": "Show interactive guidance menu and quick reference"},
                {"command": "/teramod decompile <tmod_file>", "description": "Unpack and decompile .tmod archive into editable C# project with .csproj"},
                {"command": "/teramod audit <root_folder>", "description": "Scan mod project, report entities, and detect deprecated 1.3 code patterns"},
                {"command": "/teramod migrate <root_folder>", "description": "Automatically patch obsolete 1.3 syntax into canonical 1.4.4 code"},
                {"command": "/teramod create <Item|NPC|Projectile|Boss> <Name>", "description": "Scaffold new 1.4-compliant class file with modern boilerplates"},
                {"command": "/teramod docs <ClassOrHook>", "description": "Look up overridable virtual hooks, signatures, and summaries"},
                {"command": "/teramod build <root_folder>", "description": "Run dotnet build and diagnose compiler errors with knowledge graph"},
                {"command": "/teramod unpack <tmod_file>", "description": "Extract binary .tmod assets, textures, sounds, and DLL assembly"}
            ]
        }
    elif cmd == "decompile":
        if not target:
            return {"error": "Missing target .tmod file. Usage: /teramod decompile <PathTo.tmod>"}
        unpacked = tool_tmod_unpack(target)
        decompiled = tool_tmod_decompile(unpacked["extracted_dir"])
        return {"unpacked": unpacked, "decompiled": decompiled}
    elif cmd in ["audit", "scan"]:
        return tool_tmod_scan(target or os.getcwd())
    elif cmd == "migrate":
        return tool_tmod_migrate(target or os.getcwd())
    elif cmd == "create":
        kind = extra or "Item"
        name = target or "NewItem"
        return tool_tmod_create(kind, name)
    elif cmd in ["docs", "hooks"]:
        return tool_get_class_hooks(target or "ModItem")
    elif cmd == "build":
        return tool_tmod_build(target or os.getcwd())
    elif cmd == "unpack":
        return tool_tmod_unpack(target or "")
    else:
        return {"error": f"Unknown command '{cmd}'. Run /teramod for guidance."}

# --- Metadata Specifications ---

TOOLS_METADATA = [
    {
        "name": "teramod",
        "description": "Master TerraMod 1.4 router: execute help, decompile, audit, migrate, create, docs, or build",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Subcommand (help, decompile, audit, migrate, create, docs, build, unpack)", "default": "help"},
                "target": {"type": "string", "description": "File path, directory path, or symbol name"},
                "extra": {"type": "string", "description": "Optional auxiliary parameter (e.g. Item, NPC, Projectile for create)"}
            }
        }
    },
    {
        "name": "tmod_build",
        "description": "Runs dotnet build on a mod project, diagnosing compiler errors with 1.4 knowledge graph mappings",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_dir": {"type": "string", "description": "Root folder of the mod project containing .csproj"}
            },
            "required": ["project_dir"]
        }
    },
    {
        "name": "tmod_migrate",
        "description": "Batch refactors obsolete 1.3 patterns to canonical 1.4 syntax (DamageClass, ModContent, etc.)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_or_dir": {"type": "string", "description": "Path to .cs file or mod directory to refactor"},
                "dry_run": {"type": "boolean", "description": "If true, only report planned changes without modifying disk", "default": False}
            },
            "required": ["file_or_dir"]
        }
    },
    {
        "name": "tmod_create",
        "description": "Scaffolds a compliant 1.4 ModItem, ModNPC, ModProjectile, or Boss file",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "description": "Item, NPC, Projectile, or Boss"},
                "name": {"type": "string", "description": "Class name for the new entity"},
                "output_dir": {"type": "string", "description": "Directory where file should be created"}
            },
            "required": ["kind", "name"]
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
        "description": "Scans decompiled mod source directory, summarizing entities and 1.3 deprecated idioms",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source_dir": {"type": "string", "description": "Directory of decompiled mod C# project"}
            },
            "required": ["source_dir"]
        }
    },
    {
        "name": "get_class_hooks",
        "description": "List all overridable 1.4 virtual/abstract hooks, signatures, and docs for a ModLoader class",
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
        "description": "Check code or symbol against 260+ obsolete 1.3 patterns and receive exact 1.4 replacements",
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
        "description": "Search ground-truth ExampleMod 1.4 C# implementations (Sword, Gun, Minion, Boss, Tile)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Topic keyword (e.g. Sword, Armor, Accessory, Minion)"}
            },
            "required": ["topic"]
        }
    }
]

PROMPTS_METADATA = [
    {
        "name": "teramod",
        "description": "TerraMod 1.4+ Modding Assistant: guidance, decompilation, audit, migration, creation, and building",
        "arguments": [
            {
                "name": "command",
                "description": "Subcommand: help, decompile, audit, migrate, create, docs, build, unpack",
                "required": False
            },
            {
                "name": "target",
                "description": "Path to file/folder or class/hook name",
                "required": False
            },
            {
                "name": "extra",
                "description": "Extra argument (e.g. Item, NPC, Projectile, Boss)",
                "required": False
            }
        ]
    }
]

DISPATCHER = {
    "teramod": lambda args: tool_teramod(args.get("command", "help"), args.get("target"), args.get("extra")),
    "tmod_build": lambda args: tool_tmod_build(args.get("project_dir", "")),
    "tmod_migrate": lambda args: tool_tmod_migrate(args.get("file_or_dir", ""), args.get("dry_run", False)),
    "tmod_create": lambda args: tool_tmod_create(args.get("kind", "Item"), args.get("name", "NewItem"), args.get("output_dir")),
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

def handle_prompt_get(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    cmd = (args.get("command") or "help").strip().lower()
    target = args.get("target", "")
    extra = args.get("extra", "")
    
    if cmd in ["help", "info", ""]:
        prompt_text = """# TerraMod 1.4+ Command & Guidance Hub

Welcome to **TerraMod**! Below are the available commands and workflows for tModLoader 1.4.4+ mod development:

| Command | Description | Example |
| :--- | :--- | :--- |
| `/teramod` | Show this interactive guidance menu | `/teramod` |
| `/teramod decompile <tmod>` | Unpack & decompile .tmod archive into editable C# project | `/teramod decompile /path/to/Mod.tmod` |
| `/teramod audit <dir>` | Scan mod files, report entities, and detect obsolete 1.3 code | `/teramod audit ./my_mod_src` |
| `/teramod migrate <dir>` | Automatically refactor obsolete 1.3 syntax into modern 1.4 | `/teramod migrate ./my_mod_src` |
| `/teramod create <type> <name>` | Scaffold 1.4 ModItem, ModNPC, Projectile, or Boss | `/teramod create Item FrostBlade` |
| `/teramod docs <hook>` | Look up exact 1.4 signatures, parameter types, and summaries | `/teramod docs ModItem.OnHitNPC` |
| `/teramod build <dir>` | Run dotnet build with knowledge-graph compiler diagnostics | `/teramod build ./my_mod_src` |

To begin, type any of the commands above!"""
    else:
        prompt_text = f"User requested TerraMod subcommand: '{cmd}'. Target: '{target}', Extra: '{extra}'.\nPlease execute the corresponding TerraMod tool (e.g. `teramod(command='{cmd}', target='{target}', extra='{extra}')`) and report results."
        
    return {
        "description": f"TerraMod assistant prompt for {cmd}",
        "messages": [
            {
                "role": "user",
                "content": {"type": "text", "text": prompt_text}
            }
        ]
    }

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
                    "capabilities": {
                        "tools": {},
                        "prompts": {}
                    },
                    "serverInfo": {"name": "teramod", "version": "1.1.0"}
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
        elif method == "prompts/list":
            send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"prompts": PROMPTS_METADATA}
            })
        elif method == "prompts/get":
            prompt_name = params.get("name")
            prompt_args = params.get("arguments", {})
            if prompt_name == "teramod":
                resp = handle_prompt_get(prompt_name, prompt_args)
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": resp
                })
            else:
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Prompt not found: {prompt_name}"}
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
