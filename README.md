# bios-tuning

Read a UEFI BIOS image's hidden setup parameters (IFR) into an Obsidian vault that a
person can browse and a reasoning agent can traverse over MCP.

![The MS-7E59 BIOS rendered as an Obsidian vault](docs/media/graph-overview.png)

A modern AMI/Aptio BIOS shows a few hundred options in its menu and hides several
thousand more in its IFR (Internal Form Representation): AMD CBS/PBS knobs, DRAM
timings, ODT/RTT termination, drive strengths, fabric clocks, voltages, fan tables.
The hidden options still bind to NVRAM and the silicon still reads them.

This tool reads the IFR from a BIOS image and writes one markdown note per
parameter, menu, and NVRAM variable — each with its decoded options, byte offset,
domain tags, and links to its menu, variable, and sibling profiles. The result is
browsable in Obsidian and traversable by an agent through the
[Semantic Vault MCP](https://community.obsidian.md/plugins/semantic-vault-mcp)
plugin. Extraction itself is done by LongSoft
[UEFITool](https://github.com/LongSoft/UEFITool) and
[IFRExtractor-RS](https://github.com/LongSoft/IFRExtractor-RS); this organizes their
output into a graph. It does not edit or flash firmware.

## Requirements

- `python3`
- `rust` + `cargo`, and `cmake` + a C/C++ compiler (to build the extractors, done by
  `make tools`)
- [Obsidian](https://obsidian.md) and the Semantic Vault MCP plugin

## Quick start

```bash
cp ~/Downloads/7E59v2A91.zip rom/   # drop a BIOS image or vendor .zip
make                                # extract -> parse -> vault
# open vault/ in Obsidian
```

A full AM5 board yields ~5,000 notes across ~20 firmware modules.

## Pipeline

```
rom/<image>  →  ifr/*.ifr.txt  →  build/catalog.json  →  vault/
   extract          parse              vault
```

| Stage | Command | Tool |
|-------|---------|------|
| extract | `make extract` | `tools/extract_ifr.py` (UEFIExtract + IFRExtractor, auto-discovers IFR modules) |
| parse | `make parse` | `tools/parse_ifr.py` (IFR text → `catalog.json`) |
| vault | `make vault` | `tools/build_vault.py` (`catalog.json` → Obsidian vault) |

`make` runs all three. `make help` lists targets.

## Documentation

- [What this is](docs/concept.md) — the model and the pipeline.
- [Getting started](docs/getting-started.md) — build a vault and connect an agent.
- [Agent traversal](docs/agent-traversal.md) — the MCP surface and how to work the graph.
- [Walkthroughs](docs/walkthroughs.md) — worked traversals: tune, fix, reconcile.
  - [Enrichment](docs/walkthroughs/04-enrichment.md) — write research back into a note via MCP ([real note](docs/examples/HwmSetupData.md)).
  - [Driver extension](docs/walkthroughs/05-driver-extension.md) — use the BIOS model to extend an out-of-tree driver.

A `bios-vault` Claude Code skill (`.claude/skills/bios-vault/`) runs the whole flow
interactively: identify the board, get the BIOS, build, and start exploring.

## Repository layout

| Path | Purpose | Tracked? |
|------|---------|----------|
| `tools/` | the three pipeline scripts | yes |
| `Makefile`, `docs/`, `CLAUDE.md` | orchestration and docs | yes |
| `rom/` | drop a BIOS image here (gitignored; not redistributable) | README only |
| `ifr/`, `build/` | generated intermediates | generated |
| `vault/` | the generated Obsidian vault | generated |
| `tools-uefitool/`, `tools-ifrextractor/` | cloned extractors | external |

The generator is the source of truth, not the vault — re-run `make vault` to
regenerate. Hand annotations under a note's `## Notes` heading are preserved across
regeneration. Because `vault/` is gitignored, those annotations are not version
controlled by default; back them up or track the vault deliberately if they matter.

## License

MIT — see [LICENSE](LICENSE).
