//import Carbon.HIToolbox
import Cocoa
import InputMethodKit

@objc(InputController)
class InputController: IMKInputController {
    var currentComposition: String = ""
    var currentCandidates: ArraySlice<Candidate> = []
    var signList: [Candidate] = []
    
    func insertCandidate(_: Candidate) {
        
    }

    override func activateServer(_ sender: Any!) {
        guard let client = sender as? IMKTextInput else {
            return;
        }
        NSLog("activateServer")
        if let path = Bundle.main.path(forResource: "sign_list", ofType: "txt") {
            NSLog(path)
            do {
                let file = try String(contentsOfFile: path)
                NSLog("Reading sign list (%d characters)...", signList.count)
                let lines = file.components(separatedBy: CharacterSet.newlines)
                signList.removeAll()
                NSLog("%d compositions...", lines.count)
                for line in lines {
                    if line.isEmpty {
                        continue
                    }
                    let parts = line.components(separatedBy: CharacterSet(charactersIn: "="))
                    let composition = parts[0].trimmingCharacters(in: CharacterSet(charactersIn: "\""))
                    let sign = parts[1].trimmingCharacters(in: CharacterSet(charactersIn: "\""))
                    signList.append(Candidate(composition:composition, text:sign))
                }
                signList.sort(by: {(l, r) in l.composition.lexicographicallyPrecedes(r.composition)})
            } catch {}
        }
        CandidateWindow.shared.inputController = self;
        //TISRegisterInputSource(NSURL(fileURLWithPath: Bundle.main.bundlePath))
        /*
        let inputSources = TISCreateInputSourceList(nil, true).takeRetainedValue() as! [TISInputSource]
        for inputSource in inputSources {
            let id = Unmanaged<NSString>
                .fromOpaque(TISGetInputSourceProperty(inputSource, kTISPropertyInputSourceID)).takeUnretainedValue() as String
            if (id.contains(/mock/)) {
                NSLog(id)
            }
        }*/
        // TODO(egg): Configurability.
        client.overrideKeyboard(withKeyboardNamed: "com.mockingbirdnest.inputmethod.Enmerkar.keylayout.ʾṣṭpŋf")
    }
    
    override func deactivateServer(_ sender: Any!) {
        CandidateWindow.shared.close()
    }
    
    override func candidateSelectionChanged(_ candidateString: NSAttributedString!) {
        
    }
    
    override func candidateSelected(_ candidateString: NSAttributedString!) {
        
    }
    
    func getOriginPoint() -> NSPoint {
        let xd: CGFloat = 0
        let yd: CGFloat = 4
        var rect = NSRect()
        client()?.attributes(forCharacterIndex: 0, lineHeightRectangle: &rect)
        return NSPoint(x: rect.minX + xd, y: rect.minY - yd)
    }
    
    override func inputText(_ string: String!, key keyCode: Int, modifiers rawFlags: Int, client sender: Any!) -> Bool {
        let flags = NSEvent.ModifierFlags(rawValue: UInt(rawFlags))
        NSLog(string)
        guard let client = sender as? IMKTextInput else {
            return false
        }
        if (keyCode == kVK_Space || keyCode == kVK_Return) {
            if currentComposition.isEmpty {
                return false
            }
            if !currentCandidates.isEmpty {
                // TODO(egg): index with the arrow keys.
                client.insertText(currentCandidates.first!.text, replacementRange: client.markedRange())
                currentComposition = "";
                CandidateWindow.shared.close()
            }
            return true;
        }
        if (keyCode == kVK_Delete) {
            if currentComposition.isEmpty {
                // TODO(egg): 𒋛𒀀 backspacing.
                return false
            }
            currentComposition = String(currentComposition.prefix(currentComposition.count - 1))
            client.setMarkedText(currentComposition, selectionRange: NSRange(location: NSNotFound, length: NSNotFound), replacementRange: client.markedRange())
            updateCandidateWindow()
            return true
        }
        if flags.contains(.capsLock) || flags.contains(.shift) {
            return false
        }
        if (currentComposition.isEmpty) {
            currentComposition = string;
            client.setMarkedText(currentComposition, selectionRange: NSRange(location: NSNotFound, length: NSNotFound), replacementRange: NSRange(location: NSNotFound, length: NSNotFound))
        } else {
            currentComposition.append(string)
            client.setMarkedText(currentComposition, selectionRange: NSRange(location: NSNotFound, length: NSNotFound), replacementRange: client.markedRange())
        }
        updateCandidateWindow()
        return true
    }
    
    private func updateCandidateWindow() {
        NSLog(currentComposition)
        if currentComposition.isEmpty {
            currentCandidates = []
            CandidateWindow.shared.close()
        } else {
            var begin: Array<Candidate>.Index?
            var end: Array<Candidate>.Index?
            for i in signList.indices {
                if begin == nil && signList[i].composition.starts(with: currentComposition) {
                    begin = i
                }
                if begin != nil && !signList[i].composition.starts(with: currentComposition) {
                    end = i
                }
            }
            if begin != nil && end == nil {
                end = signList.count
            }
            if begin == nil || end == nil {
                NSLog("no match")
                CandidateWindow.shared.setCandidates(
                    [],
                    currentComposition: currentComposition,
                    topLeft: getOriginPoint())
            } else {
                NSLog("%d", begin!)
                NSLog("%d", end!)
                currentCandidates = signList[begin!...end!]
                // TODO(egg): Sorting, paging.
                CandidateWindow.shared.setCandidates(
                    [Candidate](currentCandidates.prefix(10)),
                    currentComposition: currentComposition,
                    topLeft: getOriginPoint())
            }
        }
    }
}
