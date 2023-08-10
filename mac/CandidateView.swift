import SwiftUI

struct CandidateView: View {
    var candidate: Candidate
    var index: Int
    var currentComposition: String
    var selected: Bool = false

    var body: some View {
        let backgroundColor = selected
        ? Color.init(red: 0.65, green: 0.65, blue: 0)
        : Color.white;
        let textColor = selected
        ? Color.white
        : Color.black;

        return HStack(alignment: .center, spacing: 2) {
            Text(candidate.text)
                .foregroundColor(textColor)
                .frame(minWidth: 90, alignment: .leading)
            Text(prettyHint())
                .foregroundColor(textColor)
                .frame(minWidth: 0, alignment: .leading)
        }
        .frame(width: 300, alignment: .leading)
        .onTapGesture {
            NotificationCenter.default.post(
                name: CandidatesView.candidateSelected,
                object: nil,
                userInfo: [
                    "candidate": candidate,
                    "index": index
                ]
            )
        }.background(backgroundColor)
    }

    private func prettyHint() -> String {
        if candidate.composition.first == "x" {
            return prettyListHint()
        }
        var vowelCount = 0
        let enteredSize = currentComposition.unicodeScalars.count
        var subscriptEntered = true
        var homophoneIndex = 0
        for (offset: i, element: c) in candidate.composition.unicodeScalars.enumerated() {
            if c == "v" {
                break
            }
            if vowels.contains(c) {
                vowelCount += 1
            } else if CharacterSet.decimalDigits.contains(c) {
                if enteredSize <= i {
                    subscriptEntered = false
                }
                homophoneIndex *= 10
                homophoneIndex += Int(c.properties.numericValue!)
            }
        }
        var accent = ""
        if subscriptEntered && vowelCount == 1 {
            if homophoneIndex == 2 {
                accent = "\u{0301}"
            } else if homophoneIndex == 3 {
                accent = "\u{0300}"
            }
        }
        var result: String = ""
        var inParenthetical = false
        var afterLetters = false
        for (offset: i, element: c) in candidate.composition.unicodeScalars.enumerated() {
            if c == "v" {
                result.append(" (")
                inParenthetical = true
            }
            var tokenHint = ""
            if c == "v" {
                tokenHint.append("‸variant ")
            } else {
                tokenHint.append("‸")
            }
            if CharacterSet.decimalDigits.contains(c) || c == "x" {
                if !afterLetters || inParenthetical {
                    tokenHint.append(String(c))
                } else if accent.isEmpty {
                    if c == "x" {
                        tokenHint += "ₓ";
                    } else {
                        tokenHint += String(UnicodeScalar(subscriptZero.value + (c.value - zero.value))!)
                    }
                }
            } else if c != "v" {
                if alphabet.contains(c) {
                    afterLetters = true
                }
                if candidate.composition == "m" {
                  tokenHint += "ᵐ";
                } else if candidate.composition == "f" {
                  tokenHint += "ᶠ";
                } else if candidate.composition == "d" {
                  tokenHint += "ᵈ";
                } else if c == "+" {
                  tokenHint += "⁺";
                } else if c == "-" {
                  tokenHint += "⁻";
                } else {
                  tokenHint += String(c);
                }
                if !inParenthetical && !accent.isEmpty &&
                    vowels.contains(c) {
                  tokenHint += accent;
                }
            }
            if i == enteredSize {
                result.append(
                    tokenHint)
            } else {
                result += tokenHint.suffix(from: tokenHint.index(after: tokenHint.startIndex))
            }
        }
        if inParenthetical {
            result += ")"
        }
        if enteredSize == candidate.composition.unicodeScalars.count {
            result += "‸"
        }
        return result
    }
    
    let signLists = [
        ("abzl", "aBZL"),
        ("bau", "BAU"),
        ("elles", "ELLes"),
        ("ḫzl", "HZL"),
        ("kwu", "KWU"),
        ("lak", "LAK"),
        ("mea", "MÉA"),
        ("mzl", "MZL"),
        ("reš", "RÉC"),
        ("rsp", "RSP"),
        ("šl", "ŠL"),
        ("zatu", "ZATU"),
    ]
    
