import SwiftUI
import InputMethodKit

class CandidateWindow: NSWindow, NSWindowDelegate {
    let hostingView = NSHostingView(rootView: CandidatesView(candidates: [], currentComposition: ""))
    var inputController: InputController?

    func windowDidMove(_ notification: Notification) {
        DispatchQueue.main.async {
            self.limitFrameInScreen()
        }
    }

    func windowDidResize(_ notification: Notification) {
        limitFrameInScreen()
    }

    func setCandidates(
        _ candidates: [Candidate],
        originalString: String,
        topLeft: NSPoint
    ) {
        hostingView.rootView.candidates = candidates
        self.setFrameTopLeftPoint(topLeft)
        self.orderFront(nil)
    }

    func bindEvents() {
        let events: [(name: Notification.Name, callback: (_ notification: Notification) -> Void)] = [
            (CandidatesView.candidateSelected, { notification in
                if let candidate = notification.userInfo?["candidate"] as? Candidate {
                    self.inputController?.insertCandidate(candidate)
                }
            }),
        ]
        events.forEach { (observer) in NotificationCenter.default.addObserver(
          forName: observer.name, object: nil, queue: nil, using: observer.callback
        )}
    }

    override init(
        contentRect: NSRect,
        styleMask style: NSWindow.StyleMask,
        backing backingStoreType: NSWindow.BackingStoreType,
        defer flag: Bool
    ) {
        super.init(contentRect: contentRect, styleMask: style, backing: backingStoreType, defer: flag)

        level = NSWindow.Level(rawValue: NSWindow.Level.RawValue(CGShieldingWindowLevel()))
        styleMask = .init(arrayLiteral: .fullSizeContentView, .borderless)
        isReleasedWhenClosed = false
        backgroundColor = NSColor.clear
        delegate = self
        setSizePolicy()
        bindEvents()
    }

    private func limitFrameInScreen() {
       let origin = self.transformTopLeft(originalTopLeft: NSPoint(x: self.frame.minX, y: self.frame.maxY))
       self.setFrameTopLeftPoint(origin)
    }

    private func setSizePolicy() {
        hostingView.translatesAutoresizingMaskIntoConstraints = false
        guard self.contentView != nil else {
            return
        }
        self.contentView?.addSubview(hostingView)
        self.contentView?.leftAnchor.constraint(equalTo: hostingView.leftAnchor).isActive = true
        self.contentView?.rightAnchor.constraint(equalTo: hostingView.rightAnchor).isActive = true
        self.contentView?.topAnchor.constraint(equalTo: hostingView.topAnchor).isActive = true
        self.contentView?.bottomAnchor.constraint(equalTo: hostingView.bottomAnchor).isActive = true
    }
    
    private func getScreenFromPoint(_ point: NSPoint) -> NSScreen? {
        for screen in NSScreen.screens {
            if screen.frame.contains(point) {
                return screen
            }
        }
        return NSScreen.main
    }

    private func transformTopLeft(originalTopLeft: NSPoint) -> NSPoint {
        let screenPadding: CGFloat = 6

        var left = originalTopLeft.x
        var top = originalTopLeft.y
        if let curScreen = getScreenFromPoint(originalTopLeft) {
            let screen = curScreen.frame

            if originalTopLeft.x + frame.width > screen.maxX - screenPadding {
                left = screen.maxX - frame.width - screenPadding
            }
            if originalTopLeft.y - frame.height < screen.minY + screenPadding {
                top = screen.minY + frame.height + screenPadding
            }
        }
        return NSPoint(x: left, y: top)
    }

    static let shared = CandidateWindow()
}
