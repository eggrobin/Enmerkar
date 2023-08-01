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
            // TODO(egg) fancy preview based on currentComposition.
            Text(candidate.text)
                .foregroundColor(textColor)
                .frame(minWidth: 90, alignment: .leading)
            Text(candidate.composition)
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
}

struct CandidatesView: View {
    static let candidateSelected = Notification.Name("CandidatesView.candidateSelected")

    var candidates: [Candidate]
    var currentComposition: String

    var _candidatesView: some View {
        ForEach(Array(candidates.enumerated()), id: \.offset) { (index, candidate) -> CandidateView in
            CandidateView(
                candidate: candidate,
                index: index,
                currentComposition: currentComposition,
                selected: index == 0
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
            Candidate(composition: "ṣa₃", text: "𒀭"),
            Candidate(composition: "ṣab", text: "𒂟"),
            Candidate(composition: "ṣaḫ", text: "𒉈"),
            Candidate(composition: "ṣaḫ₅", text: "𒆤"),
        ], currentComposition: "ṣa")
        CandidatesView(candidates: [
            Candidate(composition: "gag₅", text: "𒈙")
        ], currentComposition: "gag₅")
        CandidatesView(candidates: [
            Candidate(composition: "enku", text: "𒍠𒄩"),
            Candidate(composition: "enkuₓ",text: "𒄩𒍠"),
            Candidate(composition: "enkud", text: "𒍠𒄩"),
            Candidate(composition: "enkudₓ", text: "𒍠"),
            Candidate(composition: "enkum", text: "𒂗𒉽𒅊𒉣𒈨𒂬")
        ], currentComposition: "enku")
    }
}
