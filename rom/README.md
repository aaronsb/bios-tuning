# rom/ — drop your BIOS image here

Put a UEFI BIOS image in this directory, then run `make` from the repo root.

Accepted:
- a raw flash image (`.bin`, `.ROM`, `.CAP`, or a vendor-suffixed file like
  `E7E59AMSI.2A91`)
- a vendor `.zip` (e.g. an MSI BIOS download) — it's unzipped automatically

The pipeline picks the **largest** image-like file it finds here, so you can drop
the whole download without unpacking it.

**Nothing in this directory is committed** (see `.gitignore`). BIOS images are the
vendor's intellectual property and aren't redistributable — keep your own copy
here locally.
