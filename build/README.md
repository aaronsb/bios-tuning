# build/ — structured catalog (intermediate, generated)

`make parse` writes `catalog.json` here: the normalized, structured form of every
parameter, form, NVRAM variable, and menu reference parsed out of `ifr/`.

This is the stable data layer — render it however you like. `make vault` consumes
it to build the Obsidian vault, but you could also diff two BIOS versions' catalogs,
or drive other tooling from it.

Generated content is gitignored; this README is the only tracked file.
