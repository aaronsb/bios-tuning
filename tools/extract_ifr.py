#!/usr/bin/env python3
"""Auto-extract IFR text from a UEFI BIOS image — the first stage of the pipeline.

Drop a flash image (or an MSI-style .zip) into rom/ and this:
  1. unzips any archives, picks the largest image file,
  2. unpacks it with UEFIExtract,
  3. finds every PE32 module that actually contains IFR *form* packages
     (discovery by scanning, not a hardcoded GUID list — so it works on any
     AMI/Aptio board, not just this one),
  4. runs IFRExtractor on each -> ifr/<ModuleName>.ifr.txt.

Stage 2 (parse_ifr.py) and stage 3 (build_vault.py) then turn that into the vault.
"""
import argparse
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

IMG_SKIP = {".zip", ".txt", ".md", ".json", ".py", ".7z"}
NAME_RE = re.compile(r'_([A-Za-z0-9]+)_body\.bin$')

def unzip_all(rom_dir: Path):
    for z in rom_dir.glob("*.zip"):
        try:
            with zipfile.ZipFile(z) as zf:
                zf.extractall(rom_dir)
            print(f"[extract] unzipped {z.name}")
        except Exception as e:
            print(f"[extract] skip {z.name}: {e}")

def find_image(rom_dir: Path) -> Path | None:
    cands = [p for p in rom_dir.rglob("*")
             if p.is_file() and p.suffix.lower() not in IMG_SKIP
             and ".dump" not in str(p) and p.stat().st_size > 1_000_000]
    return max(cands, key=lambda p: p.stat().st_size) if cands else None

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", help="explicit image path (default: largest under --rom-dir)")
    ap.add_argument("--rom-dir", default="rom")
    ap.add_argument("--out", default="ifr")
    ap.add_argument("--uefiextract", required=True)
    ap.add_argument("--ifrextractor", required=True)
    ap.add_argument("--min-forms", type=int, default=1)
    a = ap.parse_args()

    rom_dir = Path(a.rom_dir)
    unzip_all(rom_dir)
    rom = Path(a.rom) if a.rom else find_image(rom_dir)
    if not rom or not rom.exists():
        sys.exit(f"[extract] no BIOS image >1MB found in {rom_dir}/ "
                 f"(drop a .bin/.ROM/.CAP or an MSI .zip there)")
    print(f"[extract] image: {rom}  ({rom.stat().st_size:,} bytes)")

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.ifr.txt"):   # clean stale modules from a previous BIOS
        old.unlink()

    dump = Path(f"{rom}.dump")
    if dump.exists():
        shutil.rmtree(dump)
    # 'unpack' = legacy flat dump: one Section_*_<Name>_body.bin per item, which
    # is what we scan. ('all'/default produce a nested tree with generic names.)
    subprocess.run([a.uefiextract, str(rom), "unpack"], capture_output=True)
    if not dump.exists():
        sys.exit("[extract] UEFIExtract produced no .dump directory")

    bodies = sorted(dump.glob("*PE32*body.bin"))
    print(f"[extract] scanning {len(bodies)} PE32 modules for IFR forms...")
    written = 0
    for b in bodies:
        lst = subprocess.run([a.ifrextractor, str(b), "list"],
                             capture_output=True, text=True)
        forms = len(re.findall(r'form package', lst.stdout, re.I))
        if forms < a.min_forms:
            continue
        subprocess.run([a.ifrextractor, str(b), "all"], capture_output=True)
        produced = sorted(b.parent.glob(b.name + "*.ifr.txt"),
                          key=lambda p: p.stat().st_size)
        if not produced:
            continue
        m = NAME_RE.search(b.name)
        mod = m.group(1) if m else b.stem
        dst = out / f"{mod}.ifr.txt"
        src = produced[-1]                      # largest, if a name repeats
        if not dst.exists() or src.stat().st_size > dst.stat().st_size:
            dst.write_bytes(src.read_bytes())
            print(f"  + {mod}.ifr.txt  (forms={forms}, {src.stat().st_size:,} B)")
            written += 1
        for p in produced:                      # tidy up so next run is clean
            p.unlink()
    print(f"[extract] wrote {written} IFR module(s) to {out}/")
    if not written:
        sys.exit("[extract] no IFR modules found — is this a UEFI/AMI image?")

if __name__ == "__main__":
    main()
