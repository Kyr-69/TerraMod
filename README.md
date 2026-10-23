# TerraMod (tModLoader 1.4+ Knowledge Graph, Decompiler & MCP Server)

> An authoritative, open-source, decompilation-grounded Knowledge Graph, universal agent specification, and MCP Server for Terraria 1.4.4+ (`tModLoader`) mod development, inspection, and reverse engineering.

> **Status**: Open Source & Active Work in Progress (WIP). Contributions and feedback are welcome!

## Overview

Most AI models (ChatGPT, Claude, Gemini) struggle to write modern tModLoader code because they hallucinate deprecated 1.3-era patterns (e.g. `item.melee = true`, `ModRecipe`, legacy `OnHitNPC` parameter lists).

**TerraMod** solves this by providing:
1. **`tmod_extractor.py`**: Standalone, zero-dependency unpacker for Terraria `.tmod` binary packages (handles 7-bit encoded headers, metadata, and Deflate compressed assets/DLLs).
2. **`server.py`**: Native Model Context Protocol (MCP) Server exposing tools for LLMs to unpack `.tmod` files, decompile assemblies into editable C# projects via `ilspycmd`, scan mod architectures, and query the 1.4 knowledge graph.
3. **`AGENTS.md` / `TMOD_1_4_MODDING.md`**: Universal prompt specification encoding critical breaking changes, anti-hallucination rules, modern fluent builder recipes, combat hooks with `NPC.HitInfo`, and minimal working boilerplates.
4. **`graphify_graph.json`**: Graph dataset containing 1,800+ nodes and nearly 1,000 edges detailing class hierarchies, lifecycle hooks, and 1.3-to-1.4 replacements.
5. **`tmod_1_4.db`**: Self-contained SQLite Knowledge Graph extracted directly from `tModLoader.dll`, `tModPorter`, and official `ExampleMod` sources.

---

## Repository Contents

| File / Tool | Description |
| :--- | :--- |
| `server.py` | Model Context Protocol (MCP) server providing 6 modding & decompiler tools over JSON-RPC stdio. |
| `tmod_extractor.py` | Standalone CLI & module to extract any Terraria `.tmod` package into assets and .NET assemblies. |
| `AGENTS.md` | Universal markdown specification ready to drop into LLM system prompts, Cursor rules, or MCP contexts. |
| `TMOD_1_4_MODDING.md` | Complete reference guide detailing 1.4 API patterns and hook signatures. |
| `graphify_graph.json` | JSON graph dataset (nodes and edges) for visualizers and graph querying tools. |
| `tmod_1_4.db` | SQLite database indexing 700+ lifecycle hooks and 260+ migration rules. |

---

## MCP Server Tools

The MCP server (`server.py`) exposes 6 tools designed for autonomous AI agents and developers:

- `tmod_unpack(tmod_path, output_dir)`: Unpacks binary `.tmod` archive into textures, sounds, localization, and compiled DLL.
- `tmod_decompile(assembly_or_extracted_dir, output_source_dir)`: Decompiles the mod's `.dll` into a complete C# `.csproj` project tree with `ilspycmd`.
- `tmod_scan(source_dir)`: High-level architectural audit listing all `ModItem`, `ModNPC`, `ModProjectile`, `ModBuff`, and `.hjson` localization files.
- `get_class_hooks(class_name)`: Returns overridable 1.4 virtual/abstract hooks, full signatures, parameter types, and summaries.
- `check_1_3_migration(code_or_symbol)`: Checks code against 260+ deprecated 1.3 patterns and provides the canonical 1.4 replacement.
- `get_example_snippet(topic)`: Returns ground-truth reference C# code snippets from official `ExampleMod`.

### Installing TerraMod into Hermes Agent / MCP Clients

Add TerraMod to Hermes with a single command:
```bash
hermes mcp add teramod --command python3 --args /path/to/TerraMod/server.py
```

Or add to Claude Desktop / Cursor `mcpServers` config:
```json
{
  "mcpServers": {
    "teramod": {
      "command": "python3",
      "args": ["/absolute/path/to/TerraMod/server.py"]
    }
  }
}
```

---

## Standalone Decompiler Usage

Extract any `.tmod` mod file directly from the terminal:
```bash
python3 tmod_extractor.py /path/to/ModName.tmod ./extracted_mod/
```

Decompile extracted mod assemblies into editable C# source files:
```bash
ilspycmd --disable-updatecheck --nested-directories -p -o ./mod_src/ ./extracted_mod/ModName.dll
```

---

## License
MIT
