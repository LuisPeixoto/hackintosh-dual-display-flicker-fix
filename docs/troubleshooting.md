# Troubleshooting

Each heading is a symptom, followed by its likely cause and what to do.

## `ioreg` prints nothing for `CFG_HIDE_HPD`

```bash
ioreg -c IOPCIDevice -l -w0 | grep CFG_HIDE_HPD
```

The property never reached the GPU. Check, in this order:

1. **You booted a different EFI.** With more than one drive or USB stick that has OpenCore, edit the one that actually
   starts. `nvram 4D1FDA02-38C7-4A6A-9CC6-4BCCA8B30102:boot-path` shows where OpenCore booted from.
2. **The PCI path is wrong.** It must be the path of your GPU, not the one from the example. Get it with
   `gfxutil -f display`, and compare character by character.
3. **The key sits under the wrong dictionary,** or is named in the wrong case. It is `CFG_HIDE_HPD`, under
   `DeviceProperties > Add > <your path>`.
4. **The entry is commented out.** Keys that start with `#` in OpenCore are ignored.
5. **The file was not saved,** or a config editor wrote a different copy.

## It is applied, but the flicker is the same

- **Measure it** instead of judging by eye: [measuring.md](measuring.md). Runs vary a lot, so use several.
- **The flicker may have a different cause on your machine.** This fix hides one notification. If your flicker does not
  come from it, nothing changes. A [test report](https://github.com/LuisPeixoto/hackintosh-dual-display-flicker-fix/issues/new?template=test_report.yml)
  that says "no change", with your numbers, is useful.
- **A very large HiDPI mode makes it worse.** Compare at the monitor's native resolution; see
  [`tools/display-mode.swift`](../tools/display-mode.swift).
- Check [what-did-not-work.md](what-did-not-work.md) so you do not repeat a dead end.

## `tools/measure-flicker.sh` prints zeros but I can see the flicker

The script counts one specific signature in the log. If it is zero while the screen blinks, the blink has another cause,
and that is worth reporting. Also check that you are not reading an empty log: in zsh `log` is a builtin, so use
`/usr/bin/log`, as in [measuring.md](measuring.md).

## A monitor is not detected after I power it on or plug it in

That is the expected side effect: the fix stops the system from reacting to link changes. Reboot, or sleep and wake the
machine, and it is detected. If it is a problem for you, remove the property and reboot.

## The machine does not boot after editing `config.plist`

Restore the backup of `config.plist` from before the edit. On a FAT32 EFI partition you can do that from Windows, Linux
or another macOS install. The fix adds one property and cannot stop OpenCore from loading, so a boot problem usually
means the file was damaged by the edit: validate it with the `ocvalidate` that matches your OpenCore version.

## `tools/carve-kext-text.py` says only x86_64 is supported

It reads Intel kernel collections only. Collections on Apple silicon encode their pointers in a way the tools do not
decode.

## The names or addresses in the guides do not match what I see

They belong to one macOS build. [reverse-engineering.md](reverse-engineering.md) describes how to find the same things
by name, which keeps working when addresses move.
