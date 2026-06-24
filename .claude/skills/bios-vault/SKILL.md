---
name: bios-vault
description: Ingest a UEFI BIOS image into an explorable Obsidian knowledge vault and begin exploring a board's firmware settings. Use when someone wants to analyze a motherboard's hidden BIOS parameters, build the vault from a BIOS file, or investigate a subsystem (memory/ODT tuning, fan control, a specific AMD CBS/PBS/AOD area). Not for flashing firmware, writing NVRAM, or improving the IFR extractor itself.
---

# bios-vault

Drive the `bios-tuning` pipeline end to end: identify the board, get its BIOS image,
build the vault, and start a first traversal toward the operator's goal. The vault
locates and describes settings. It does not flash firmware or write NVRAM; that stays
with the operator.

## 0. Orient

- Confirm you are in the `bios-tuning` repo (`Makefile`, `tools/extract_ifr.py`).
- Check for an existing vault (`vault/Home.md`). If one exists, ask whether to reuse
  it or rebuild from a different image.

## 1. Interview the operator

Ask three things, briefly:

1. **Which board / BIOS?** If this is the operator's own machine, offer to read it:
   `sudo dmidecode -t 2 -t 0` gives board vendor, model (e.g. `MS-7E59`), BIOS
   version, and date; `dmidecode | grep -i agesa` often gives the AGESA version.
   Otherwise ask for the model and BIOS version.
2. **What do they want to understand?** Memory/ODT/timing tuning, fan/Super-I/O,
   PBO/overclocking, a specific subsystem, or a general survey. This sets the first
   traversal target.
3. **Do they have the BIOS file?** It is needed as input.

## 2. Acquire the BIOS image

- The image goes in `rom/` (a raw image or a vendor `.zip`; the pipeline unzips and
  picks the largest image).
- Prefer the version that **matches what is installed**, so NVRAM offsets line up for
  any later no-flash edit. The installed version comes from step 1's `dmidecode`.
- Vendor support sites often block automated downloads. If a direct fetch fails, ask
  the operator to download the file and drop it in `rom/`. Mirrors (e.g.
  station-drivers) carry older versions when the vendor lists only the latest.
- BIOS images are not redistributable and are gitignored; they stay local.

## 3. Build

```bash
make            # extract -> parse -> vault (clones+builds extractors on first run)
```

Requires `python3`, `rust`+`cargo`, `cmake`+a compiler. Report any missing tool.

## 4. Report

State what was produced: module count, parameter count, and any notable modules
(e.g. `AodDxe` for AMD Overclocking, `SioDynamicSetup` for the Super-I/O). The
numbers come from the `make` output and `build/catalog.json`.

## 5. Open and connect

- Tell the operator to open `vault/` in Obsidian and enable the
  [Semantic Vault MCP](https://community.obsidian.md/plugins/semantic-vault-mcp)
  plugin against it, then add that MCP server to the agent.
- First indexing of a large vault takes a while. Wait for it before traversing.
- Advise keeping Obsidian's global graph view closed while querying (it starves the
  in-Obsidian MCP server).

## 6. First traversal

Once the MCP server is reachable and indexed, run a traversal toward the goal from
step 1. Pattern (see `docs/agent-traversal.md`):

- `vault.search` by concept to resolve terminology to the board's labels.
- `graph.neighbors` on the relevant menu to get the setting cluster.
- `vault.read` the leaf note for its variable, offset, and decoded options.

Report findings plainly. If the operator wants to keep a finding, write it into the
note's `## Notes` section (preserved across regeneration).

## Cautions

- Do not flash or write NVRAM. Surface the offset and option byte; the operator
  decides and verifies.
- A wrong ODT, timing, or voltage value can leave the machine unstable or unbootable.
  Treat any proposed change as a hypothesis.
