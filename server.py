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

def tool_tmod_create(kind: str = "Plan", name: str = "MyMod", output_dir: Optional[str] = None) -> Dict[str, Any]:
    """Scaffolds compliant 1.4 ModItem, ModNPC, ModProjectile, Boss, UIState/UISystem, entire mod project, or runs interactive Plan interview."""
    if output_dir is None:
        output_dir = os.getcwd()
    os.makedirs(output_dir, exist_ok=True)
    
    kind_lower = (kind or "plan").lower()
    
    # 1. Interactive Planning / Interview Mode
    if kind_lower in ['plan', 'interview', 'interactive'] or not name or name.lower() in ['help', 'plan']:
        mod_name = name if (name and name.lower() not in ['help', 'plan']) else "CustomMod"
        return {
            "status": "interactive_plan_required",
            "step": "interview",
            "message": f"Interactive Mod Planning Session for '{mod_name}'. Select a content category or explore ideas:",
            "interview_questions": [
                {
                    "id": "content_type",
                    "question": "What type of content are you creating?",
                    "options": [
                        {
                            "name": "Custom Gameplay Mechanic",
                            "command": "Mechanic",
                            "summary": "ModPlayer & ModSystem driven mechanics, custom resources, and hooks.",
                            "idea": "Heat/stamina resource meter, dash or dodge roll, right-click parry, combo streak counter, or custom damage scaling."
                        },
                        {
                            "name": "In-Game HUD & Interface",
                            "command": "UI",
                            "summary": "1.4 UIState and UserInterface layer injections into the game canvas.",
                            "idea": "Resource gauge/bar overlay in 'Vanilla: Mouse Text' layer, draggable info panel, inventory slot grid, or cooldown tracker with mouse-lock guards."
                        },
                        {
                            "name": "Weapon or Equipment",
                            "command": "Sword",
                            "summary": "1.4 ModItem with swing animation, projectile shooting, and hit effects.",
                            "idea": "Transforming greatsword, homing celestial staff, alt-fire firearm, or summoner whip with minion tag damage."
                        },
                        {
                            "name": "Armor Set & Set Bonus",
                            "command": "Armor",
                            "summary": "Coordinated Head, Body, Legs armor set with custom SetBonus ability.",
                            "idea": "Endgame celestial set with minion slot boosts, damage resistance, active ability keybinds, and visual dust trails."
                        },
                        {
                            "name": "Boss Encounter or Custom Enemy",
                            "command": "NPC",
                            "summary": "AI-driven enemy with state machine, attack phases, and custom drops.",
                            "idea": "Multi-phase boss with telegraph attacks, projectile spirals, custom treasure bag, and music track."
                        },
                        {
                            "name": "Full Mod Project",
                            "command": "Project",
                            "summary": "Complete 1.4 project structure ready for tModLoader compilation.",
                            "idea": "Comprehensive scaffolding with .csproj, build.txt, description, en-US.hjson localization, and starter items."
                        }
                    ]
                },
                {
                    "id": "progression_tier",
                    "question": "What game stage should it be balanced around?",
                    "options": [
                        {
                            "name": "Early Pre-Hardmode",
                            "summary": "Wood, copper/iron ore, surface/underground tier",
                            "idea": "Balanced around Eye of Cthulhu & King Slime. Low mana costs, basic weapon swings, simple movement speed boosts."
                        },
                        {
                            "name": "Late Pre-Hardmode",
                            "summary": "Dungeon, Shadow Orb/Crimson Heart, Hellstone tier",
                            "idea": "Wall of Flesh ready. Penetrating attacks, double jumps, complex buff immunities, and underworld crafting recipes."
                        },
                        {
                            "name": "Early Hardmode",
                            "summary": "Cobalt/Mythril, Souls of Night/Light tier",
                            "idea": "Mechanical Bosses tier. Secondary projectile sprays, armor set bonuses with dashing or stealth, and flight accessories."
                        },
                        {
                            "name": "Endgame / Celestial",
                            "summary": "Pillar Fragments, Luminite, Moon Lord tier",
                            "idea": "Overpowered stats, screen-clearing AoE, 100+ minion slots, infinite flight, or celestial dust trail visuals."
                        }
                    ]
                }
            ],
            "blueprint_template": {
                "mod_name": mod_name,
                "version": "0.1.0",
                "author": "Kyr-69",
                "files_to_scaffold": [
                    "build.txt",
                    f"{mod_name}.csproj",
                    "description.txt",
                    "Localization/en-US.hjson",
                    f"Common/UI/{mod_name}UIState.cs",
                    f"Common/UI/{mod_name}UISystem.cs",
                    f"Content/Items/{mod_name}Blade.cs"
                ]
            },
            "next_step": "Run teramod create <Type> <Name> (e.g. teramod create Mechanic HeatSystem or teramod create UI ManaHUD) to scaffold immediately."
        }
        
    # 2. Gameplay Mechanic Scaffolding (ModPlayer + ModSystem)
    if kind_lower in ['mechanic', 'player', 'system']:
        player_file = os.path.join(output_dir, f"{name}Player.cs")
        system_file = os.path.join(output_dir, f"{name}System.cs")
        
        player_content = f"""using Microsoft.Xna.Framework;
using System;
using Terraria;
using Terraria.DataStructures;
using Terraria.ID;
using Terraria.ModLoader;

namespace MyMod.Common.Players
{{
    public class {name}Player : ModPlayer
    {{
        // 1.4 Custom Mechanic State
        public int {name}ResourceCurrent = 0;
        public int {name}ResourceMax = 100;
        public int {name}CooldownTimer = 0;
        public bool {name}EffectActive = false;

        public override void ResetEffects()
        {{
            {name}EffectActive = false;
        }}

        public override void PostUpdateMiscEffects()
        {{
            // Cooldown handling and passive resource decay / regeneration
            if ({name}CooldownTimer > 0)
            {{
                {name}CooldownTimer--;
            }}
        }}

        public override void OnHitNPC(NPC target, NPC.HitInfo hit, int damageDone)
        {{
            if ({name}EffectActive)
            {{
                {name}ResourceCurrent = Math.Min({name}ResourceMax, {name}ResourceCurrent + 5);
            }}
        }}

        public override void ModifyHitByNPC(NPC npc, ref Player.HurtModifiers modifiers)
        {{
            // Custom damage mitigation or trigger effects when player is hit
        }}
    }}
}}
"""
        system_content = f"""using Terraria.ModLoader;

namespace MyMod.Common.Systems
{{
    public class {name}System : ModSystem
    {{
        public override void PostUpdateWorld()
        {{
            // World-level timers or environmental mechanic updates
        }}
    }}
}}
"""
        with open(player_file, 'w', encoding='utf-8') as f:
            f.write(player_content.strip() + '\n')
        with open(system_file, 'w', encoding='utf-8') as f:
            f.write(system_content.strip() + '\n')

        return {
            "name": name,
            "kind": "Mechanic",
            "status": "created",
            "files_created": [player_file, system_file],
            "components": {
                "player": f"{name}Player.cs (ModPlayer with resource state, ResetEffects & OnHitNPC)",
                "system": f"{name}System.cs (ModSystem with PostUpdateWorld)"
            },
            "preview": f"Scaffolded 1.4 Gameplay Mechanic ModPlayer and ModSystem into {output_dir}"
        }

    # 3. Armor Set Scaffolding (Head, Body, Legs)
    if kind_lower in ['armor', 'set', 'armorset']:
        helmet_file = os.path.join(output_dir, f"{name}Helmet.cs")
        chest_file = os.path.join(output_dir, f"{name}Breastplate.cs")
        legs_file = os.path.join(output_dir, f"{name}Leggings.cs")
        
        h_code = f"""using Terraria;
using Terraria.ID;
using Terraria.Localization;
using Terraria.ModLoader;

namespace MyMod.Content.Items.Armor
{{
    [AutoloadEquip(EquipType.Head)]
    public class {name}Helmet : ModItem
    {{
        public static LocalizedText SetBonusText {{ get; private set; }}

        public override void SetStaticDefaults()
        {{
            SetBonusText = this.GetLocalization(\"SetBonus\");
        }}

        public override void SetDefaults()
        {{
            Item.width = 24;
            Item.height = 20;
            Item.value = Item.buyPrice(gold: 5);
            Item.rare = ItemRarityID.Pink;
            Item.defense = 12;
        }}

        public override void UpdateEquip(Player player)
        {{
            player.GetDamage(DamageClass.Generic) += 0.10f;
        }}

        public override bool IsArmorSet(Item head, Item body, Item legs)
        {{
            return body.type == ModContent.ItemType<{name}Breastplate>() && legs.type == ModContent.ItemType<{name}Leggings>();
        }}

        public override void UpdateArmorSet(Player player)
        {{
            player.setBonus = SetBonusText.Value;
            player.GetDamage(DamageClass.Generic) += 0.15f;
        }}

        public override void AddRecipes()
        {{
            CreateRecipe()
                .AddIngredient(ItemID.HallowedBar, 12)
                .AddTile(TileID.MythrilAnvil)
                .Register();
        }}
    }}
}}
"""
        c_code = f"""using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace MyMod.Content.Items.Armor
{{
    [AutoloadEquip(EquipType.Body)]
    public class {name}Breastplate : ModItem
    {{
        public override void SetDefaults()
        {{
            Item.width = 30;
            Item.height = 20;
            Item.value = Item.buyPrice(gold: 5);
            Item.rare = ItemRarityID.Pink;
            Item.defense = 18;
        }}

        public override void UpdateEquip(Player player)
        {{
            player.GetDamage(DamageClass.Generic) += 0.10f;
        }}

        public override void AddRecipes()
        {{
            CreateRecipe()
                .AddIngredient(ItemID.HallowedBar, 24)
                .AddTile(TileID.MythrilAnvil)
                .Register();
        }}
    }}
}}
"""
        l_code = f"""using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace MyMod.Content.Items.Armor
{{
    [AutoloadEquip(EquipType.Legs)]
    public class {name}Leggings : ModItem
    {{
        public override void SetDefaults()
        {{
            Item.width = 22;
            Item.height = 18;
            Item.value = Item.buyPrice(gold: 5);
            Item.rare = ItemRarityID.Pink;
            Item.defense = 14;
        }}

        public override void UpdateEquip(Player player)
        {{
            player.moveSpeed += 0.15f;
        }}

        public override void AddRecipes()
        {{
            CreateRecipe()
                .AddIngredient(ItemID.HallowedBar, 18)
                .AddTile(TileID.MythrilAnvil)
                .Register();
        }}
    }}
}}
"""
        with open(helmet_file, 'w', encoding='utf-8') as f:
            f.write(h_code.strip() + '\n')
        with open(chest_file, 'w', encoding='utf-8') as f:
            f.write(c_code.strip() + '\n')
        with open(legs_file, 'w', encoding='utf-8') as f:
            f.write(l_code.strip() + '\n')

        return {
            "name": name,
            "kind": "Armor",
            "status": "created",
            "files_created": [helmet_file, chest_file, legs_file],
            "components": {
                "head": f"{name}Helmet.cs",
                "body": f"{name}Breastplate.cs",
                "legs": f"{name}Leggings.cs"
            },
            "preview": f"Scaffolded 1.4 Armor Set into {output_dir}"
        }

    # 4. In-Game UI Scaffolding (UIState + ModSystem Layer Injection)
    if kind_lower in ['ui', 'uistate', 'hud', 'panel']:
        ui_state_file = os.path.join(output_dir, f"{name}UIState.cs")
        ui_system_file = os.path.join(output_dir, f"{name}UISystem.cs")
        
        state_content = f"""using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.GameContent.UI.Elements;
using Terraria.UI;

namespace MyMod.Common.UI
{{
    public class {name}UIState : UIState
    {{
        public UIPanel Panel;
        public UIText StatusText;

        public override void OnInitialize()
        {{
            // Container panel
            Panel = new UIPanel();
            Panel.Left.Set(24f, 0f);
            Panel.Top.Set(120f, 0f);
            Panel.Width.Set(240f, 0f);
            Panel.Height.Set(70f, 0f);
            Panel.BackgroundColor = new Color(28, 38, 68, 210);

            // Text display inside panel
            StatusText = new UIText(\"{name}: Active\", 0.9f);
            StatusText.HAlign = 0.5f;
            StatusText.VAlign = 0.5f;
            Panel.Append(StatusText);

            Append(Panel);
        }}

        public override void Update(GameTime gameTime)
        {{
            base.Update(gameTime);

            // Prevent weapon use while mouse interacts with this panel
            if (Panel.ContainsPoint(Main.MouseScreen))
            {{
                Main.LocalPlayer.mouseInterface = true;
            }}
        }}

        protected override void DrawSelf(SpriteBatch spriteBatch)
        {{
            base.DrawSelf(spriteBatch);
        }}
    }}
}}
"""
        system_content = f"""using Microsoft.Xna.Framework;
using System.Collections.Generic;
using Terraria;
using Terraria.ModLoader;
using Terraria.UI;

namespace MyMod.Common.UI
{{
    [Autoload(Side = ModSide.Client)]
    public class {name}UISystem : ModSystem
    {{
        private UserInterface customUserInterface;
        internal {name}UIState customUIState;

        public void ShowUI()
        {{
            customUserInterface?.SetState(customUIState);
        }}

        public void HideUI()
        {{
            customUserInterface?.SetState(null);
        }}

        public void ToggleUI()
        {{
            if (customUserInterface?.CurrentState != null)
                HideUI();
            else
                ShowUI();
        }}

        public override void Load()
        {{
            customUserInterface = new UserInterface();
            customUIState = new {name}UIState();
            customUIState.Activate();
            customUserInterface.SetState(customUIState);
        }}

        public override void Unload()
        {{
            customUIState = null;
            customUserInterface = null;
        }}

        public override void UpdateUI(GameTime gameTime)
        {{
            if (customUserInterface?.CurrentState != null)
            {{
                customUserInterface.Update(gameTime);
            }}
        }}

        public override void ModifyInterfaceLayers(List<GameInterfaceLayer> layers)
        {{
            int mouseTextIndex = layers.FindIndex(layer => layer.Name.Equals(\"Vanilla: Mouse Text\"));
            if (mouseTextIndex != -1)
            {{
                layers.Insert(mouseTextIndex, new LegacyGameInterfaceLayer(
                    \"MyMod: {name} UI Layer\",
                    delegate
                    {{
                        if (customUserInterface?.CurrentState != null)
                        {{
                            customUserInterface.Draw(Main.spriteBatch, new GameTime());
                        }}
                        return true;
                    }},
                    InterfaceScaleType.UI
                ));
            }}
        }}
    }}
}}
"""
        with open(ui_state_file, 'w', encoding='utf-8') as f:
            f.write(state_content.strip() + '\n')
        with open(ui_system_file, 'w', encoding='utf-8') as f:
            f.write(system_content.strip() + '\n')

        return {
            "name": name,
            "kind": "UI",
            "status": "created",
            "files_created": [ui_state_file, ui_system_file],
            "components": {
                "ui_state": f"{name}UIState.cs (UIState container with mouseInterface handling)",
                "ui_system": f"{name}UISystem.cs (ModSystem with client autoload, UpdateUI & ModifyInterfaceLayers)"
            },
            "preview": f"Scaffolded 1.4 UIState and UISystem into {output_dir}"
        }

    # 3. Full Mod Project Scaffolding
    if kind_lower in ['project', 'mod', 'scaffold']:
        proj_dir = os.path.join(output_dir, name)
        items_dir = os.path.join(proj_dir, "Content", "Items")
        ui_dir = os.path.join(proj_dir, "Common", "UI")
        loc_dir = os.path.join(proj_dir, "Localization")
        
        os.makedirs(items_dir, exist_ok=True)
        os.makedirs(ui_dir, exist_ok=True)
        os.makedirs(loc_dir, exist_ok=True)
        
        with open(os.path.join(proj_dir, "build.txt"), "w", encoding='utf-8') as f:
            f.write(f"displayName = {name}\nauthor = Kyr-69\nversion = 0.1.0\nhomepage = https://github.com/Kyr-69/TerraMod\n")
            
        with open(os.path.join(proj_dir, "description.txt"), "w", encoding='utf-8') as f:
            f.write(f"A modern tModLoader 1.4 mod built with TerraMod.\n")
            
        with open(os.path.join(proj_dir, f"{name}.csproj"), "w", encoding='utf-8') as f:
            f.write(f"""<Project Sdk="Microsoft.NET.Sdk">
  <Import Project="..\\tModLoader.targets" />
  <PropertyGroup>
    <AssemblyName>{name}</AssemblyName>
    <TargetFramework>net6.0</TargetFramework>
    <PlatformTarget>AnyCPU</PlatformTarget>
    <LangVersion>latest</LangVersion>
  </PropertyGroup>
</Project>
""")
            
        with open(os.path.join(loc_dir, "en-US.hjson"), "w", encoding='utf-8') as f:
            f.write(f"""Mods: {{
  {name}: {{
    Items: {{
      {name}Blade: {{
        DisplayName: \"{name} Blade\"
        Tooltip: \"Crafted with the power of TerraMod.\"
      }}
    }}
  }}
}}
""")
            
        tool_tmod_create("Item", f"{name}Blade", items_dir)
        tool_tmod_create("UI", f"{name}HUD", ui_dir)
        
        return {
            "name": name,
            "kind": "Project",
            "status": "created",
            "project_dir": proj_dir,
            "files_created": [
                os.path.join(proj_dir, "build.txt"),
                os.path.join(proj_dir, "description.txt"),
                os.path.join(proj_dir, f"{name}.csproj"),
                os.path.join(loc_dir, "en-US.hjson"),
                os.path.join(items_dir, f"{name}Blade.cs"),
                os.path.join(ui_dir, f"{name}HUDUIState.cs"),
                os.path.join(ui_dir, f"{name}HUDUISystem.cs")
            ],
            "preview": f"Successfully created complete 1.4 mod project '{name}'."
        }

    # 4. Standard Entities (Item, NPC, Projectile)
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
                {"command": "/teramod create [Item|UI|Project] [Name]", "description": "Interactive mod planner or scaffolding for 1.4 Items, in-game UIState/UISystem, or entire projects"},
                {"command": "/teramod docs <ClassOrHook>", "description": "Look up overridable 1.4 virtual hooks (ModItem, ModNPC, UIState, UserInterface, ModSystem)"},
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
        if not target or target.lower() in ["plan", "help", "interview", "interactive"]:
            return tool_tmod_create(kind="plan", name=extra or "MyMod")
        known_kinds = ['item', 'sword', 'weapon', 'armor', 'set', 'armorset', 'mechanic', 'player', 'system', 'npc', 'enemy', 'boss', 'projectile', 'ui', 'uistate', 'hud', 'panel', 'project', 'mod', 'scaffold']
        if target.lower() in known_kinds and extra:
            kind = target
            name = extra
        else:
            kind = extra or "Item"
            name = target
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
        "description": "Scaffolds compliant 1.4 ModItem, ModNPC, ModProjectile, Boss, UI (UIState + UISystem), Project structure, or runs interactive Plan interview",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "description": "Plan (interactive interview), UI (UIState + UISystem), Project (full mod), Item, NPC, Projectile, or Boss", "default": "Plan"},
                "name": {"type": "string", "description": "Class or project name for the new entity", "default": "MyMod"},
                "output_dir": {"type": "string", "description": "Directory where file should be created"}
            }
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
    elif cmd == "create":
        prompt_text = f"""# TerraMod 1.4 Interactive Creation Mode
Target: '{target or "NewMod"}', Type: '{extra or "Plan"}'

Follow the 3-step interactive creation protocol:
1. **Interactive Alignment**: Guide the user through theme, combat class, entity scope, in-game UI requirements (UIState / UserInterface layer injection), and balance stage.
2. **Spec Blueprint**: Summarize the design into a clear plan (MOD_SPEC.md).
3. **Execution**: Scaffold the complete mod code and UI classes using `teramod(command='create', target='{target or "NewMod"}', extra='{extra or "UI"}')`."""
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
