#!/usr/bin/env python3
"""Render catalog.json into an Obsidian vault: a typed graph of markdown notes.

Node types (all carry `type` in frontmatter; folders are just a human view):
  - param : one BIOS setting (the leaf nodes)
  - form  : one menu/page (the chapters/sections)
  - var   : one NVRAM variable (the no-flash edit map)
  - moc   : maps-of-content (Home, per-module, per-domain)

Filenames are the human title (so graph nodes read nicely); the machine-stable
kebab id lives in frontmatter as `id`. Names are made globally unique by
appending a disambiguator only on collision. Edges are [[wikilinks]];
nested #tags drive graph colouring. .obsidian/graph.json is pre-baked with one
colour per domain. Everything below `<!-- END GENERATED -->` is preserved on
re-run (the annotation layer; Obsidian renders Mermaid there).
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

GEN_END = "<!-- END GENERATED -->"

def slug(s):
    s = re.sub(r'[^\w\s.-]', '', str(s)).strip().lower()
    return re.sub(r'[\s_]+', '-', s) or "x"

def fs_safe(title):
    """Obsidian-friendly filename: keep caps, spaces -> underscores, strip illegal chars."""
    t = re.sub(r'[/\\:*?"<>|#^\[\]]', '-', str(title)).strip()
    return re.sub(r'\s+', '_', t) or "untitled"

def yaml_val(v):
    if isinstance(v, list):
        return "[" + ", ".join(yaml_val(x) for x in v) + "]"
    if v is None:
        return '""'
    s = str(v)
    if re.search(r'[:#\[\]{}",\'`]|^\s|\s$', s) or s == "":
        return '"' + s.replace('"', '\\"') + '"'
    return s

def frontmatter(d):
    return "---\n" + "".join(f"{k}: {yaml_val(v)}\n" for k, v in d.items()) + "---\n"

def link(name, display=None):
    return f"[[{name}|{display}]]" if (display and display != name) else f"[[{name}]]"

def write_note(path: Path, fm: dict, body: str, default_notes: str):
    preserved = None
    if path.exists():
        old = path.read_text(errors="replace")
        i = old.find(GEN_END)
        if i != -1:
            preserved = old[i + len(GEN_END):]
    out = frontmatter(fm) + "\n<!-- BEGIN GENERATED -->\n" + body + "\n" + GEN_END
    out += preserved if (preserved and preserved.strip()) else ("\n\n" + default_notes)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(out)

PRIORITY_DOMAINS = {"memory-timing", "odt-si", "voltage", "fabric-clock",
                    "memory-general", "power-cstate"}
DOMAIN_COLORS = {
    "odt-si": 0xE05B4F, "memory-timing": 0xE8A33D, "voltage": 0xF2D45C,
    "fabric-clock": 0x4FC3F7, "pbo-boost": 0xCE6FE0, "power-cstate": 0x9575CD,
    "cpu-core": 0x66BB6A, "security": 0xD7263D, "pcie-io": 0x26A69A,
    "storage-usb": 0xA1887F, "thermal-fan": 0xFF7043, "boot-post": 0x90A4AE,
    "memory-general": 0x6FB1FC,
}
DOMAIN_ORDER = ["odt-si", "memory-timing", "voltage", "fabric-clock", "pbo-boost",
                "power-cstate", "cpu-core", "security", "pcie-io", "storage-usb",
                "thermal-fan", "boot-post", "memory-general"]

def write_obsidian(vault: Path, domains):
    od = vault / ".obsidian"
    od.mkdir(parents=True, exist_ok=True)
    gp = od / "graph.json"
    cfg = {}
    if gp.exists():
        try:
            cfg = json.loads(gp.read_text())
        except Exception:
            cfg = {}
    cfg["showTags"] = True
    cfg["showOrphans"] = True
    cfg["colorGroups"] = [
        {"query": f"tag:#domain/{d}", "color": {"a": 1, "rgb": DOMAIN_COLORS[d]}}
        for d in domains if d in DOMAIN_COLORS]
    cfg.setdefault("nodeSizeMultiplier", 1.1)
    cfg.setdefault("lineSizeMultiplier", 0.6)
    cfg.setdefault("repelStrength", 12)
    cfg.setdefault("linkDistance", 200)
    gp.write_text(json.dumps(cfg, indent=2))

def main():
    catalog = json.loads(Path(sys.argv[1] if len(sys.argv) > 1 else "build/catalog.json").read_text())
    vault = Path(sys.argv[2] if len(sys.argv) > 2 else "vault")
    params = catalog["params"]

    # global filename allocator: human title, disambiguate only on collision
    used = set()
    def take(title, hints=()):
        base = fs_safe(title)
        hs = [fs_safe(h) for h in hints]
        c, i = base, 1
        while c.lower() in used:
            if hs:
                c = f"{base}_{hs.pop(0)}"
            else:
                i += 1
                c = f"{base}_{i}"
        used.add(c.lower())
        return c

    # ---- reserve MOC/meta names first so they keep clean names ----
    home_name = take("Home")
    legend_name = take("Domain colours")
    modules = sorted({p["module"] for p in params})
    moc_name = {m: take(f"{m} index") for m in modules}

    # form + var titles
    form_title, form_mod = {}, {}
    for p in params:
        form_title[(p["module"], p["form_id"])] = p["form"]
        form_mod[(p["module"], p["form_id"])] = p["module"]
    form_fname = {}
    for key in sorted(form_title, key=lambda k: (k[0], form_title[k])):
        m, fid = key
        form_fname[key] = take(form_title[key] or fid, hints=[m, fid])

    var_fname = {}
    var_params = defaultdict(list)
    for p in params:
        if p.get("varstore_name"):
            var_params[p["varstore_name"]].append(p)
    for v in sorted(var_params):
        var_fname[v] = take(v, hints=["NVRAM var", "var"])

    domains_present = sorted({d for p in params for d in p["domains"]})
    dom_name = {d: take(f"Domain {d}") for d in domains_present}

    # ---- param filenames + indices ----
    by_form = defaultdict(list)
    by_module = defaultdict(set)
    by_domain = defaultdict(set)
    sib = defaultdict(list)
    for p in params:
        nm = (p["name"] or "").strip() or f"param {p['question_id']}"
        p["_file"] = take(nm, hints=[p["form"], p["module"], p["question_id"] or "q"])
        key = (p["module"], p["form_id"])
        by_form[key].append(p)
        by_module[p["module"]].add(p["form_id"])
        for d in p["domains"]:
            by_domain[d].add(key)
        sk = (p["module"], p["varstore_id"], re.sub(r' P\d+$', '', p["name"]))
        sib[sk].append(p)

    # ---- param notes ----
    for p in params:
        tags = [f"module/{p['module']}", f"type/{p['type']}"]
        tags += [f"domain/{d}" for d in p["domains"]]
        if p.get("varstore_name"):
            tags.append(f"varstore/{slug(p['varstore_name'])}")
        tags.append("platform/apu-phoenix" if p["module"] == "cbs-phx" else "platform/desktop")
        if set(p["domains"]) & PRIORITY_DOMAINS:
            tags.append("priority/memory-tuning")
        fid_key = (p["module"], p["form_id"])
        fm = {
            "title": p["name"], "id": f"{p['module']}__{slug(p['name'])}__{slug(p['question_id'] or 'q')}",
            "type": "param", "module": p["module"], "menu": p["form"],
            "section": p["subtitle"] or "", "qtype": p["type"],
            "varstore": p.get("varstore_name") or "", "varstore_id": p["varstore_id"] or "",
            "offset": p["var_offset"] or "", "size_bits": p["size_bits"] or "",
            "min": p["min"] or "", "max": p["max"] or "", "step": p["step"] or "",
            "default": p["default"] or "", "options_count": len(p["options"]),
            "question_id": p["question_id"] or "", "tags": tags,
        }
        b = [f"# {p['name']}", ""]
        if p["help"]:
            b += [f"> {p['help']}", ""]
        b.append(f"**Menu:** {link(form_fname[fid_key], p['form'])}"
                 + (f" › {p['subtitle']}" if p["subtitle"] else ""))
        if p.get("varstore_name"):
            b.append(f"**NVRAM:** {link(var_fname[p['varstore_name']], p['varstore_name'])}"
                     f" @ `{p['var_offset']}`  ·  `{p['size_bits']}`-bit  ·  id `{p['varstore_id']}`")
        if p["type"] == "numeric":
            b.append(f"**Range:** `{p['min']}` – `{p['max']}`  step `{p['step']}`"
                     + (f"  ·  default `{p['default']}`" if p["default"] else ""))
        if p["options"]:
            b += ["", "| Value | Option | |", "|--:|---|:-:|"]
            for o in p["options"]:
                b.append(f"| `{o['value']}` | {o['text']} | {'✓ default' if o['default'] else ''} |")
        sk = (p["module"], p["varstore_id"], re.sub(r' P\d+$', '', p["name"]))
        sibs = [s for s in sib[sk] if s is not p]
        if sibs:
            b += ["", "**Profiles/siblings:** "
                  + " · ".join(link(s["_file"], (s["name"].split()[-1] if s["name"].split() else "opt"))
                              for s in sibs)]
        notes = ("## Notes\n\n_Annotations below are preserved across regeneration._\n"
                 "_Obsidian renders Mermaid fenced blocks here — drop diagrams freely._\n")
        write_note(vault / "params" / p["module"] / f"{p['_file']}.md", fm, "\n".join(b), notes)

    # ---- form notes (chapters) ----
    for key, plist in by_form.items():
        module, fid = key
        title = form_title[key]
        doms = sorted({d for p in plist for d in p["domains"]})
        children = sorted({r["to"] for r in catalog["refs"]
                           if r.get("module") == module and r["from"] == fid})
        fm = {"title": title, "id": f"form__{module}__{slug(title)}", "type": "form",
              "module": module, "param_count": len(plist),
              "tags": [f"module/{module}"] + [f"domain/{d}" for d in doms]}
        b = [f"# {title}", "", f"_Menu in **{module}** · {len(plist)} parameters_", "",
             f"MOC: {link(moc_name[module])}", ""]
        bysub = defaultdict(list)
        for p in plist:
            bysub[p["subtitle"]].append(p)
        for sub, ps in bysub.items():
            if sub:
                b.append(f"### {sub}")
            for p in ps:
                tag = "·".join(p["domains"][:2])
                b.append(f"- {link(p['_file'])}" + (f"  <small>{tag}</small>" if tag else ""))
            b.append("")
        kids = [(module, c) for c in children if (module, c) in form_fname]
        if kids:
            b.append("## Submenus")
            for k in kids:
                b.append(f"- {link(form_fname[k], form_title[k])}")
        write_note(vault / "forms" / module / f"{form_fname[key]}.md", fm, "\n".join(b), "## Notes\n\n")

    # ---- variable notes (no-flash edit map) ----
    for vname, plist in var_params.items():
        guid = plist[0].get("varstore_guid", "")
        plist2 = sorted(plist, key=lambda p: int(p["var_offset"] or "0x0", 16))
        fm = {"title": vname, "id": f"var__{slug(vname)}", "type": "var", "guid": guid,
              "param_count": len(plist), "tags": [f"varstore/{slug(vname)}"]}
        b = [f"# NVRAM variable: `{vname}`", "", f"GUID `{guid}`", "",
             "Parameters bound to this variable, by offset (the no-flash edit map):", "",
             "| Offset | Bits | Parameter | Menu |", "|---|--:|---|---|"]
        for p in plist2:
            b.append(f"| `{p['var_offset']}` | {p['size_bits']} | {link(p['_file'])} "
                     f"| {link(form_fname[(p['module'], p['form_id'])], p['form'])} |")
        write_note(vault / "vars" / f"{var_fname[vname]}.md", fm, "\n".join(b), "## Notes\n\n")

    # ---- MOCs ----
    for module, fids in by_module.items():
        forms = sorted(((fid, form_title[(module, fid)], len(by_form[(module, fid)]))
                        for fid in fids), key=lambda x: x[1])
        fm = {"title": f"{module} index", "type": "moc", "module": module,
              "tags": [f"module/{module}", "moc"]}
        b = [f"# {module} — menu index", "",
             f"_{len(forms)} menus · {sum(f[2] for f in forms)} parameters_", ""]
        for fid, t, c in forms:
            b.append(f"- {link(form_fname[(module, fid)], t)} <small>({c})</small>")
        write_note(vault / "00-index" / f"{moc_name[module]}.md", fm, "\n".join(b), "## Notes\n\n")

    for dom, keys in sorted(by_domain.items()):
        fm = {"title": f"domain: {dom}", "type": "moc", "domain": dom,
              "tags": [f"domain/{dom}", "moc"]}
        b = [f"# Domain — {dom}", "",
             f"_Search tag:_ `#domain/{dom}` · {len(keys)} menus", "", "Menus containing this domain:", ""]
        for key in sorted(keys, key=lambda k: form_title.get(k, "")):
            b.append(f"- {link(form_fname[key], form_title[key])} <small>({key[0]})</small>")
        write_note(vault / "00-index" / f"{dom_name[dom]}.md", fm, "\n".join(b), "## Notes\n\n")

    # ---- legend + Home ----
    present = [d for d in DOMAIN_ORDER if d in by_domain] + \
              [d for d in sorted(by_domain) if d not in DOMAIN_ORDER]
    write_obsidian(vault, present)
    leg = ["# Domain colour legend", "",
           "Graph-view colours (baked into `.obsidian/graph.json`):", "",
           "| Colour | Domain | Tag |", "|---|---|---|"]
    for d in present:
        hexc = f"#{DOMAIN_COLORS.get(d, 0):06X}" if d in DOMAIN_COLORS else "—"
        leg.append(f"| `{hexc}` | {link(dom_name[d], d)} | `#domain/{d}` |")
    write_note(vault / "00-index" / f"{legend_name}.md",
               {"title": "Domain colours", "type": "moc", "tags": ["moc"]},
               "\n".join(leg), "## Notes\n\n")

    home_b = [
        "# MS-7E59 BIOS Vault — MAG X870E TOMAHAWK WIFI (AGESA 1.2.0.3g / BIOS 2.A91)", "",
        f"**{len(params)} parameters · {len(by_form)} menus · {len(var_params)} NVRAM variables**", "",
        f"Colour legend: {link(legend_name)}", "", "## Modules (books)",
    ] + [f"- {link(moc_name[m])}" for m in modules] + ["", "## Domains (themes)"] \
      + [f"- {link(dom_name[d], d)}" for d in present] + ["", "## NVRAM variables (edit map)"] \
      + [f"- {link(var_fname[v])}" for v in sorted(var_params)] + [
        "", "## How to use", "",
        "- **Graph view**: colours are per-domain (see legend). Filter `#priority/memory-tuning` + `#platform/desktop` for your tuning set.",
        "- **Annotate**: notes/diagrams under `## Notes` in any file are preserved on regen.",
    ]
    write_note(vault / f"{home_name}.md", {"title": "Home", "type": "moc", "tags": ["moc"]},
               "\n".join(home_b), "## Notes\n\n")

    nfiles = sum(1 for _ in vault.rglob("*.md"))
    print(f"vault: {vault}  ({nfiles} notes)  params={len(params)} forms={len(by_form)} "
          f"vars={len(var_params)} domains={len(by_domain)}")
    print(f"obsidian graph colour groups: {len(present)} domains")

if __name__ == "__main__":
    main()
