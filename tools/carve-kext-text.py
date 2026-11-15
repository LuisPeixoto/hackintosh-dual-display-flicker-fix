#!/usr/bin/env python3
"""Carve one kext's __TEXT out of a macOS kernel collection, so ordinary tools can read it.

On recent macOS the kext binaries are no longer separate files: they live inside the kernel collections under
/System/Library/KernelCollections. This script reads the collection (read only), finds the entry for a bundle
identifier, and writes two files into an output folder you choose:

  text.macho    a minimal Mach-O holding only the kext's __TEXT segment (code and C strings), mapped at the same
                address it has in the collection, so `llvm-objdump -d` works on it
  symbols.nm    the kext's symbols, from `llvm-nm` (needs Xcode or the Command Line Tools)

Both files are derived from Apple binaries: keep them on your machine and never commit them.

Only x86_64 collections are supported (Intel Hackintosh). Usage:

  tools/carve-kext-text.py --out .scratch/amd-fb
  tools/carve-kext-text.py --entry com.apple.kext.AMDRadeonX6000Framebuffer --out .scratch/amd-fb
"""
import argparse
import struct
import subprocess
import sys
from pathlib import Path

LC_SEGMENT_64 = 0x19
LC_FILESET_ENTRY = 0x80000035
MH_MAGIC_64 = 0xFEEDFACF
CPU_TYPE_X86_64 = 0x01000007

DEFAULT_KC = "/System/Library/KernelCollections/SystemKernelExtensions.kc"
DEFAULT_ENTRY = "com.apple.kext.AMDRadeonX6000Framebuffer"


def read_commands(blob: bytes, header_offset: int = 0):
    """Yield (command, offset, size) for each load command of the Mach-O header at header_offset."""
    magic, cpu, _sub, _ftype, ncmds, sizeofcmds = struct.unpack_from("<IiiIII", blob, header_offset)
    if magic != MH_MAGIC_64:
        sys.exit("not a 64-bit Mach-O at that offset")
    if cpu != CPU_TYPE_X86_64:
        sys.exit("only x86_64 kernel collections are supported (arm64e collections encode their pointers)")
    offset = header_offset + 32
    for _ in range(ncmds):
        cmd, size = struct.unpack_from("<II", blob, offset)
        yield cmd, offset, size
        offset += size


def find_entry(kc, entry: str) -> int:
    head = kc.read(32)
    sizeofcmds = struct.unpack_from("<I", head, 20)[0]
    kc.seek(0)
    blob = kc.read(32 + sizeofcmds)
    for cmd, offset, size in read_commands(blob):
        if cmd != LC_FILESET_ENTRY:
            continue
        _vmaddr, fileoff, entry_id_offset, _ = struct.unpack_from("<QQII", blob, offset + 8)
        name = blob[offset + entry_id_offset: offset + size].split(b"\0")[0].decode()
        if name == entry:
            return fileoff
    sys.exit(f"no entry named {entry} in the collection")


def text_segment(kc, header_offset: int):
    kc.seek(header_offset)
    head = kc.read(32)
    sizeofcmds = struct.unpack_from("<I", head, 20)[0]
    kc.seek(header_offset)
    blob = kc.read(32 + sizeofcmds)
    for cmd, offset, _size in read_commands(blob):
        if cmd != LC_SEGMENT_64:
            continue
        name = blob[offset + 8: offset + 24].split(b"\0")[0].decode()
        if name == "__TEXT":
            vmaddr, vmsize, fileoff, filesize = struct.unpack_from("<QQQQ", blob, offset + 24)
            return vmaddr, vmsize, fileoff, filesize
    sys.exit("the kext has no __TEXT segment")


def build_macho(vmaddr: int, data: bytes) -> bytes:
    """One segment, one section, code flags: enough for llvm-objdump to disassemble any address in it."""
    segment = struct.pack("<II16sQQQQiiII", LC_SEGMENT_64, 72 + 80, b"__TEXT", vmaddr, len(data), 0x1000, len(data),
                          7, 5, 1, 0)
    section = struct.pack("<16s16sQQIIIIIIII", b"__text", b"__TEXT", vmaddr, len(data), 0x1000, 4, 0, 0, 0x80000400,
                          0, 0, 0)
    header = struct.pack("<IiiIIIII", MH_MAGIC_64, CPU_TYPE_X86_64, 3, 2, 1, len(segment) + len(section), 0, 0)
    body = header + segment + section
    return body + b"\0" * (0x1000 - len(body)) + data


def dump_symbols(kc_path: str, entry: str) -> str:
    """The `llvm-nm` output of a fileset is one block per entry; keep only the requested one."""
    out = subprocess.run(["xcrun", "llvm-nm", kc_path], capture_output=True, text=True, check=True).stdout
    keep, lines = False, []
    for line in out.splitlines():
        if line.startswith("Symbols for "):
            keep = line.removeprefix("Symbols for ").rstrip(": ") == entry
            continue
        if keep:
            lines.append(line)
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--kc", default=DEFAULT_KC, help=f"kernel collection (default: {DEFAULT_KC})")
    parser.add_argument("--entry", default=DEFAULT_ENTRY, help=f"bundle identifier (default: {DEFAULT_ENTRY})")
    parser.add_argument("--out", required=True, help="folder to write text.macho and symbols.nm into")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    with open(args.kc, "rb") as kc:
        header_offset = find_entry(kc, args.entry)
        vmaddr, vmsize, fileoff, filesize = text_segment(kc, header_offset)
        kc.seek(fileoff)
        data = kc.read(filesize)
    (out / "text.macho").write_bytes(build_macho(vmaddr, data))
    symbols = dump_symbols(args.kc, args.entry)
    (out / "symbols.nm").write_text(symbols)
    count = sum(1 for line in symbols.splitlines() if line.strip())
    print(f"{args.entry}: __TEXT at {vmaddr:#x}, {filesize:#x} bytes, {count} symbols -> {out}")


if __name__ == "__main__":
    main()
