# vault/ — the Obsidian vault (generated output)

`make vault` renders `build/catalog.json` into this folder as a typed,
cross-linked Obsidian vault. **Open this directory in Obsidian.**

- `Home.md` — start here (library overview)
- `00-index/` — maps-of-content (per module, per domain) + the colour legend
- `params/` — one note per BIOS setting
- `forms/` — one note per menu (the chapters)
- `vars/` — one note per NVRAM variable (offset edit map)
- `.obsidian/graph.json` — pre-baked graph colours, one per domain

This is "compiled" output and is gitignored. Regenerate it any time with
`make vault`.

> **Annotation caveat:** anything you add under a `## Notes` heading is preserved
> across regeneration — but because this folder is gitignored, those annotations
> are **not version controlled** by default. If your notes/diagrams become
> valuable, back them up or track the vault deliberately.
