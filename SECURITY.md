# Security policy

This project documents a property injected through OpenCore `DeviceProperties`, and ships small read-only helper
scripts. It does not run a service and does not handle credentials.

## Supported versions

Only the latest release is maintained while the project is below 1.0.

## Reporting a vulnerability

**Please do not open a public issue.** Use GitHub's private reporting instead:

<https://github.com/LuisPeixoto/hackintosh-dual-display-flicker-fix/security/advisories/new>

## What is in scope

- A helper script that writes or deletes anything it was not asked to
- Instructions that could leave a machine unable to boot without an obvious way back

## Design notes

- **The fix changes one `config.plist` on your EFI partition.** Back it up first; restoring that file undoes the fix.
  Nothing is written to macOS itself.
- **`tools/measure-flicker.sh`** opens and quits a few stock apps and reads the system log. It changes no settings.
- **`tools/display-mode.swift`** lists display modes and can switch one, and it asks for no privileges. A mode change
  from it is permanent until you change it back in System Settings, so the `set` command says so.
- **`tools/carve-kext-text.py`** only reads the kernel collection, and writes into the output folder you give it.
- **Logs can contain personal data** (process names, window titles, network names). Read what you paste into an issue.
