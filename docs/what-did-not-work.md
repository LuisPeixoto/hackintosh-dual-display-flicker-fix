# What did not work

Dead ends are worth writing down: each one cost a reboot, and somebody else will try the same things first. Every item
below was measured with [`tools/measure-flicker.sh`](../tools/measure-flicker.sh) or checked in `ioreg`, on the same
machine as [how-it-works.md](how-it-works.md). "No effect" means the flicker count did not change.

## GPU power management

The flicker looks like a display underrun during a clock change, so the first theory was power states.

| Attempt | What happened |
|---------|---------------|
| `PP_GfxOffControl = 0` and `SMU_DisallowedFeatures` in `DeviceProperties` | **Never took effect.** The driver's own settings are merged onto the GPU's registry entry after OpenCore injects yours, so `ioreg` still showed the driver's values. Properties the driver does not set itself (like `CFG_HIDE_HPD`) are not overwritten. |
| Editing the SoftPowerPlayTable (`PP_PhmSoftPowerPlayTable`), clearing the deep-sleep and GFXOFF bits of `FeaturesToRun` | **Took effect** (the GPU stayed at its maximum clock, 2742 MHz, even when idle) and **the flicker stayed**. So power states are not the cause. |

## Audio of the GPU

Every flicker was followed by the HDMI/DisplayPort audio engine (`AppleGFXHDA`) stopping and starting, which looked like
a cause.

| Attempt | What happened |
|---------|---------------|
| OpenCore `Kernel > Block` of `com.apple.driver.AppleGFXHDA`, strategy `Exclude` | **The driver stayed loaded.** It lives in the system kernel collection, and `Exclude` only acts on the boot collection. |
| `kmutil unload -b com.apple.driver.AppleGFXHDA` | Refused: `unsupported function`. |
| Reading the log order | In the flickers examined, the first event was an `IOGraphicsFamily` synchronization point, and the audio engine stopped about 40 ms **after** it. The audio events looked like a consequence of the display going away, not the cause. |

## Display settings in the driver

The driver reads a set of `Dal*` settings, among them ones about vblank alignment between displays, stutter and DRAM
clock changes.

| Attempt | What happened |
|---------|---------------|
| `DalDisableVblankAlignment`, `DalDisableStutter`, `DalDisableIdlePowerOptimizations`, `DalDisableVActiveDramChange`, all set to 1 | Applied (they show up in `ioreg` as 4-byte data) with **no measurable effect**. It is not known whether the driver parses them from data that is not a number. |

## Display modes and cables

| Attempt | What happened |
|---------|---------------|
| Lowering the refresh rate or changing it (60, 120, 144 Hz) on the DisplayPort monitor | No effect (2, 2, 3 and 1 events in four runs). |
| Lowering the pixel clock of the monitor on the adapter (1920x1080 at 60 Hz, 148.5 MHz, under the 165 MHz limit of simple adapters) | The flicker still happened. It is not an adapter bandwidth limit. |
| Different DP to HDMI adapters, other ports on the GPU, 8-bit color, 50 Hz | Reported as tried without effect by the reporter. **Not measured here.** |
| A large HiDPI framebuffer (6400x2700 on a 2560x1080 panel) | Not a fix, but it **made it worse** (3 and 10 events per run, against 0 to 3 at native resolution). |

## Lessons

- **A correlation in the log is not a cause.** The audio theory looked solid until the order of the events was checked.
- **Check that a property reached the driver** (`ioreg`) before judging whether it works.
- **Measure, then change one thing, then measure again**, with several runs: single runs of this test vary a lot.
