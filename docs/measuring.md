# Measuring the flicker

Flicker is easy to miss by eye and easy to imagine, so measure it. This guide shows how to get a number you can compare
before and after the fix, and the one thing to know about reading the log on macOS.

## What the flicker looks like in the log

Every flicker has the same shape in the system log:

1. The graphics policy driver logs a display falling to a `1 x 1` mode at `0 Hz`, which means its link went away:

   ```text
   kernel (AppleGraphicsDevicePolicy) ... kAGDCRegisterLinkModesetCallback-ext: FB:1 -> 1 x 1, ext_blanking=0, 0 Hz
   ```

2. A moment later it comes back, and **WindowServer reconfigures every display**:

   ```text
   WindowServer ... [com.apple.CoreDisplay:default] [ERROR] - Reconfiguration started
   ```

The reconfiguration is what you see on screen. It affects all displays even when only one of them lost its link, which is
why both monitors blink together.

Two useful companions in the same log, which show up around the same moments on affected machines:

```text
(AMDRadeonX6000Framebuffer) [DAL] transferI2C() !!! Failed I2C transfer for link:2.
(AMDRadeonX6000Framebuffer) [DAL] validateDetailedTiming() !!! Failed to find sink 2.0.
```

## The script

[`tools/measure-flicker.sh`](../tools/measure-flicker.sh) reproduces the trigger and counts the events:

```bash
tools/measure-flicker.sh        # 4 loops, about two minutes
tools/measure-flicker.sh 8      # more loops, less noise
```

Each loop opens and quits six stock apps (Calculator, TextEdit, Notes, System Settings, Safari, Activity Monitor), which
is enough activity to trigger the flicker on affected machines. Apps that are already running are skipped, so no unsaved
work is ever closed. It prints one line:

```text
loops=4 drops=3 reconfigs=3
```

| Field | Meaning |
|-------|---------|
| `drops` | Bursts of a display falling to `1 x 1`, one count per second in which it happened |
| `reconfigs` | Times WindowServer reconfigured the displays: the visible flicker |

## How to compare fairly

- **Run it several times**, with the same display modes, and report all the numbers. The count varies between runs: on the
  machine this was developed on, the same setup gave anything from 0 to 3 events per four loops before the fix.
- **Change one thing at a time.** Reboot between the runs with and without the fix, and keep the display modes the same.
- **Leave the machine alone while it runs.** Moving windows around adds events that are not the problem.
- A HiDPI mode that is much larger than the panel (for example a 6400x2700 framebuffer on a 2560x1080 panel) made the
  flicker worse on the development machine. It is worth testing both with and without.

## Reading the log yourself

On macOS the shell may shadow `log` with a builtin (zsh does). Use the full path:

```bash
/usr/bin/log show --last 10m --style compact --predicate 'process == "kernel"' | grep -E 'FB:[0-9]+ -> 1 x 1'
/usr/bin/log show --last 10m --style compact --predicate 'process == "WindowServer"' | grep 'Reconfiguration started'
```

If a command prints nothing even though the system log has plenty in it, this shadowing is the first thing to check.

## Reporting your numbers

Please send them with the [test report form](https://github.com/LuisPeixoto/hackintosh-dual-display-flicker-fix/issues/new?template=test_report.yml):
the output of the script without the fix, the output with it, and your GPU, macOS version and display setup.
