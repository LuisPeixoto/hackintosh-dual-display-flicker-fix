# Reading the driver yourself

The fix came from reading Apple's AMD framebuffer driver, not from documentation. This guide shows how to repeat that on
your own machine, so you can check every claim in [how-it-works.md](how-it-works.md) instead of trusting it.

> The driver is Apple's code. Read it locally, and keep what the tools write out of any repository.

## What you need

- An **Intel Hackintosh** (the tools read x86_64 kernel collections).
- Xcode or the Command Line Tools, for `llvm-nm` and `llvm-objdump` (`xcode-select --install`).
- Python 3. Nothing else is installed.

## 1. Get the driver out of the kernel collection

On recent macOS the kext binaries are not files anymore: they live inside the kernel collections. The AMD framebuffer
driver is in `SystemKernelExtensions.kc`, not in the boot collection. That matters beyond this guide: OpenCore's
`Kernel > Block` with the `Exclude` strategy only acts on the boot collection, so it cannot remove a kext from the system
collection.

```bash
tools/carve-kext-text.py --out .scratch/amd-fb
# com.apple.kext.AMDRadeonX6000Framebuffer: __TEXT at 0xbf5d000, 0x28a000 bytes, 3314 symbols -> .scratch/amd-fb
```

The numbers differ between macOS versions. `.scratch/` is ignored by git on purpose.

Why not just open the kernel collection in a disassembler? The tool writes a small Mach-O with only the driver's `__TEXT`
(code and C strings), mapped at its original address, so any tool that reads Mach-O files can use it, and the symbol names
come along from the collection.

## 2. Find the settings the driver reads

The driver reads its configuration from properties on the GPU's registry entry. Search the C strings:

```bash
tools/disassemble.py .scratch/amd-fb strings '^CFG_'
tools/disassemble.py .scratch/amd-fb strings '^Dal[A-Z]'
```

You will find a family of `CFG_*` flags (`CFG_USE_AGDC`, `CFG_AGDC_PCON_MGMT`, `CFG_USE_PSR`, `CFG_NO_DSC`,
`CFG_RGB_ONLY`, and `CFG_HIDE_HPD` among them) and a set of `Dal*` display settings.

## 3. Find who reads a setting

Take the address printed next to the string and ask which function loads it:

```bash
tools/disassemble.py .scratch/amd-fb refs 0xc14d1b8
# 0xbf699c0 in __ZN33AMDRadeonX6000_AmdProjectFeatures22readRegistryPropertiesEv+0xb2
```

Disassemble that function:

```bash
tools/disassemble.py .scratch/amd-fb dis readRegistryProperties
```

What it shows, for each flag: the driver pre-loads an 8-byte buffer with the default (1 for most flags, **0 for
`CFG_HIDE_HPD`**), calls `getRegistryProperty` on the GPU's registry entry with the flag's name, and stores
`value != 0` as one bit in a feature word. Reading the property goes through `parseOSObjectValue`, which accepts binary
data and copies at most that many bytes into the buffer, so an 8-byte `Data` value of `01 00 00 00 00 00 00 00` sets the
flag.

## 4. Find what a flag does

The feature word is read through `supportsFeature`. Its switch maps each feature number to a bit:

```bash
tools/disassemble.py .scratch/amd-fb dis AmdProjectFeatures15supportsFeature
```

Feature 3 tests bit 3, which is the bit `readRegistryProperties` sets from `CFG_HIDE_HPD`. To see who asks for feature 3,
look for functions that load `3` into `esi` right before a call. `notifyLinkChange` is one:

```bash
tools/disassemble.py .scratch/amd-fb dis notifyLinkChange
```

It asks whether the feature is on. If it is, it writes a debug line (`[AGDC] ... DEBUG: Hotplug notification ...`) and
jumps to the end. If it is not, it goes on to a switch over the link-change event number. That is the evidence behind
"with `CFG_HIDE_HPD` on, the driver does not pass link-change notifications on". See the limits section of
[how-it-works.md](how-it-works.md) for what this does and does not prove.

## 5. Other things worth knowing about

```bash
tools/disassemble.py .scratch/amd-fb functions HotPlug
tools/disassemble.py .scratch/amd-fb dis handleHotPlug
```

`AmdInterruptManager::handleHotPlug` logs the hot-plug source and detection reason, then asks `isHotPlugDisabled` (one
bit of a flags byte) before doing any work. The driver's own `[IRQMGR]` log lines are filtered by a log mask, so they do
not show up in the system log by default.

## Limits of this method

- It is static reading. Nothing here runs or traces the driver, so conclusions about *behavior* are inferences from the
  code, and the only runtime evidence is the before and after measurement in [measuring.md](measuring.md).
- Offsets, addresses and function names belong to one macOS build. Expect them to move.
- Arm64 (Apple silicon) collections use pointer encodings that these tools do not decode.
