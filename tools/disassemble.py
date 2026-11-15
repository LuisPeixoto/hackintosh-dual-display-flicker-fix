#!/usr/bin/env python3
"""Read a carved kext: list functions, search strings, find who uses a string, disassemble a function.

Works on the folder written by tools/carve-kext-text.py (text.macho and symbols.nm). Needs Xcode or the Command Line
Tools for `llvm-objdump`. The output is Apple code: read it, learn from it, do not commit it.

  tools/disassemble.py DIR functions Hotplug          functions whose mangled name contains "Hotplug"
  tools/disassemble.py DIR strings '^CFG_'            C strings matching a regex, with their addresses
  tools/disassemble.py DIR refs 0xc14d1b8             functions that load the address of that string
  tools/disassemble.py DIR dis notifyLinkChange       disassemble the first function whose name contains this

Call targets in the disassembly are replaced by symbol names where one exists.
"""
import argparse
import bisect
import re
import struct
import subprocess
import sys
from pathlib import Path


class Kext:
    def __init__(self, folder: Path):
        self.macho = folder / "text.macho"
        blob = self.macho.read_bytes()
        # The carved file is laid out by carve-kext-text.py: one segment, its data starting at 0x1000.
        self.base = struct.unpack_from("<Q", blob, 32 + 24)[0]
        self.data = blob[0x1000:]
        self.symbols = []
        for line in (folder / "symbols.nm").read_text().splitlines():
            parts = line.split()
            if len(parts) == 3 and parts[1] in ("T", "t") and re.fullmatch(r"[0-9a-f]{16}", parts[0]):
                self.symbols.append((int(parts[0], 16), parts[2]))
        self.symbols.sort()
        self.addresses = [address for address, _ in self.symbols]

    def name_at(self, address: int):
        index = bisect.bisect_right(self.addresses, address) - 1
        if index < 0:
            return None
        start, name = self.symbols[index]
        return name if address == start else f"{name}+{address - start:#x}"

    def function_end(self, start: int) -> int:
        index = self.addresses.index(start)
        return self.addresses[index + 1] if index + 1 < len(self.addresses) else start + 0x200

    def cstrings(self, pattern: re.Pattern):
        for match in re.finditer(rb"[\x20-\x7e]{4,300}(?=\x00)", self.data):
            text = match.group().decode()
            if pattern.search(text):
                yield self.base + match.start(), text


def disassemble(kext: Kext, start: int, end: int) -> None:
    out = subprocess.run(["xcrun", "llvm-objdump", "-d", "--no-show-raw-insn", f"--start-address={start:#x}",
                          f"--stop-address={end:#x}", str(kext.macho)], capture_output=True, text=True, check=True).stdout

    def annotate(match: re.Match) -> str:
        name = kext.name_at(int(match.group(0), 16))
        return f"{match.group(0)} <{name}>" if name else match.group(0)

    for line in out.splitlines():
        found = re.match(r"\s*([0-9a-f]+):\s+(.*)", line)
        if found:
            print(f"{found.group(1)}: {re.sub(r'0x[0-9a-f]{7,}', annotate, found.group(2))}")


def references(kext: Kext, target: int):
    """Find `lea reg, [rip+disp]` instructions that load `target`, and yield the function each one is in."""
    data = kext.data
    for i in range(len(data) - 7):
        if data[i] in (0x48, 0x4C) and data[i + 1] == 0x8D and (data[i + 2] & 0xC7) == 0x05:
            disp = struct.unpack_from("<i", data, i + 3)[0]
            if kext.base + i + 7 + disp == target:
                address = kext.base + i
                yield address, kext.name_at(address)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("folder", type=Path, help="folder written by carve-kext-text.py")
    parser.add_argument("command", choices=["functions", "strings", "refs", "dis"])
    parser.add_argument("argument", help="substring, regex, address or function name, depending on the command")
    args = parser.parse_args()
    kext = Kext(args.folder)

    if args.command == "functions":
        for address, name in kext.symbols:
            if args.argument in name:
                print(f"{address:#x} {name}")
    elif args.command == "strings":
        for address, text in kext.cstrings(re.compile(args.argument)):
            print(f"{address:#x} {text}")
    elif args.command == "refs":
        for address, name in references(kext, int(args.argument, 16)):
            print(f"{address:#x} in {name}")
    else:
        matches = [(a, n) for a, n in kext.symbols if args.argument in n]
        if not matches:
            sys.exit("no function with that name")
        address, name = matches[0]
        end = kext.function_end(address)
        print(f"=== {name} [{address:#x}-{end:#x}] {end - address} bytes")
        disassemble(kext, address, end)


if __name__ == "__main__":
    main()
