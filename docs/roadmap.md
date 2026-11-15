# Roadmap

## Where the project stands

**v0.1.0:** the fix, the measurement script, the display-mode tool, the driver-reading tools and the guides. The fix was
validated on one machine. The most useful thing right now is evidence from others.

## Wanted

- **Test reports** from other GPUs (Navi 21, 22, 24 and any other card that uses the same driver), other macOS versions,
  other OpenCore and WhateverGreen versions, and other display setups, including setups where it did **not** work.
  Use the [test report form](https://github.com/LuisPeixoto/hackintosh-dual-display-flicker-fix/issues/new?template=test_report.yml).
- **Hot-plug behavior with the flag on:** does a monitor plugged in or power-cycled while macOS runs get detected after
  sleep? After a reboot only? This is not tested yet.

## Ideas

Not planned, listed so they are not forgotten:

- **Confirm the trigger at runtime.** Today the cause is read from the code. Tracing which notification is sent at each
  flicker would turn the inference into a fact.
- **A finer fix.** Hiding every link-change notification is a blunt tool. If the one that causes the flicker can be
  told apart, only that one could be dropped, and hot-plug would keep working.
- **Other flags.** The driver reads more `CFG_*` flags (for instance `CFG_AGDC_PCON_MGMT`, which concerns DP to HDMI
  converters) that have not been tried.
- **A Lilu plugin** that applies the setting without editing `DeviceProperties`, if a good reason appears.
- **Apple silicon** is out of scope: it does not use this driver.
