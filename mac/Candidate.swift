struct Candidate: Hashable {
    let composition: String
    let text: String

    init(composition: String, text: String) {
        self.composition = composition
        self.text = text
    }
}
