# bios-tuning

Turn a UEFI BIOS image into a **browsable Obsidian knowledge graph** of every
firmware setting — including the thousands of parameters most vendors hide from
their graphical setup UI.

Modern AMI/Aptio BIOSes expose only a curated slice of their settings in the
menu. The full set — every AMD CBS/PBS knob, every DRAM timing, ODT/RTT
impedance, fabric clock, voltage rail, fan-table entry — lives in the firmware's
**IFR** (Internal Form Representation). This tool decompiles that, classifies it,
and renders it as a typed, cross-linked, colour-coded vault you can explore and
annotate.

It was built to make sense of an MSI MAG X870E TOMAHAWK WIFI (AM5 / Ryzen 9000),
but the extractor discovers modules by scanning — not by hardcoded GUIDs — so it
works on any AMI-based UEFI image.

## What you get

- **One note per parameter** (~3,800 on this board) with typed YAML frontmatter:
  variable + offset, value range, decoded options, default, menu path, and
  heuristic domain tags (`odt-si`, `memory-timing`, `voltage`, `fabric-clock`,
  `pbo-boost`, `thermal-fan`, …).
- **Menu (form) notes** that mirror the BIOS menu tree, **NVRAM variable notes**
  that map each setting to its byte offset (the no-flash edit map), and
  **maps-of-content** per module and per domain.
- **Wikilink edges** (param → menu, param → variable, P0–P3 siblings) and a
  pre-baked `.obsidian/graph.json` with **one graph colour per domain**.
- An **annotation layer**: anything under `## Notes` in a note (prose, tables,
  Mermaid diagrams) is preserved across regeneration.

## Requirements

- `python3`
- `rust` + `cargo` and `cmake` + a C/C++ compiler (to build the LongSoft
  extractors — done automatically by `make tools`)
- [Obsidian](https://obsidian.md) to browse the result

## Quick start

```bash
# 1. drop a BIOS image (or an MSI-style .zip) into rom/
cp ~/Downloads/7E59v2A91.zip rom/

# 2. run the pipeline (clones+builds extractors on first run)
make

# 3. open the vault/ folder in Obsidian
```

## Pipeline

```
rom/<image>  ──extract──>  ifr/*.ifr.txt  ──parse──>  build/catalog.json  ──vault──>  vault/
 (UEFIExtract +              (IFR text)      (parse_ifr.py)  (structured)   (build_vault.py)  (Obsidian)
  IFRExtractor, auto-
  discovers IFR modules)
```

| Stage | Command | Tool |
|-------|---------|------|
| 1. extract | `make extract` | `tools/extract_ifr.py` |
| 2. parse   | `make parse`   | `tools/parse_ifr.py` |
| 3. vault   | `make vault`   | `tools/build_vault.py` |

`make` runs all three. `make help` lists targets.

## Repository layout

| Path | Purpose | Tracked? |
|------|---------|----------|
| `tools/` | the three pipeline scripts | ✅ |
| `Makefile` | orchestration | ✅ |
| `rom/` | **drop your BIOS image here** (gitignored — blobs aren't redistributable) | ⛔ (README only) |
| `ifr/` | intermediate IFR text dumps | ⛔ generated |
| `build/` | intermediate `catalog.json` | ⛔ generated |
| `vault/` | the Obsidian vault — the "compiled" output | ⛔ generated |
| `tools-uefitool/`, `tools-ifrextractor/` | cloned LongSoft extractors | ⛔ external |

The vault is generated output and is gitignored. **Caveat:** hand annotations
(your `## Notes` sections) live inside `vault/` and are therefore *not* version
controlled by default — back them up if they become precious, or track the vault
deliberately.

## Credits

Built on the excellent [LongSoft](https://github.com/LongSoft) tooling:
[UEFITool](https://github.com/LongSoft/UEFITool) (UEFIExtract) and
[IFRExtractor-RS](https://github.com/LongSoft/IFRExtractor-RS).

## License

MIT — see [LICENSE](LICENSE).
