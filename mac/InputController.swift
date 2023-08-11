//import Carbon.HIToolbox
import Cocoa
import InputMethodKit

@objc(InputController)
class InputController: IMKInputController {
    let pageSize = 10
    var currentComposition: String = ""
    var currentCandidates: ArraySlice<Candidate> = []
    var selectedIndex: Int? = nil
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
        // TODO(egg): Ignore ESC, etc.
        let flags = NSEvent.ModifierFlags(rawValue: UInt(rawFlags))
        NSLog(string)
        guard let client = sender as? IMKTextInput else {
            return false
        }

        let increment = { () -> Int? in
            if selectedIndex == nil {
                return nil
            }
            switch keyCode {
            case kVK_UpArrow:return -1
            case kVK_DownArrow:return +1
            case kVK_PageUp:return -self.pageSize
            case kVK_PageDown:return +self.pageSize
            default:return nil
            }
        }()
        if let Δ = increment {
            selectedIndex! += Δ;
            selectedIndex = min(max(selectedIndex!, currentCandidates.indices.min()!), currentCandidates.indices.max()!)
            let pageStart = (selectedIndex! - currentCandidates.startIndex) / pageSize * pageSize + currentCandidates.startIndex;
            CandidateWindow.shared.setCandidates(
                [Candidate](currentCandidates.suffix(from: pageStart).prefix(10)),
                selectedIndex: selectedIndex! - pageStart,
                currentComposition: currentComposition,
                topLeft: getOriginPoint())
            return true
        }
        if keyCode == kVK_Space || keyCode == kVK_Return {
            if currentComposition.isEmpty {
                return false
            }
            if !currentCandidates.isEmpty {
                let text = currentCandidates[selectedIndex!].text
                let marked = client.markedRange()
                client.insertText(text, replacementRange: marked)
                // Wrong in the terminal...
                let emitted = NSRange.init(location: marked.location, length: text.utf16.count)
                if let s = client.attributedSubstring(from: emitted) {
                    NSLog(s.string)
                }
                NSLog(emitted.description)
                NSLog(client.uniqueClientIdentifierString())
                currentComposition = "";
                currentCandidates = []
                selectedIndex = nil
                CandidateWindow.shared.close()
            }
            return true;
        }
        if keyCode == kVK_Delete {
            if currentComposition.isEmpty {
                // TODO(egg): 𒋛𒀀 backspacing.
                return false
            }
            currentComposition = String(currentComposition.prefix(currentComposition.count - 1))
            client.setMarkedText(currentComposition, selectionRange: NSRange(location: NSNotFound, length: NSNotFound), replacementRange: client.markedRange())
            updateCandidateWindow()
            return true
        }
        if flags.contains(.capsLock) || flags.contains(.shift) ||
            flags.contains(.command) || flags.contains(.control) {
            return false
        }
        if currentComposition.isEmpty {
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
            selectedIndex = nil
            CandidateWindow.shared.close()
        } else {
            // TODO(egg): Binary search.
            var begin: Array<Candidate>.Index = signList.count
            var end: Array<Candidate>.Index = signList.count
            for i in signList.indices {
                if begin > i && signList[i].composition.starts(with: currentComposition) {
                    begin = i
                }
                if begin < i && !signList[i].composition.starts(with: currentComposition) {
                    end = i
                    break
                }
            }
            currentCandidates = signList[begin..<end]
            selectedIndex = currentCandidates.startIndex
            currentCandidates.sort(by: candidatesOrdered)
            CandidateWindow.shared.setCandidates(
                [Candidate](currentCandidates.prefix(pageSize)),
                selectedIndex: 0,
                currentComposition: currentComposition,
                topLeft: getOriginPoint())
        }
    }
    
    private func candidatesOrdered(_ left: Candidate, _ right: Candidate) -> Bool {
        let left = left.composition.starts(with: "x") ? listKey(left.composition) : valueKey(left.composition)
        let right = right.composition.starts(with: "x") ? listKey(right.composition) : valueKey(right.composition)
        if left.primary.lexicographicallyPrecedes(right.primary, by: {l,r in l.keys.lexicographicallyPrecedes(r.keys)}) {
            return true
        } else if right.primary.lexicographicallyPrecedes(left.primary, by: {l,r in l.keys.lexicographicallyPrecedes(r.keys)}) {
            return false
        } else if left.secondary.lexicographicallyPrecedes(right.secondary, by: {l,r in l.keys.lexicographicallyPrecedes(r.keys)}) {
            return true
        } else if right.secondary.lexicographicallyPrecedes(left.secondary, by: {l,r in l.keys.lexicographicallyPrecedes(r.keys)}) {
            return false
        } else {
            return left.variant < right.variant
        }
    }
    
    class WordCollationKey {
        var keys: [Int] = []
        
        init() {}
        
        init(_ k: [Int]) {
            keys = k
        }
    }
    
    struct CollationKeys {
        var primary: [WordCollationKey]
        var secondary: [WordCollationKey]
        var variant: Int
    }
    
    private func valueKey(_ s: String) -> CollationKeys {
        var key = CollationKeys(primary: [], secondary: [], variant: 0)
        enum InputCategory {
            case ValueNumeric
            case FractionSlash
            case ValueAlphabetic
            case Variant
        }
        var lastCategory: InputCategory?
        for c in s.unicodeScalars {
            if alphabet.contains(c) {
                if lastCategory != InputCategory.ValueAlphabetic {
                    key.secondary.append(WordCollationKey())
                }
                let lastWord =
                    key.secondary[key.secondary.indices.last!]
                lastWord.keys.append(alphabeticalOrder[c]!)
                lastCategory = InputCategory.ValueAlphabetic
            } else if CharacterSet.decimalDigits.contains(c) {
                if lastCategory == InputCategory.Variant {
                    key.variant *= 10
                    key.variant += Int(c.properties.numericValue!)
                } else {
                    if lastCategory == InputCategory.ValueNumeric {
                        let lastWord =
                            key.secondary[key.secondary.indices.last!]
                        lastWord.keys[lastWord.keys.indices.last!] *= 10
                    } else if lastCategory == InputCategory.FractionSlash {
                        let lastWord =
                            key.secondary[key.secondary.indices.last!]
                        lastWord.keys.append(0)
                    } else {
                        key.secondary.append(WordCollationKey([0]))
                    }
                    let lastWord =
                    key.secondary[key.secondary.indices.last!]
                    lastWord.keys[lastWord.keys.indices.last!] +=
                        Int(c.properties.numericValue!)
                    lastCategory = InputCategory.ValueNumeric
                }
            } else if c == "x" {
                key.secondary.append(WordCollationKey([Int.max]))
                lastCategory = InputCategory.ValueNumeric
            } else if c == "+" || c == "-" {
                if lastCategory != InputCategory.ValueNumeric {
                    key.secondary.append(WordCollationKey([-1]))
                    lastCategory = InputCategory.ValueNumeric
                }
                let lastWord =
                    key.secondary[key.secondary.indices.last!]
                lastWord.keys.append(c == "-" ? 0 : 1)
            } else if c == "/" {
                lastCategory = InputCategory.FractionSlash
            } else if c == "v" {
                lastCategory = InputCategory.Variant
            }
        }
        for word in key.secondary {
            var nextPrimaryWord : [Int] = []
            for c in word.keys {
                if c != Unicode.Scalar("ʾ").value {
                    nextPrimaryWord.append(c)
                }
            }
            key.primary.append(WordCollationKey(nextPrimaryWord))
        }
        return key
    }
    
    private func listKey(_ s: String) -> CollationKeys {
        var key = CollationKeys(primary: [], secondary: [], variant: 0)
        let nameEnd = s.unicodeScalars.firstIndex(where: {CharacterSet.decimalDigits.contains($0)})!
        let name = s[..<nameEnd]
        let numberEnd = (s[nameEnd...].unicodeScalars.firstIndex(where: {!CharacterSet.decimalDigits.contains($0)}) ?? s.endIndex)
        let number = s[nameEnd..<numberEnd]
        let tailEnd = (s[numberEnd...].unicodeScalars.firstIndex(where: {$0 == "v"}) ?? s.endIndex)
        let tail = s[numberEnd..<tailEnd]
        key.primary.append(WordCollationKey([Int(number)!]))
        key.primary.append(WordCollationKey(Array(tail.unicodeScalars.map({Int($0.value)}))))
        key.secondary = key.primary
        let variant = s[tailEnd...]
        if !variant.isEmpty {
            key.variant = Int(variant[variant.index(after: tailEnd)...])!
        }
        return key
    }
}
