import Foundation
import CoreGraphics
// holdkeys <seconds>: hold Control+Option (OpenClicky push-to-talk), then release.
let secs = Double(CommandLine.arguments.dropFirst().first ?? "3") ?? 3
let src = CGEventSource(stateID: .hidSystemState)
func post(_ key: CGKeyCode, down: Bool, flags: CGEventFlags) {
    let e = CGEvent(keyboardEventSource: src, virtualKey: key, keyDown: down)!
    e.type = .flagsChanged
    e.flags = flags
    e.post(tap: .cghidEventTap)
}
post(59, down: true, flags: [.maskControl])
usleep(60_000)
post(58, down: true, flags: [.maskControl, .maskAlternate])
Thread.sleep(forTimeInterval: secs)
post(58, down: false, flags: [.maskControl])
usleep(60_000)
post(59, down: false, flags: [])
print("held ctrl+option for \(secs)s")