    private func prettyListHint() -> String {
        let currentComposition = currentComposition.suffix(from: currentComposition.index(after: currentComposition.startIndex))
        let candidateComposition = candidate.composition.suffix(from: candidate.composition.index(after: candidate.composition.startIndex))
        var prettyList : [UnicodeScalar] = []
        for (listComposition, listName) in signLists {
            if currentComposition.starts(with: listComposition) {
                prettyList = Array(listName.unicodeScalars)
            }
        }
        var result = ""
        var inParenthetical = false
        let enteredSize = currentComposition.unicodeScalars.count
        for (i, c) in candidateComposition.unicodeScalars.enumerated() {
            if c == "v" {
                result += " ("
                inParenthetical = true
            }
            
            var tokenHint = ""
            if c == "v" {
                tokenHint += "‸variant "
            } else {
                tokenHint += "‸"
                if i < prettyList.count {
                    tokenHint += String(prettyList[i])
                } else if c == "š" {
                    tokenHint += "c"
                } else {
                    tokenHint += String(c)
                }
            }
            if i == prettyList.count {
                result += " "
            }
            if enteredSize == i {
                result += tokenHint
            } else {
                result += tokenHint.suffix(from: tokenHint.index(after:tokenHint.startIndex))
            }
        }
        if inParenthetical {
            result += ")"
        }
        if enteredSize == candidateComposition.unicodeScalars.count {
            result += "‸"
        }
        return result
    }
}

struct CandidatesView: View {
    static let candidateSelected = Notification.Name("CandidatesView.candidateSelected")

    var candidates: [Candidate]
    var currentComposition: String
    var selectedIndex: Int

    var _candidatesView: some View {
        ForEach(Array(candidates.enumerated()), id: \.offset) { (index, candidate) -> CandidateView in
            CandidateView(
                candidate: candidate,
                index: index,
                currentComposition: currentComposition,
                selected: index == selectedIndex
            )
        }
    }

    var body: some View {
            VStack(alignment: .leading, spacing: CGFloat(6)) {
                _candidatesView
            }
            .fixedSize()
            .padding(.top, CGFloat(6))
            .padding(.bottom, CGFloat(6))
            .padding(.leading, CGFloat(10))
            .padding(.trailing, CGFloat(10))
            .fixedSize()
            .font(.system(size: CGFloat(20)))
            .background(Color.white)
            .cornerRadius(CGFloat(6), antialiased: true)
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        CandidatesView(candidates: [
            Candidate(composition: "ṣa", text: "𒍝"),
            Candidate(composition: "ṣa3", text: "𒀭"),
            Candidate(composition: "ṣab", text: "𒂟"),
            Candidate(composition: "ṣaḫ", text: "𒉈"),
            Candidate(composition: "ṣaḫ5", text: "𒆤"),
        ], currentComposition: "ṣa", selectedIndex: 2)
        CandidatesView(candidates: [
            Candidate(composition: "ṣa3", text: "𒀭"),
        ], currentComposition: "ṣa3", selectedIndex: 0)
        CandidatesView(candidates: [
            Candidate(composition: "/", text: "\u{200B}"),
            Candidate(composition: "/v1", text: "𒑰"),
        ], currentComposition: "/", selectedIndex: 0)
        CandidatesView(candidates: [
            Candidate(composition: "gag5", text: "𒈙")
        ], currentComposition: "gag5", selectedIndex: 0)
        CandidatesView(candidates: [
            Candidate(composition: "enku", text: "𒍠𒄩"),
            Candidate(composition: "enkux",text: "𒄩𒍠"),
            Candidate(composition: "enkud", text: "𒍠𒄩"),
            Candidate(composition: "enkudx", text: "𒍠"),
            Candidate(composition: "enkum", text: "𒂗𒉽𒅊𒉣𒈨𒂬")
        ], currentComposition: "enku", selectedIndex: 0)
    }
}
