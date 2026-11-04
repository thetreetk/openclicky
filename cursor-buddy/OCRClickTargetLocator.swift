import AppKit
import Foundation
import Vision

/// XAT: finds a click target by READING the screen's text instead of asking a vision model for coordinates.
/// For named things (file names, button labels, links) the macOS text recogniser gives exact boxes, so a click
/// on "notes April" lands on the `notes_april.txt` row instead of a neighbouring one. Returns nil when no single
/// text line contains every content word of the phrase, or when two lines match equally (ambiguous); the caller
/// then falls back to the vision model.
enum OCRClickTargetLocator {
    struct Match {
        /// Centre of the matching text line in screenshot pixels (top-left origin), the space `globalPoint(fromScreenshotPoint:in:)` expects.
        let point: CGPoint
        let text: String
        let candidateCount: Int
    }

    private static let stopWords: Set<String> = [
        "the", "a", "an", "on", "to", "of", "that", "this", "it", "please", "button", "buttons", "link", "links", "icon", "tab",
        "menu", "field", "file", "files", "document", "folder", "item", "option", "called", "named", "one", "my"
    ]
    private static let extensionTokens: Set<String> = ["txt", "pdf", "png", "jpg", "jpeg", "doc", "docx", "xls", "xlsx", "csv", "md", "key", "pages", "numbers", "zip", "mp3", "mov", "mp4", "heic", "gif"]
    private static let numberWords: [String: String] = [
        "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10"
    ]

    /// Lower-case alphanumeric tokens; "version two" / "version 2" become "v2"; number words become digits.
    static func tokens(_ text: String) -> [String] {
        var normalized = text.lowercased()
        normalized = normalized.replacingOccurrences(of: #"\bversion\s+(\w+)"#, with: "v$1", options: .regularExpression)
        var result: [String] = []
        for raw in normalized.split(whereSeparator: { !$0.isLetter && !$0.isNumber }) {
            var token = String(raw)
            if token.hasPrefix("v"), let mapped = numberWords[String(token.dropFirst())] { token = "v" + mapped }
            result.append(numberWords[token] ?? token)
        }
        return result
    }

    enum Resolution {
        case none
        case unique(Match)
        /// Several lines match equally well (e.g. two identical "Add to cart" buttons), in reading order (top to bottom, then left to right).
        case ambiguous([Match])
    }

    static func locate(phrase: String, capture: CompanionScreenCapture) -> Match? {
        if case .unique(let match) = resolve(phrase: phrase, capture: capture) { return match }
        return nil
    }

    static func resolve(phrase: String, capture: CompanionScreenCapture) -> Resolution {
        let wanted = tokens(phrase).filter { !stopWords.contains($0) }
        guard !wanted.isEmpty,
              let image = NSImage(data: capture.imageData)?.cgImage(forProposedRect: nil, context: nil, hints: nil),
              capture.screenshotWidthInPixels > 0, capture.screenshotHeightInPixels > 0 else { return .none }

        let request = VNRecognizeTextRequest()
        request.recognitionLevel = .accurate
        request.usesLanguageCorrection = false
        guard (try? VNImageRequestHandler(cgImage: image, options: [:]).perform([request])) != nil,
              let observations = request.results else { return .none }

        let scaleX = CGFloat(capture.screenshotWidthInPixels) / CGFloat(image.width)
        let scaleY = CGFloat(capture.screenshotHeightInPixels) / CGFloat(image.height)

        var scored: [(score: Double, match: Match)] = []
        for observation in observations {
            guard let candidate = observation.topCandidates(1).first else { continue }
            let have = tokens(candidate.string)
            let haveSet = Set(have)
            guard wanted.allSatisfy({ haveSet.contains($0) }) else { continue }
            // Prefer the line with the fewest extra words, so "report final" picks report_final.txt over report_final_v2.txt.
            let extras = have.filter { !wanted.contains($0) && !extensionTokens.contains($0) && !stopWords.contains($0) }.count
            let box = observation.boundingBox
            let point = CGPoint(
                x: box.midX * CGFloat(image.width) * scaleX,
                y: (1 - box.midY) * CGFloat(image.height) * scaleY
            )
            scored.append((1.0 / Double(1 + extras), Match(point: point, text: candidate.string, candidateCount: 1)))
        }
        guard let topScore = scored.map({ $0.score }).max() else { return .none }
        var tied = scored.filter { abs($0.score - topScore) <= 0.0001 }.map { $0.match }
        if tied.count == 1 { return .unique(tied[0]) }
        // Reading order: rows first (points within 12 px count as one row), then left to right.
        tied.sort { abs($0.point.y - $1.point.y) > 12 ? $0.point.y < $1.point.y : $0.point.x < $1.point.x }
        return .ambiguous(tied)
    }
}
