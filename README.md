<h1 align="center">Hackintosh dual-display flicker fix</h1>

<p align="center">
  <b>Both monitors blink on macOS when two displays are connected to an AMD Navi GPU on a Hackintosh?</b><br />
  One OpenCore property, <code>CFG_HIDE_HPD</code>, stopped it on the machine it was found on.
</p>

<p align="center">
  <a href="https://github.com/LuisPeixoto/hackintosh-dual-display-flicker-fix/actions/workflows/ci.yml"><img src="https://github.com/LuisPeixoto/hackintosh-dual-display-flicker-fix/actions/workflows/ci.yml/badge.svg" alt="CI status" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-7c5cff.svg" alt="MIT license" /></a>
  <a href="https://github.com/LuisPeixoto/hackintosh-dual-display-flicker-fix/releases"><img src="https://img.shields.io/github/v/release/LuisPeixoto/hackintosh-dual-display-flicker-fix?include_prereleases&color=22d3ee" alt="Latest release" /></a>
  <img src="https://img.shields.io/badge/status-experimental-orange.svg" alt="Status: experimental" />
  <a href="CONTRIBUTING.md"><img src="https://img.shields.io/badge/test%20reports-welcome-brightgreen.svg" alt="Test reports welcome" /></a>
</p>

<p align="center">
  <a href="#quick-start">Quick start</a> ·
  <a href="docs/how-it-works.md">How it works</a> ·
  <a href="docs/measuring.md">Measuring</a> ·
  <a href="docs/what-did-not-work.md">What did not work</a> ·
  <a href="docs/troubleshooting.md">Troubleshooting</a> ·
  <a href="docs/reverse-engineering.md">Reverse engineering</a>
</p>

> **Status: experimental.** Validated on **one machine**: an Intel Hackintosh with a RX 6600 XT (Navi 23), macOS 26.2,
> OpenCore 1.0.6 and WhateverGreen 1.7.1. It is shared so that others can confirm it or prove it wrong. Please send a
> [test report](https://github.com/LuisPeixoto/hackintosh-dual-display-flicker-fix/issues/new?template=test_report.yml),
> whichever way it goes.

## The problem

With two monitors connected, both screens blink when you open an app, and now and then on their own. With one monitor
connected it never happens, and on Windows and Linux on the same machine it never happens either. Changing ports,
adapters, refresh rates or color depth does not help, and it happens even if the second monitor is switched off but
still plugged in.

## Highlights

- **A one-line fix.** Add `CFG_HIDE_HPD` as an 8-byte `Data` value to your GPU's entry in `DeviceProperties`. No kext, no
  patch, no boot-arg.
- **Measured, not guessed.** [`tools/measure-flicker.sh`](tools/measure-flicker.sh) counts the flicker from the system
  log, so you can compare before and after with numbers. On the development machine it went from about two events per
  run (up to ten with a large HiDPI mode) to zero.
- **Explained, and checkable.** The setting was found by reading Apple's AMD driver, and the
  [reverse-engineering guide](docs/reverse-engineering.md) lets you repeat every step on your own machine.
- **Honest about its limits.** One machine, a cause inferred from code, and a likely side effect (monitor hot-plug may go
  unnoticed until a reboot) that has not been tested. See [how-it-works.md](docs/how-it-works.md).
- **Dead ends included.** [What did not work](docs/what-did-not-work.md) lists what was tried first, so you can skip it.

## Quick start

1. **Back up** the `config.plist` on your EFI partition.
2. Find your GPU's PCI path (`gfxutil -f display`, the part after `=`).
3. In `config.plist`, under `DeviceProperties > Add > <your GPU path>`, add:

   | Key | Type | Value |
   |-----|------|-------|
   | `CFG_HIDE_HPD` | Data | `0100000000000000` |

   See [`examples/DeviceProperties-snippet.plist`](examples/DeviceProperties-snippet.plist) for the exact shape.
4. Reboot, then check it was applied:

   ```bash
   ioreg -c IOPCIDevice -l -w0 | grep CFG_HIDE_HPD
   # "CFG_HIDE_HPD" = <0100000000000000>
   ```

5. Measure, with the same display modes as before:

   ```bash
   tools/measure-flicker.sh
   # loops=4 drops=0 reconfigs=0
   ```

To undo it, put the backup of `config.plist` back.

## Documentation

| Guide | What it covers |
|-------|----------------|
| [How it works](docs/how-it-works.md) | The problem, applying the fix, what it changes, the evidence, side effects and limits |
| [Measuring](docs/measuring.md) | What the flicker looks like in the log, the measurement script, how to compare runs fairly |
| [What did not work](docs/what-did-not-work.md) | Power management, GPU audio, `Dal*` settings, display modes: what was tried and measured |
| [Troubleshooting](docs/troubleshooting.md) | Symptom, cause and fix, one heading each |
| [Reverse engineering](docs/reverse-engineering.md) | How to read the driver out of the kernel collection and check every claim |
| [Roadmap](docs/roadmap.md) | Where the project stands, the reports it needs, and ideas |
| [Changelog](CHANGELOG.md) | What changed in each release |

## Project layout

| Path | What it is |
|------|------------|
| `examples/` | The `DeviceProperties` fragment to merge into your `config.plist` |
| `tools/measure-flicker.sh` | Counts flicker events from the system log under an app-launch load |
| `tools/display-mode.swift` | Lists and switches display modes, to compare with and without HiDPI |
| `tools/carve-kext-text.py` | Carves a kext's `__TEXT` and symbols out of a kernel collection |
| `tools/disassemble.py` | Lists functions, searches strings, finds references and disassembles a carved kext |
| `docs/` | The guides above |

## Contributing

Test reports are the most valuable contribution: this fix gets more useful with every GPU, macOS version and monitor
setup that confirms or refutes it. Read [CONTRIBUTING.md](CONTRIBUTING.md) first. Security reports go through
[SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE). The fix and the tools are original work. The driver they help you read is Apple's, and nothing derived from
it is included in this repository.
