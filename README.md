# TerraMod (tModLoader 1.4+ Knowledge Graph & Agent Spec)

> An authoritative, open-source, decompilation-grounded Knowledge Graph and universal agent specification for Terraria 1.4.4+ (`tModLoader`) mod development.

> **Status**: Open Source & Active Work in Progress (WIP). Contributions and feedback are welcome!

## Overview

Most AI models (ChatGPT, Claude, Gemini) struggle to write modern tModLoader code because they hallucinate deprecated 1.3-era patterns (e.g. `item.melee = true`, `ModRecipe`, legacy `OnHitNPC` parameter lists). 

**TerraMod** solves this by providing:
1. **`AGENTS.md` / `TMOD_1_4_MODDING.md`**: A universal prompt specification encoding critical breaking changes, anti-hallucination rules, modern fluent builder recipes, combat hooks with `NPC.HitInfo`, and minimal working boilerplates.
2. **`graphify_graph.json`**: An exportable graph containing 1,800+ nodes and nearly 1,000 edges detailing class hierarchies, lifecycle hooks, and 1.3-to-1.4 replacements.
3. **`tmod_1_4.db`**: A self-contained SQLite Knowledge Graph extracted directly from `tModLoader.dll`, `tModPorter`, and official `ExampleMod` sources.

---

## Repository Contents

| File | Description |
| :--- | :--- |
| `AGENTS.md` | Universal markdown specification ready to drop into LLM system prompts, Cursor rules, or MCP servers. |
| `TMOD_1_4_MODDING.md` | Complete reference guide detailing 1.4 API patterns and hook signatures. |
| `graphify_graph.json` | JSON graph dataset (nodes and edges) for visualizers and graph querying tools. |
| `tmod_1_4.db` | SQLite database with `nodes` and `edges` tables, indexing 700+ lifecycle hooks and 260+ migration rules. |

---

## How to Use

### 1. In AI Coding Assistants (Claude Code, Cursor, Hermes, Copilot)
Copy or symlink `AGENTS.md` into your mod project root or add it to your agent's context:
```bash
cp AGENTS.md /path/to/YourMod/.cursorrules
# or copy into your system prompt
```

### 2. Querying the SQLite Knowledge Graph (`tmod_1_4.db`)
You can inspect overridable hooks for any mod class directly:
```sql
-- Find all hooks for ModItem
SELECT n.name, json_extract(n.data, '$.signature'), json_extract(n.data, '$.summary')
FROM edges e
JOIN nodes n ON e.target_id = n.id
WHERE e.source_id = 'Terraria.ModLoader.ModItem' AND e.relationship = 'EXPOSES_HOOK';

-- Look up what replaced a legacy 1.3 pattern
SELECT name, json_extract(data, '$.replaced_by'), json_extract(data, '$.note')
FROM nodes
WHERE label = 'Legacy13' AND name LIKE '%damage%';
```

### 3. Loading with Graphify / Python
```python
import json

with open('graphify_graph.json', 'r', encoding='utf-8') as f:
    graph = json.load(f)

print(f"Loaded {graph['nodes_count']} nodes and {graph['edges_count']} edges.")
```

---

## License
MIT
