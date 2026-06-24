# Getting started

From a BIOS image to a navigable knowledge graph in three commands, then connect a
reasoning agent.

## Prerequisites

- **`python3`** — the pipeline scripts
- **`rust` + `cargo`** and **`cmake` + a C/C++ compiler** — to build the LongSoft
  extractors (done automatically by `make tools` on first run)
- **[Obsidian](https://obsidian.md)** — to browse the vault
- **[Semantic Vault MCP](https://community.obsidian.md/plugins/semantic-vault-mcp)**
  Obsidian plugin — to expose the vault to a reasoning agent over MCP
  ([source](https://github.com/aaronsb/obsidian-mcp-plugin))

## 1. Get a BIOS image

Drop a flash image into `rom/`. Accepted: a raw image (`.bin`, `.ROM`, `.CAP`, or a
vendor-suffixed file like `E7E59AMSI.2A91`) or a vendor `.zip` — it's unzipped
automatically and the largest image is picked.

```bash
cp ~/Downloads/7E59v2A91.zip rom/
```

> BIOS images are vendor IP and aren't redistributable, so `rom/` is gitignored.
> Bring your own. Most vendors host current BIOS files on the board's support page;
> mirrors like station-drivers keep older versions if you need a specific one (e.g.
> to match your *installed* version so NVRAM offsets line up exactly).

## 2. Build the vault

```bash
make            # extract -> parse -> vault  (clones+builds extractors on first run)
```

Stages, if you want them individually:

| Stage | Command | Output |
|-------|---------|--------|
| extract | `make extract` | `ifr/*.ifr.txt` (decompiled forms) |
| parse | `make parse` | `build/catalog.json` (structured) |
| vault | `make vault` | `vault/` (Obsidian) |

On a full AM5 board expect ~5,000 notes across ~20 firmware modules.

## 3. Open it in Obsidian

Point Obsidian at the `vault/` folder. Start at `Home.md`; the colour legend lives
in `00-index/Domain colours`.

**Performance note.** The *global* graph view runs a force-directed physics sim on
every node and struggles at several thousand nodes. This is Obsidian's renderer.
For day-to-day use:

- Use the **local graph** (per-note, depth 1–2) — instant, shows a knob with its
  menu, variable, and sibling profiles.
- Or filter the global graph to a subset — `tag:#domain/odt-si` or `path:forms/` —
  which the per-domain colours make readable.
- Navigate with **search + backlinks**, not the galaxy render.

## 4. Connect a reasoning agent

Install and enable the **Semantic Vault MCP** plugin in Obsidian, pointed at this
vault. It exposes file ops, full-text + semantic search, and graph traversal over
MCP. Add the server to your agent (e.g. Claude Code's MCP config), and the agent
can read nodes, follow links, and search-traverse the BIOS directly.

First indexing of a large vault takes a while (it builds the link graph and search
index); subsequent updates are incremental. Don't query mid-index — you'll get
partial results.

See **[Agent traversal](agent-traversal.md)** for a worked example.

## 5. Iterate

The vault is generated output — the **generator is the source of truth**, not the
vault. Re-run `make vault` any time. Hand annotations you add under a note's
`## Notes` heading are preserved across regeneration (and Obsidian renders Mermaid
there, so diagrams survive too).

To analyse a different/newer BIOS, drop it in `rom/` and `make` again — handy for
diffing two versions.
