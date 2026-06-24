# What this is

![The MS-7E59 BIOS rendered as an Obsidian vault](media/graph-overview.png)

A modern AMI/Aptio BIOS shows a few hundred options in its setup menu. Its IFR
(Internal Form Representation) defines several thousand more that the menu hides:
AMD CBS/PBS knobs, DRAM timings, ODT/RTT termination, drive strengths, fabric
clocks, voltages, fan tables. The hidden options still bind to NVRAM and the
silicon still reads them.

`bios-tuning` reads the IFR from a BIOS image and writes it out as an Obsidian
vault — one markdown note per parameter, menu, and NVRAM variable. Each note
records its type, domain tags, decoded option values, and byte offset in
frontmatter, and links to its menu, its variable, and its sibling profiles. The
vault is browsable in Obsidian and traversable by a reasoning agent through the
[Semantic Vault MCP](https://community.obsidian.md/plugins/semantic-vault-mcp)
plugin ([source](https://github.com/aaronsb/obsidian-mcp-plugin)).

The extraction is done by existing tools — LongSoft
[UEFITool](https://github.com/LongSoft/UEFITool) and
[IFRExtractor-RS](https://github.com/LongSoft/IFRExtractor-RS). This project
organizes their output into a graph and exposes it to an agent. It does not edit
or flash firmware; it locates and describes settings.

## Pipeline

```
rom/<image>  →  extract  →  ifr/*.ifr.txt  →  parse  →  build/catalog.json  →  vault/
              (UEFIExtract +                 (parse_ifr)  (structured)      (build_vault)
               IFRExtractor)
```

Module discovery is by scanning for IFR form packages, so any AMI/Aptio image
works, not only the board this was written against. A full AM5 board yields roughly
5,000 notes across ~20 firmware modules.

## The graph

- **param** — one setting. Frontmatter holds the NVRAM variable, offset, size,
  min/max, decoded options, default, and domain tags.
- **form** — one menu. Lists its parameters.
- **var** — one NVRAM variable. Lists the parameters bound to it, ordered by offset.
  This is the map for a no-flash edit.
- **moc** — per-module and per-domain indexes, plus `Home`.

Edges are wikilinks: parameter → menu, parameter → variable, parameter → sibling
profiles, menu → submenu. Tags group by module, type, domain, variable, and a
priority marker for memory-tuning parameters. The same files serve three readers: a
person reading markdown, Obsidian rendering the graph, an agent traversing over MCP.

## Why a graph

A BIOS is structured. The IFR records each question's VarStore and offset.
Promoting VarStore and form to nodes gives two independent groupings over the same
parameters — by menu and by variable. Domain tags give a third; content search
gives a fourth, by meaning. An agent reasoning about a setting enters through
whichever grouping fits the question and crosses to the others. When one grouping
misses, another finds it. The [walkthroughs](walkthroughs.md) show this in practice.

## Scope

- Extraction is delegated to UEFITool/IFRExtractor.
- No flashing, no NVRAM writes. The tool surfaces an offset and an option byte;
  applying it is the operator's decision and carries the usual risk — a wrong ODT or
  timing value is an unstable or unbootable machine.
- Naming heuristics target AMI/Aptio + AMD AGESA, but the parser is generic.

## See also

- [Getting started](getting-started.md)
- [Agent traversal](agent-traversal.md)
- [Walkthroughs](walkthroughs.md)
