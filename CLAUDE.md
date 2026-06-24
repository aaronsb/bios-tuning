# CLAUDE.md — working in this repo

`bios-tuning` reads a UEFI BIOS image's hidden IFR (setup forms) into a typed
Obsidian vault, so a reasoning agent can navigate a BIOS over MCP. Extraction is
delegated to LongSoft UEFITool and IFRExtractor; this repo organizes their output
into a graph and exposes it. It does not edit or flash firmware. Read
`docs/concept.md` for the model.

## The pipeline (and the source of truth)

```
rom/<image> ──extract──> ifr/*.ifr.txt ──parse──> build/catalog.json ──vault──> vault/
```

- `tools/extract_ifr.py` — UEFIExtract (`unpack` mode) + IFRExtractor; auto-discovers
  IFR modules by scanning for form packages (no hardcoded GUIDs).
- `tools/parse_ifr.py` — IFR text → normalized `catalog.json`; assigns heuristic
  domain tags (`DOMAIN_RULES`).
- `tools/build_vault.py` — `catalog.json` → vault: typed frontmatter, `[[wikilinks]]`,
  per-domain `.obsidian/graph.json` colours, preserved `## Notes` annotation blocks.

**The generator is the source of truth, never the vault.** To change the output,
edit `tools/*.py` and re-run `make`. Do not hand-edit generated notes except inside
their `## Notes` section (everything above `<!-- END GENERATED -->` is overwritten
on regen; the Notes section is preserved).

`build/catalog.json` is the stable structured layer — prefer it for any new analysis
(e.g. cross-version diffs) over re-parsing IFR text.

## Conventions

- **Never commit** `rom/` (vendor BIOS blobs, not redistributable), `vault/`,
  `build/`, `ifr/*.ifr.txt`, `*.dump/`, or the cloned `tools-*/` extractors — see
  `.gitignore`. Tracked surface is `tools/`, `Makefile`, `docs/`, `README.md`,
  `LICENSE`, and the per-dir READMEs.
- **Regenerate, don't patch the vault.** `make vault` is cheap; a 5k-file hand-edit
  is not.
- **Don't flash anything.** This project documents and *locates* settings. A
  `setup_var`/NVRAM write is the operator's deliberate decision — surface the offset
  and option byte, explain the risk, let them apply it.

## Navigating a built vault

A full vault is ~5,000 notes — far too large to read file-by-file. Use the
**Semantic Vault MCP** plugin's traversal instead (see `docs/agent-traversal.md`):
search to a node, `graph.neighbors`/`traverse` to follow structure, `vault.read` the
node you need. Load only the path you're reasoning about.

Caveats: let first-time indexing finish before querying; keep Obsidian's *global*
graph view closed while traversing (it starves the in-Obsidian MCP server).

## Extending

- New domain classification → add a rule to `DOMAIN_RULES` in `tools/parse_ifr.py`
  (and a colour in `DOMAIN_COLORS` in `tools/build_vault.py`).
- Filename/edge scheme lives in `tools/build_vault.py` (`take()` allocates unique,
  human-readable underscore filenames; the kebab `id` stays in frontmatter).
- Test changes against a real image in `rom/` with `make`, then spot-check a node
  via the MCP `vault.read`.

## Kickoff

The `bios-vault` skill (`.claude/skills/bios-vault/`) runs the operator interview +
pipeline end-to-end. Invoke it when someone wants to analyse a board's firmware.
