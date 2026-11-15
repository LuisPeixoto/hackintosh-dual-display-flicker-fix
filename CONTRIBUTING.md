# Contributing

Thank you for helping! The most valuable contribution is a **test report**: this fix was validated on one machine, and
it gets more useful with every GPU, macOS version and monitor setup that confirms or refutes it.

By participating you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Ways to contribute

- **Send a test report** with the
  [test report form](https://github.com/LuisPeixoto/hackintosh-dual-display-flicker-fix/issues/new?template=test_report.yml).
  Include the before and after numbers from [docs/measuring.md](docs/measuring.md), whether the fix worked or not.
- **Report a problem** with the
  [bug report form](https://github.com/LuisPeixoto/hackintosh-dual-display-flicker-fix/issues/new?template=bug_report.yml).
- **Improve the docs.** Clearer wording, missing steps and corrections are all welcome.
- **Improve the tools** in `tools/`, or port the measurement script to other setups.

For anything bigger than a small fix, please open an issue first so we can agree on the approach.

## Ground rules

- Everything in the repository is **English**: docs, comments, commit messages, issue text.
- **Be honest about evidence.** Say what you measured, on which hardware, and what you did not verify. A result that
  contradicts the fix is as useful as one that confirms it.
- **Never commit Apple binaries**: no kernel collections, no kext binaries, no disassembly dumps. Describe how to
  produce them with the tools in `tools/` instead.
- **Remove personal data** (serial numbers, UUIDs, SMBIOS values, email addresses) from anything you paste.

## Workflow

1. Fork the repository and create a branch from `main` (`docs/…`, `fix/…`, `feat/…`).
2. Make your change in small, focused commits using
   [Conventional Commits](https://www.conventionalcommits.org/): `type(scope): imperative summary`.
3. Run the checks below.
4. Open a pull request and fill in the template.

## Checks

```bash
python3 -m py_compile tools/*.py
zsh -n tools/measure-flicker.sh
python3 -c "import plistlib,sys; plistlib.load(open('examples/DeviceProperties-snippet.plist','rb'))"
swiftc -parse tools/display-mode.swift   # macOS only
```
