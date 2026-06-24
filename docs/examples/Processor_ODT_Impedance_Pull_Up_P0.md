---
title: Processor ODT Impedance Pull Up P0
id: cbs-rpl__processor-odt-impedance-pull-up-p0__0x8f
type: param
module: cbs-rpl
menu: DDR Bus Configuration
section: DDR Bus Configuration
qtype: oneof
varstore: AmdSetupRPL
varstore_id: 0x5000
offset: 0x3D2
size_bits: 8
min: 0x0
max: 0xFF
step: 0x0
default: ""
options_count: 21
question_id: 0x8F
tags: [module/cbs-rpl, type/oneof, domain/odt-si, domain/memory-general, varstore/amdsetuprpl, platform/desktop, priority/memory-tuning]
---

<!-- BEGIN GENERATED -->
# Processor ODT Impedance Pull Up P0

> Specifies the Processor ODT Impedance Pull Up P0

**Menu:** [[DDR_Bus_Configuration_cbs-rpl|DDR Bus Configuration]] › DDR Bus Configuration
**NVRAM:** [[AmdSetupRPL]] @ `0x3D2`  ·  `8`-bit  ·  id `0x5000`

| Value | Option | |
|--:|---|:-:|
| `255` | Auto | ✓ default |
| `0` | High Impedance |  |
| `1` | 480 ohm |  |
| `2` | 240 ohm |  |
| `3` | 160 ohm |  |
| `4` | 120 ohm |  |
| `5` | 96 ohm |  |
| `6` | 80 ohm |  |
| `7` | 68 ohm |  |
| `12` | 60 ohm |  |
| `13` | 53 ohm |  |
| `14` | 48 ohm |  |
| `15` | 43 ohm |  |
| `28` | 40 ohm |  |
| `29` | 36 ohm |  |
| `30` | 34 ohm |  |
| `31` | 32 ohm |  |
| `60` | 30 Ohm |  |
| `61` | 28 ohm |  |
| `62` | 26 ohm |  |
| `63` | 25 ohm |  |

**Profiles/siblings:** [[Processor_ODT_Impedance_Pull_Up_P1|P1]] · [[Processor_ODT_Impedance_Pull_Up_P2|P2]] · [[Processor_ODT_Impedance_Pull_Up_P3|P3]]
<!-- END GENERATED -->

## Notes

### What this knob is

Processor ODT (on-die termination) is the termination the CPU memory controller
presents on the DQ/data bus. On AM5/DDR5 it is split by direction into a **pull-up**
and a **pull-down** leg; this note is the pull-up, see
[[Processor_ODT_Impedance_Pull_Down_P0_DDR_Bus_Configuration|Pull Down P0]]. The
`P0`–`P3` profiles correspond to the controller's gear/voltage states; `P0` applies
at the trained operating point. The option byte maps to a resistance (table above).

It is one leg of a matched termination system. The DRAM-side termination is the RTT
family — [[Dram_ODT_impedance_RTT_PARK_P0_DDR_Bus_Configuration|RTT_PARK]] (idle),
`RTT_NOM_RD`/`RTT_NOM_WR` (reads/writes), `RTT_WR` (writes) — and the CAD bus and DQ
drive strengths sit in the same menu. Changing one leg shifts the correct value of
the others.

```mermaid
flowchart LR
  subgraph CPU["memory controller"]
    PU["ProcODT Pull Up"]:::odt
    PD["ProcODT Pull Down"]:::odt
    DQ["DQ drive strength"]:::ds
  end
  CPU ==>|DQ / data bus| DRAM
  subgraph DRAM["DRAM — 4 ranks per channel"]
    RP["RTT_PARK (idle)"]:::odt
    RN["RTT_NOM_RD / WR"]:::odt
    RW["RTT_WR (writes)"]:::odt
  end
  classDef odt fill:#E05B4F,stroke:#FF8A80,color:#ffffff
  classDef ds fill:#E8A33D,stroke:#FFD180,color:#1A1A1A
```

### Why it matters at 4× dual-rank (2DPC)

Two dual-rank DIMMs per channel present four ranks per channel. The added parallel
termination load is why EXPO (validated for one DIMM per channel) will not train, and
why these values must be set by hand. Findings for this class of config:

- ProcODT in the **28–48 Ω** band is typical; above ~48 Ω is rarely useful and
  perturbs many voltages. Common bytes here: `28 = 40Ω`, `14 = 48Ω`, `12 = 60Ω`.
- `RTT_PARK` around RZQ/3–RZQ/4. `RTT_NOM` is often disabled, but with more than one
  rank per channel it frequently cannot be set OFF without a CMOS clear.
- `VDDIO` at or above **1.35 V** is commonly needed at this rank count; the SOC/VDDP
  domain is the usual limiter in 2DPC.

These are starting points, not answers — the correct value is rock stable; near
misses pass briefly and fail under load.

### To apply (no flash)

Write the chosen byte to `AmdSetupRPL` offset `0x3D2` (`setup_var`), set the matching
pull-down, reboot, and validate with a memory stress test (Prime95 Small 240k +
Large 864k). Recoverable with a CMOS clear.

### Sources

- [TechPowerUp — Ryzen Memory OC: procODT, RTT & CAD_BUS](https://www.techpowerup.com/review/amd-ryzen-memory-tweaking-overclocking-guide/7.html)
- [Overclock.net — AMD High-Capacity DDR5 OC, dual-rank](https://www.overclock.net/threads/amd-high-capacity-ddr5-oc-dual-rank-dimms.1816297/page-2)
- [Level1Techs — AM5 4-DIMM dual-rank 128GB Hynix](https://forum.level1techs.com/t/am5-ddr5-4-dimm-dual-rank-128gb-hynix-die-doubts/220251)
