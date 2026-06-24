# ifr/ — extracted IFR text (intermediate, generated)

`make extract` writes one `<Module>.ifr.txt` here per IFR-bearing firmware module
(`Setup`, `CbsSetupDxeRPL`, `AmdPbsSetupDxe`, …), produced by IFRExtractor.

These are the human-readable decompiled forms — useful to `grep` directly, but the
canonical structured form is `build/catalog.json` (made by `make parse`).

Generated content is gitignored; this README is the only tracked file.
