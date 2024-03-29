import Cocoa
import InputMethodKit

@objc(InputController)
class InputController: IMKInputController {
    let pageSize = 10
    var currentComposition: String = ""
    var currentCandidates: ArraySlice<Candidate> = []
    var selectedIndex: Int? = nil
    var signList: [Candidate] = []
    
    class EmittedSequence {
        var range: Range<Int>
        let text: String
        
        init(range: Range<Int>, text: String) {
            self.range = range
            self.text = text
        }
    }
    
    var emittedSequences: [EmittedSequence] = []
    
    func insertCandidate(offset: Int) {
        if let currentIndex = selectedIndex {
            let pageStart = (currentIndex - currentCandidates.startIndex) / pageSize * pageSize + currentCandidates.startIndex;
            selectedIndex = pageStart + offset
            insertSelectedCandidate(client: client())
        }
    }

    override func activateServer(_ sender: Any!) {
        emittedSequences = []
        guard let client = sender as? IMKTextInput else {
            return;
        }
        if let path = Bundle.main.path(forResource: "sign_list", ofType: "txt") {
            
            do {
                let file = try String(contentsOfFile: path)
                
                let lines = file.components(separatedBy: CharacterSet.newlines)
                signList.removeAll()
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
        let lastInputSource = TISCopyCurrentASCIICapableKeyboardInputSource().takeRetainedValue()
        let lastKeyboardLayout =
        Unmanaged<CFData>.fromOpaque(TISGetInputSourceProperty(lastInputSource, kTISPropertyUnicodeKeyLayoutData)).takeUnretainedValue()
        let getLayoutKey = {(vkey: Int) in
            var deadKeyState: UInt32 = 0
            var s: [UniChar] = Array(repeating: 0, count: 255)
            var actualLength: Int = 0
            UCKeyTranslate(unsafeBitCast(CFDataGetBytePtr(lastKeyboardLayout), to: UnsafePointer<UCKeyboardLayout>.self), UInt16(vkey), UInt16(kUCKeyActionDown), 0, UInt32(LMGetKbdType()), UInt32(kUCKeyTranslateNoDeadKeysMask), &deadKeyState, 255, &actualLength, &s)
            return CFStringCreateWithCharacters(kCFAllocatorDefault, s, actualLength) as String
        }
        let layoutMnemonic = [kVK_ANSI_Q,kVK_ANSI_W,kVK_ANSI_E,kVK_ANSI_R,kVK_ANSI_T,kVK_ANSI_Y].map(getLayoutKey).joined()
        if layoutMnemonic == "',.pyf" {
            client.overrideKeyboard(withKeyboardNamed: "com.mockingbirdnest.inputmethod.Enmerkar.keylayout.ʾṣṭpŋf")
        } else if layoutMnemonic == "qwerty" {
            client.overrideKeyboard(withKeyboardNamed: "com.mockingbirdnest.inputmethod.Enmerkar.keylayout.qwertŋ")
        } else if layoutMnemonic == "qwertz" {
            client.overrideKeyboard(withKeyboardNamed: "com.mockingbirdnest.inputmethod.Enmerkar.keylayout.qwertz")
        } else if layoutMnemonic == "azerty" {
            client.overrideKeyboard(withKeyboardNamed: "com.mockingbirdnest.inputmethod.Enmerkar.keylayout.azertŋ")
        } else {
            NSLog("Unknown layout " + layoutMnemonic + ", using qwertŋ")
            client.overrideKeyboard(withKeyboardNamed: "com.mockingbirdnest.inputmethod.Enmerkar.keylayout.qwertŋ")
        }
    }
    
    override func deactivateServer(_ sender: Any!) {
        CandidateWindow.shared.close()
    }
    
    func getOriginPoint() -> NSPoint {
        let xd: CGFloat = 0
        let yd: CGFloat = 4
        var rect = NSRect()
        client()?.attributes(forCharacterIndex: 0, lineHeightRectangle: &rect)
        return NSPoint(x: rect.minX + xd, y: rect.minY - yd)
    }
    
    private func insertSelectedCandidate(client: IMKTextInput) {
        if !currentCandidates.isEmpty {
            let text = currentCandidates[selectedIndex!].text
            let marked = client.markedRange()
            client.insertText(text, replacementRange: marked)
            for s in emittedSequences {
                if s.range.endIndex > marked.location {
                    s.range = s.range.startIndex..<(s.range.endIndex+text.utf16.count)
                }
                if s.range.startIndex >= marked.location {
                    s.range = (s.range.startIndex+text.utf16.count)..<s.range.endIndex
                }
            }
            if text.unicodeScalars.count > 1 {
                let emitted = NSRange.init(location: marked.location, length: text.utf16.count)
                if emittedSequences.count >= 128 {
                    emittedSequences.removeFirst()
                }
                emittedSequences.append(EmittedSequence(range:Range(emitted)!, text: text))
            }
            currentComposition = "";
            currentCandidates = []
            selectedIndex = nil
            CandidateWindow.shared.close()
        }
    }
    
    override func inputText(_ string: String!, key keyCode: Int, modifiers rawFlags: Int, client sender: Any!) -> Bool {
        let flags = NSEvent.ModifierFlags(rawValue: UInt(rawFlags))
        guard let client = sender as? IMKTextInput else {
            return false
        }

        let increment = { () -> Int? in
            if selectedIndex == nil {
                return nil
            }
            switch keyCode {
                case kVK_UpArrow: return -1
                case kVK_DownArrow: return +1
                case kVK_PageUp: return -self.pageSize
                case kVK_PageDown: return +self.pageSize
                default: return nil
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
        if keyCode == kVK_Space ||
            keyCode == kVK_Return ||
            keyCode == kVK_ANSI_KeypadEnter {
            if currentComposition.isEmpty {
                return false
            } else {
                insertSelectedCandidate(client: client)
                return true
            }
        }
        if keyCode == kVK_Delete {
            if currentComposition.isEmpty {
                // Custom backspacing is somewhat circuitous on mac.  Calling |insertText|
                // with an empty string seems to have no effect; |setMarkedText| with an
                // empty string works in many places, but not in web page text fields in
                // Chrome, nor in Safari & Firefox (either in web page text fields or in the
                // browser’s own UI).
                // Instead we replace the text to be deleted with a space, and return false
                // from this function so that normal backspacing happens, removing the
                // space.  We could do that as a fallback if the first attempt at
                // backspacing failed, but that does not work because |setMarkedText| with
                // an empty string garbles the location of the |selectedRange| on Firefox.
                // Backspacing seems to be by legacy grapheme cluster on mac by default, but
                // is overriden, e.g., in Chrome, to being by code point; but our space
                // forms its own grapheme cluster, so this does not matter.
                // Complicating matters further, in some situations (webpage text fields in
                // Safari, message field on Discord even in Chrome), attempting to replace
                // part of an extended grapheme cluster with a space keeps the EGC intact,
                // but still inserts the space, so that backspacing gets stuck at a combining
                // mark.  Thus, when trying to delete one code point from an EGC, we instead
                // replace the whole EGC a string made up of that EGC with its last code
                // point removed, followed by a space.
                var deletion: (NSRange, String)? = nil
                if client.selectedRange().length == 0 {
                    for (i, s) in emittedSequences.enumerated() {
                        if s.range.endIndex == client.selectedRange().location {
                            if let actualText = client.attributedSubstring(from: NSRange(s.range)) {
                                if actualText.string == s.text {
                                    // A 𒋛𒀀 should always consist of whole EGCs, so
                                    // straightforward replacement with a space should work here.
                                    deletion = (NSRange(s.range), " ")
                                    emittedSequences.remove(at: i)
                                    break
                                }
                            }
                        }
                    }
                    if deletion == nil && client.selectedRange().location > 0 {
                        // If we are not backspacing a 𒋛𒀀, backspace by code point.
                        let location = client.selectedRange().location
                        var candidateLength = 1
                        while let deletedText = client.attributedSubstring(from: NSRange(location: location - candidateLength, length: candidateLength)) {
                            if deletedText.string.count > 1 {
                                // The first element of |deletion| probably covers a whole EGC.
                                // This is not true, e.g., if we are at the end of an indic
                                // consonant conjunct, as shown below.
                                //    Consonant [Virama Consonant]
                                //    The bracketed part here is two EGCs, but the whole string is
                                //    a single EGC (post 15.1).
                                // However, this is a somewhat unlikely situation for a cuneiform
                                // IME, and I do not want to implement a GCB iterator here if I can
                                // avoid it.
                                break
                            }
                            deletion = (NSRange(location: location - deletedText.string.utf16.count,
                                                length: deletedText.string.utf16.count),
                                        String(deletedText.string.unicodeScalars.dropLast()) + " ")
                            candidateLength = deletedText.string.utf16.count + 1
                            if candidateLength > location {
                                // The first element of |deletion| reaches the beginning of the
                                // string, and thus covers a whole EGC.
                                break
                            }
                        }
                    }

                    if let (deletedRange, replacement) = deletion {
                        client.insertText(replacement, replacementRange: deletedRange)

                        for s in emittedSequences {
                            // TODO(egg): We could be smarter about the case where we deleted stuff within a 𒋛𒀀.
                            if s.range.startIndex >= deletedRange.location {
                                s.range = (s.range.startIndex-deletedRange.length)..<(s.range.endIndex-deletedRange.length)
                            }
                        }
                    }
                }
                return false
            }
            currentComposition = String(currentComposition.prefix(currentComposition.count - 1))
            client.setMarkedText(currentComposition, selectionRange: NSRange(location: 0, length: currentComposition.utf16.count), replacementRange: client.markedRange())
            updateCandidateWindow()
            return true
        }
        if flags.contains(.capsLock) || flags.contains(.shift) ||
            flags.contains(.command) || flags.contains(.control) {
            // TODO(egg): In the shifted or caps-locked case, update emittedSequences.
            return false
        }
        if string.unicodeScalars.contains(where:{ $0.properties.generalCategory == .control ||
            $0.properties.generalCategory == .privateUse
        }) {
            return false
        }
        if currentComposition.isEmpty {
            currentComposition = string;
            client.setMarkedText(currentComposition, selectionRange: NSRange(location: 0, length: currentComposition.utf16.count), replacementRange: NSRange(location: NSNotFound, length: NSNotFound))
        } else {
            currentComposition.append(string)
            client.setMarkedText(currentComposition, selectionRange: NSRange(location: 0, length: currentComposition.utf16.count), replacementRange: client.markedRange())
        }
        updateCandidateWindow()
        return true
    }
    
    private func updateCandidateWindow() {
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

