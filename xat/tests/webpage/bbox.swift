import Foundation
import CoreGraphics
import ImageIO
// bbox <image.png> name=RRGGBB ...  -> JSON {name:[x1,y1,x2,y2]} bounding boxes of pixels within +-14 of each colour
let args = Array(CommandLine.arguments.dropFirst())
guard let src = CGImageSourceCreateWithURL(URL(fileURLWithPath: args[0]) as CFURL, nil), let img = CGImageSourceCreateImageAtIndex(src, 0, nil) else { print("{}"); exit(1) }
let w = img.width, h = img.height
var data = [UInt8](repeating: 0, count: w * h * 4)
let ctx = CGContext(data: &data, width: w, height: h, bitsPerComponent: 8, bytesPerRow: w * 4, space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
ctx.draw(img, in: CGRect(x: 0, y: 0, width: w, height: h))
let tol = 14
var roi = [0, 0, w, h]
if let r = args.first(where: { $0.hasPrefix("roi=") }) { roi = r.dropFirst(4).split(separator: ",").map { Int($0)! } }
if args.count > 1 && args[1] == "px" { var i = 2; while i + 1 < args.count { let x = Int(args[i])!, y = Int(args[i+1])!; let k = (y * w + x) * 4; print("(\(x),\(y)) = \(String(format: "%02x%02x%02x", data[k], data[k+1], data[k+2]))"); i += 2 }; exit(0) }
var out: [String: [Int]] = [:]
for spec in args.dropFirst() where !spec.hasPrefix("roi=") {
    let p = spec.split(separator: "="); let name = String(p[0]); let hex = UInt32(p[1], radix: 16)!
    let r = Int((hex >> 16) & 255), g = Int((hex >> 8) & 255), b = Int(hex & 255)
    var x1 = w, y1 = h, x2 = -1, y2 = -1, n = 0
    for y in roi[1]..<min(roi[3], h) { for x in roi[0]..<min(roi[2], w) { let i = (y * w + x) * 4
        if abs(Int(data[i]) - r) <= tol && abs(Int(data[i+1]) - g) <= tol && abs(Int(data[i+2]) - b) <= tol { n += 1; if x < x1 { x1 = x }; if x > x2 { x2 = x }; if y < y1 { y1 = y }; if y > y2 { y2 = y } } } }
    if n > 200 { out[name] = [x1, y1, x2, y2] }
}
let d = try! JSONSerialization.data(withJSONObject: out); print(String(data: d, encoding: .utf8)!)
