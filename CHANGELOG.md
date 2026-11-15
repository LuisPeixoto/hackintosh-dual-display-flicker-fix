# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-11-15

First release: the fix, the tools to measure and check it, and the guides. Validated on one machine (RX 6600 XT,
macOS 26.2, OpenCore 1.0.6); test reports from other setups are wanted.

### Added

- **The fix:** `CFG_HIDE_HPD` as an 8-byte `Data` value on the GPU's `DeviceProperties` entry, with an example fragment in
  `examples/DeviceProperties-snippet.plist`. It makes Apple's AMD driver stop passing link-change notifications on to
  macOS, which is what made both monitors blink.
- **`tools/measure-flicker.sh`:** reproduces the trigger by opening and quitting stock apps, and counts the flicker
  (`drops` and `reconfigs`) from the system log. Apps that are already running are never touched.
- **`tools/display-mode.swift`:** lists a display's modes and switches one, to compare with and without HiDPI.
- **`tools/carve-kext-text.py` and `tools/disassemble.py`:** read the AMD framebuffer driver out of the kernel collection,
  search its strings, find which function uses a setting, and disassemble it.
- **Guides:** how the fix works, how to measure, what did not work, troubleshooting, reverse engineering and a roadmap.
- **Community files:** contributing guide, code of conduct, security policy, issue forms (including a test report form)
  and a pull request template.
- **CI** on Linux and macOS: the Python tools compile, the example plist is valid, and the script and the Swift tool parse.

### Known limits

- Tested on one machine. The cause is inferred from reading the driver, not from tracing it.
- Monitor hot-plug may go unnoticed while macOS runs, until a reboot or a sleep and wake. Not tested.
