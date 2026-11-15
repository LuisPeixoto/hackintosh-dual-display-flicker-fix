# How the fix works

Short version: add one property, `CFG_HIDE_HPD`, to your GPU in OpenCore's `DeviceProperties`. It tells Apple's AMD
driver not to pass link-change (hot-plug) notifications on to macOS.

## The problem

On the machine this was found on (Intel Hackintosh, RX 6600 XT, two monitors: one on DisplayPort, one HDMI-only through a
DisplayPort to HDMI adapter), both monitors blinked whenever apps were opened, and now and then on their own. Windows and
Linux on the same machine, ports and cables were fine, and so was macOS with either monitor alone.

What the system log showed, and what the numbers looked like, is in [measuring.md](measuring.md). In one line: a display
falls to a `1 x 1` mode and returns, and WindowServer reconfigures **all** displays, which is the blink.

## Apply the fix

1. **Back up** the `config.plist` on your EFI partition. Restoring that file undoes everything below.
2. **Find your GPU's PCI path.** It is the same path you already see in your config if it has an entry for the GPU. To
   list it, use [gfxutil](https://github.com/acidanthera/gfxutil):

   ```bash
   gfxutil -f display
   # 00:1:0 1002:73FF /PCI0@0/PEG0@1/.../GFX0@0 = PciRoot(0x0)/Pci(0x1,0x0)/Pci(0x0,0x0)/Pci(0x0,0x0)/Pci(0x0,0x0)
   ```

   The part after `=` is the path. Yours will differ.
3. **Add the property** under `DeviceProperties > Add > <your path>`: key `CFG_HIDE_HPD`, type **Data**, value
   `0100000000000000` (8 bytes). The fragment in
   [`examples/DeviceProperties-snippet.plist`](../examples/DeviceProperties-snippet.plist) shows the exact shape. If your
   config already has an entry for that path, add the key to it instead of making a second entry.
4. **Reboot** from that EFI.
5. **Check it was applied:**

   ```bash
   ioreg -c IOPCIDevice -l -w0 | grep CFG_HIDE_HPD
   # "CFG_HIDE_HPD" = <0100000000000000>
   ```

   If nothing prints, the property did not reach the GPU: see [troubleshooting.md](troubleshooting.md).
6. **Measure** with [`tools/measure-flicker.sh`](../tools/measure-flicker.sh), as described in
   [measuring.md](measuring.md).

## What it changes

The driver reads a family of `CFG_*` flags from the GPU's registry entry when it starts. Most default to on; `CFG_HIDE_HPD`
defaults to **off**. Any non-zero value turns it on, and because OpenCore's `DeviceProperties` writes onto that same
registry entry, injecting the property is enough.

With the flag on, the driver's function that forwards link-change events to the graphics policy driver (and from there
to macOS) writes a debug line and returns, instead of forwarding. With it off, it forwards them. So the fix does not make
the link more stable: it stops the system from reacting to the link blinking.

How this was read from the driver, step by step, is in [reverse-engineering.md](reverse-engineering.md), and you can
repeat it.

## Evidence

Counts of flicker events (`drops`, see [measuring.md](measuring.md)) from [`tools/measure-flicker.sh`](../tools/measure-flicker.sh)-style
runs of 3 to 4 loops each, on one machine:

| Setup | Without the fix | With the fix |
|-------|-----------------|--------------|
| Monitor at its native resolution | 0, 2, 2, 2, 3, 1 (six runs) | 0 and 0 (two runs, the second of a single loop) |
| Same monitor in a 6400x2700 HiDPI mode | 3 and 10 (two runs) | 0 and 0 (two runs) |

The "without" runs include other settings that were tried and had no measurable effect (see
[what-did-not-work.md](what-did-not-work.md)). The runs are few, and the loop count was 3 in some runs and 4 in others, so
treat this as a strong hint and not as a benchmark. The reporter also saw the flicker stop by eye.

## Side effects and limits

- **Monitor hot-plug may not be noticed while macOS runs.** Plugging a monitor in, unplugging it, or power-cycling it can
  go unnoticed until you reboot or sleep and wake the machine. This was **not tested**; it follows from what the flag
  does. If it bothers you, remove the property.
- **One machine.** Tested on a RX 6600 XT (Navi 23), macOS 26.2, OpenCore 1.0.6, WhateverGreen 1.7.1, MacPro7,1 SMBIOS.
  Other GPUs, macOS versions and display setups are unverified: please send a
  [test report](https://github.com/LuisPeixoto/hackintosh-dual-display-flicker-fix/issues/new?template=test_report.yml).
- **The cause is an inference from the code.** The runtime evidence is the before and after measurement. Nothing here
  traced the driver while it ran, so it is not proven that this notification is the trigger on every machine.
- **Apple can change the driver in any macOS update.** If a flag stops having an effect, the offsets and names in
  [reverse-engineering.md](reverse-engineering.md) will have moved.
- **Intel and AMD only as tested.** The tools read x86_64 collections.
