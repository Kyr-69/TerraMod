# TerraMod (tModLoader 1.4+ Knowledge Graph, Decompiler & MCP Server)

> An authoritative, open-source, decompilation-grounded Knowledge Graph, universal agent specification, and Model Context Protocol (MCP) Server for Terraria 1.4.4+ (`tModLoader`) mod development, reverse engineering, inspection, and migration.

> **Status**: Open Source & Active Work in Progress (WIP). Contributions and feedback are welcome!

---

## Installation

### Via npm / npx (Node.js)

Run instantly with **zero installation** via `npx`:
```bash
npx github:Kyr-69/TerraMod
```

Or install globally with npm:
```bash
npm install -g github:Kyr-69/TerraMod
```

### Via pip / uvx (Python)

```bash
pip install git+https://github.com/Kyr-69/TerraMod.git
# or run once with uvx:
uvx --from git+https://github.com/Kyr-69/TerraMod.git teramod
```

---

## Quick Start: `/teramod` Interactive Guidance Hub

TerraMod includes an interactive MCP prompt and terminal CLI (`teramod`).

### Available Commands

| Command | Description | Example |
| :--- | :--- | :--- |
| `/teramod` | Interactive guidance menu and documentation | `/teramod` |
| `/teramod decompile <PathTo.tmod>` | Unpack & decompile .tmod into an editable C# project with `.csproj` | `/teramod decompile ~/.local/share/.../Mod.tmod` |
| `/teramod audit <RootFolder>` | Scan mod files, report entities, and detect deprecated 1.3 patterns | `/teramod audit ./my_mod_src` |
| `/teramod migrate <RootFolder>` | Automatically refactor obsolete 1.3 code into canonical 1.4.4 | `/teramod migrate ./my_mod_src` |
| `/teramod create [Type] [Name]` | Interactive planning interview, or scaffold 1.4 Items, in-game UIState/UISystem, and Projects | `/teramod create` or `teramod create UI ManaGauge` |
| `/teramod docs <ClassOrHook>` | Look up exact 1.4 signatures, parameter types, and summaries (Items, NPCs, UIState, UserInterface) | `/teramod docs UIState` |
| `/teramod build <RootFolder>` | Run `dotnet build` with knowledge-graph compiler diagnostics | `/teramod build ./my_mod_src` |
| `/teramod unpack <PathTo.tmod>` | Extract binary `.tmod` raw assets, textures, sounds, and DLL | `/teramod unpack ./Mod.tmod` |

---

## Adding TerraMod to AI Agents & IDEs

### Hermes Agent
```bash
# Using npx directly:
hermes mcp add teramod --command npx --args -y github:Kyr-69/TerraMod

# Or using local python file:
hermes mcp add teramod --command python3 --args /path/to/teramod/server.py
```

### Claude Desktop / Cursor (`mcpServers` config)
Add this snippet to your `claude_desktop_config.json` or Cursor MCP settings:
```json
{
  "mcpServers": {
    "teramod": {
      "command": "npx",
      "args": ["-y", "github:Kyr-69/TerraMod"]
    }
  }
}
```

---

## Direct Terminal CLI Usage

After installing via `npm install -g github:Kyr-69/TerraMod` or `pip install`:
```bash
# View guidance menu
teramod

# Decompile an installed mod
teramod decompile /path/to/ModName.tmod

# Audit code for 1.3 breaking changes
teramod audit /path/to/extracted_src/

# Look up hook signatures
teramod docs ModItem
```

---

## Repository Contents

| File / Tool | Description |
| :--- | :--- |
| `bin/teramod.js` | Node.js entry point auto-detecting CLI vs stdio MCP server execution. |
| `package.json` | npm package manifest supporting `npx` and global install. |
| `pyproject.toml` | Python packaging manifest supporting `pip` and `uvx`. |
| `server.py` | Model Context Protocol (MCP) server providing 10 modding & decompiler tools over JSON-RPC stdio. |
| `cli.py` | Terminal CLI wrapper (`teramod`) exposing all tools directly to shell scripts. |
| `tmod_extractor.py` | Standalone CLI & module to extract any Terraria `.tmod` package into assets and .NET assemblies. |
| `AGENTS.md` | Universal markdown specification ready to drop into LLM system prompts, Cursor rules, or MCP contexts. |
| `TMOD_1_4_MODDING.md` | Complete reference guide detailing 1.4 API patterns and hook signatures. |
| `graphify_graph.json` | JSON graph dataset (nodes and edges) for visualizers and graph querying tools. |
| `tmod_1_4.db` | SQLite database indexing 700+ lifecycle hooks and 260+ migration rules. |

---

## License
MIT
