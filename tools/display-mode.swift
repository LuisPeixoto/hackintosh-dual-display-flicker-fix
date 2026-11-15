// List the display modes macOS offers for each connected display, and switch one of them.
//
//   swiftc -O tools/display-mode.swift -o display-mode
//   ./display-mode list
//   ./display-mode set <vendor-hex> <width> <height> <pixel-width> <hz>
//
// `list` shows each display's id, vendor (hex, as in the EDID) and current mode, then every usable mode.
// `set` switches the display with that vendor id to the matching mode. The change is PERMANENT, as if you had picked it
// in System Settings, so write down the current mode first and switch back when you are done testing.
//
// <width> and <height> are the points the desktop uses; <pixel-width> is the real framebuffer width, which is twice the
// width for a HiDPI mode. Example: a HiDPI mode of "3200x1350" has pixel width 6400.

import CoreGraphics
import Foundation

let args = CommandLine.arguments
guard args.count >= 2, args[1] == "list" || (args[1] == "set" && args.count == 7) else {
    FileHandle.standardError.write(Data("usage: display-mode list | set <vendor-hex> <width> <height> <pixel-width> <hz>\n".utf8))
    exit(2)
}

var ids = [CGDirectDisplayID](repeating: 0, count: 16)
var count: UInt32 = 0
CGGetOnlineDisplayList(UInt32(ids.count), &ids, &count)
let options = [kCGDisplayShowDuplicateLowResolutionModes as String: true] as CFDictionary

func usableModes(_ display: CGDirectDisplayID) -> [CGDisplayMode] {
    ((CGDisplayCopyAllDisplayModes(display, options) as? [CGDisplayMode]) ?? []).filter { $0.isUsableForDesktopGUI() }
}

if args[1] == "list" {
    for index in 0..<Int(count) {
        let display = ids[index]
        let current = CGDisplayCopyDisplayMode(display)
        print("display id=\(display) vendor=\(String(CGDisplayVendorNumber(display), radix: 16)) " +
              "current=\(current?.width ?? 0)x\(current?.height ?? 0) pixels=\(current?.pixelWidth ?? 0) " +
              "@\(Int(current?.refreshRate ?? 0))Hz")
        var seen = Set<String>()
        for mode in usableModes(display) {
            let line = "  \(mode.width)x\(mode.height) pixels=\(mode.pixelWidth) @\(Int(mode.refreshRate))Hz"
            if seen.insert(line).inserted { print(line) }
        }
    }
    exit(0)
}

guard let vendor = UInt32(args[2], radix: 16), let width = Int(args[3]), let height = Int(args[4]),
      let pixelWidth = Int(args[5]), let hertz = Double(args[6]) else {
    FileHandle.standardError.write(Data("set: vendor must be hex, the rest numbers\n".utf8))
    exit(2)
}

for index in 0..<Int(count) {
    let display = ids[index]
    guard CGDisplayVendorNumber(display) == vendor else { continue }
    guard let mode = usableModes(display).first(where: {
        $0.width == width && $0.height == height && $0.pixelWidth == pixelWidth && abs($0.refreshRate - hertz) < 0.5
    }) else {
        FileHandle.standardError.write(Data("no such mode on that display; run `list` to see the choices\n".utf8))
        exit(1)
    }
    var config: CGDisplayConfigRef?
    CGBeginDisplayConfiguration(&config)
    CGConfigureDisplayWithDisplayMode(config, display, mode, nil)
    let result = CGCompleteDisplayConfiguration(config, .permanently)
    print(result == .success ? "switched (permanent until you change it back)" : "failed with error \(result.rawValue)")
    exit(result == .success ? 0 : 1)
}
FileHandle.standardError.write(Data("no connected display has vendor \(args[2])\n".utf8))
exit(1)
