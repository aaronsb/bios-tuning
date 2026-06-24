#!/usr/bin/env python3
"""Parse ifrextractor-RS text dumps into a normalized JSON catalog.

Input:  one or more `*.ifr.txt` files produced by `ifrextractor <module> all`.
Output: a single catalog.json describing every form, varstore, and question
        (OneOf / Numeric / CheckBox), with menu context and heuristic domain tags.

The JSON is the structured-data layer; build_vault.py turns it into an Obsidian
vault. Keeping the two stages separate means the structured form is reusable
(e.g. diffing two BIOS versions) independent of any particular rendering.
"""
import json
import re
import sys
from pathlib import Path

# --- line matchers (ifrextractor-RS v1.6 format; leading tabs encode nesting) ---
RE_FORMSET = re.compile(r'^\s*FormSet Guid: ([0-9A-Fa-f-]+), Title: "(.*?)", Help: "(.*?)"')
RE_VARSTORE = re.compile(
    r'^\s*VarStore(?:Efi)? Guid: ([0-9A-Fa-f-]+), VarStoreId: (0x[0-9A-Fa-f]+),'
    r'(?: Attributes: 0x[0-9A-Fa-f]+,)? Size: (0x[0-9A-Fa-f]+), Name: "(.*?)"')
RE_FORM = re.compile(r'^\s*Form FormId: (0x[0-9A-Fa-f]+), Title: "(.*?)"')
RE_SUBTITLE = re.compile(r'^\s*Subtitle Prompt: "(.*?)", Help:')
RE_REF = re.compile(r'^\s*Ref Prompt: "(.*?)", Help: "(.*?)",.*?FormId: (0x[0-9A-Fa-f]+)')
RE_QHEAD = re.compile(r'^\s*(OneOf|Numeric|CheckBox) Prompt: "(.*?)",\s*(.*)$')
RE_QHELP = re.compile(r'^Help: "(.*?)",\s*(.*)$')
RE_OPTION = re.compile(r'^\s*OneOfOption Option: "(.*?)" Value: (\d+)(, Default)?')

def kv(rest: str) -> dict:
    """Parse the trailing ', Key: Value, Key: Value' part of a question line."""
    out = {}
    for m in re.finditer(r'(\w+):\s*([^,]+)', rest):
        out[m.group(1)] = m.group(2).strip()
    return out

# --- heuristic domain classification for rich graph labels ---
DOMAIN_RULES = [
    ("memory-timing", r'\bt(CL|RCD|RP|RAS|RC|RRD|FAW|WTR|WR|RTP|CWL|RFC|REFI|RDRD|WRWR|RDWR|WRRD|RDWRSC)\b|Cas Latency|\bRAS\b|\bCAS\b|Timing|tPHYRDL|RcvEn'),
    ("odt-si", r'ProcODT|\bODT\b|RTT|DrvStren|Drive Strength|CAD_?BUS|ClkDrv|AddrCmdDrv|CsOdtDrv|CkeDrv|Setup Time|Hold|Slew|DqsRtt|CK ODT|CS ODT|CA ODT|Impedance|Bus Termination'),
    ("voltage", r'\bVDD\w*|\bVDDQ\b|\bVDDP\b|\bVDDIO\b|\bVDDG\b|\bVSOC\b|\bVPP\b|Voltage|\bVID\b|Vcore'),
    ("fabric-clock", r'\bFCLK\b|\bUCLK\b|\bMCLK\b|\bBCLK\b|Fabric|Infinity|DF C|Memory Clock|Coupled|Frequency'),
    ("pbo-boost", r'\bPBO\b|Precision Boost|Curve Optimizer|Curve Shaper|Boost|\bPPT\b|\bTDC\b|\bEDC\b|Scalar|Overclock|Thermal Limit'),
    ("power-cstate", r'C-?state|Power Down|Global C|CPPC|Power Supply Idle|Package Power|\bECO\b|Eco Mode'),
    ("cpu-core", r'\bCore\b|\bSMT\b|Thread|Prefetch|\bSVM\b|x2APIC|Watchdog|Microcode|\bCCD\b|\bCCX\b'),
    ("security", r'\bTPM\b|Secure Boot|\bSME\b|TSME|Memory Encryption|Platform Security|\bPSP\b|Rollback|fTPM'),
    ("pcie-io", r'PCIe|PCIE|Lane|Bifurcat|ASPM|Above 4G|Re-?Size|Resizable|\bSR-IOV\b|\bIOMMU\b'),
    ("storage-usb", r'\bUSB\b|\bSATA\b|\bNVMe\b|\bAHCI\b|\bM\.2\b|XHCI'),
    ("thermal-fan", r'\bFan\b|Temperature|Thermal|\bHWM\b|Smart Fan|Pump'),
    ("boot-post", r'\bBoot\b|\bPOST\b|\bCSM\b|Setup Prompt|Logo|Fast Boot|NumLock|Boot Order'),
    ("memory-general", r'Memory|\bDRAM\b|\bDDR\b|\bUMC\b|Refresh|Bank|Rank|Interleav|Gear Down|Power Down'),
]
DOMAIN_RES = [(name, re.compile(pat, re.I)) for name, pat in DOMAIN_RULES]

def classify(name, help_, form):
    blob = f"{name} {help_} {form}"
    return [d for d, rx in DOMAIN_RES if rx.search(blob)]

def slug(s):
    s = re.sub(r'[^\w\s-]', '', s).strip().lower()
    return re.sub(r'[\s_]+', '-', s) or "untitled"

def parse_file(path: Path, module: str):
    varstores, params, forms, refs = {}, [], {}, []
    formset_title = module
    cur_form_id, cur_form_title, cur_sub = None, module, ""
    active = None  # the OneOf currently collecting options

    for line in path.read_text(errors="replace").splitlines():
        m = RE_OPTION.match(line)
        if m and active is not None:
            active["options"].append(
                {"text": m.group(1), "value": int(m.group(2)), "default": bool(m.group(3))})
            continue
        if re.match(r'^\s*End\s*$', line):
            active = None
            continue
        m = RE_FORMSET.match(line)
        if m:
            formset_title = m.group(2)
            continue
        m = RE_VARSTORE.match(line)
        if m:
            varstores[m.group(2)] = {"id": m.group(2), "guid": m.group(1),
                                     "size": m.group(3), "name": m.group(4)}
            continue
        m = RE_FORM.match(line)
        if m:
            cur_form_id, cur_form_title, cur_sub = m.group(1), m.group(2), ""
            forms[cur_form_id] = cur_form_title
            active = None
            continue
        m = RE_SUBTITLE.match(line)
        if m:
            if m.group(1).strip():
                cur_sub = m.group(1)
            continue
        m = RE_REF.match(line)
        if m:
            refs.append({"from": cur_form_id, "to": m.group(3),
                         "label": m.group(1)})
            continue
        m = RE_QHEAD.match(line)
        if m:
            qtype, name, rest = m.group(1), m.group(2), m.group(3)
            hm = RE_QHELP.match(rest)
            help_, rest = (hm.group(1), hm.group(2)) if hm else ("", rest)
            d = kv(rest)
            vs_id = d.get("VarStoreId")
            vs = varstores.get(vs_id, {})
            p = {
                "module": module,
                "formset": formset_title,
                "form_id": cur_form_id,
                "form": cur_form_title,
                "subtitle": cur_sub,
                "type": qtype.lower(),
                "name": name,
                "help": help_,
                "question_id": d.get("QuestionId"),
                "varstore_id": vs_id,
                "varstore_name": vs.get("name"),
                "varstore_guid": vs.get("guid"),
                "var_offset": d.get("VarOffset"),
                "size_bits": d.get("Size"),
                "min": d.get("Min"),
                "max": d.get("Max"),
                "step": d.get("Step"),
                "default": d.get("Default"),
                "mfg_default": d.get("MfgDefault"),
                "options": [],
                "domains": classify(name, help_, cur_form_title),
            }
            params.append(p)
            active = p if qtype == "OneOf" else None
            continue
    return varstores, params, forms, refs

def main():
    ifr_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("ifr")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("build/catalog.json")
    out.parent.mkdir(parents=True, exist_ok=True)

    MODMAP = {"Setup": "setup", "CbsSetupDxeRPL": "cbs-rpl",
              "CbsSetupDxePHX": "cbs-phx", "AmdPbsSetupDxe": "pbs"}
    catalog = {"modules": [], "varstores": {}, "params": [], "forms": {}, "refs": []}
    for f in sorted(ifr_dir.glob("*.ifr.txt")):
        stem = f.name.replace(".ifr.txt", "")
        module = MODMAP.get(stem, slug(stem))
        vs, params, forms, refs = parse_file(f, module)
        catalog["modules"].append({"module": module, "source": f.name,
                                   "params": len(params), "forms": len(forms)})
        for k, v in vs.items():
            catalog["varstores"][f"{module}::{k}"] = v
        catalog["params"].extend(params)
        catalog["forms"][module] = forms
        for r in refs:
            r["module"] = module
        catalog["refs"].extend(refs)

    out.write_text(json.dumps(catalog, indent=1))
    # summary to stderr
    p = catalog["params"]
    print(f"modules: {len(catalog['modules'])}  params: {len(p)}  "
          f"forms: {sum(len(v) for v in catalog['forms'].values())}  "
          f"varstores: {len(catalog['varstores'])}  refs: {len(catalog['refs'])}",
          file=sys.stderr)
    from collections import Counter
    dc = Counter(d for x in p for d in x["domains"])
    print("domain tag counts: " + ", ".join(f"{k}={v}" for k, v in dc.most_common()),
          file=sys.stderr)
    miss = sum(1 for x in p if x["form"] == x["module"])
    print(f"params with no resolved form: {miss}", file=sys.stderr)

if __name__ == "__main__":
    main()
