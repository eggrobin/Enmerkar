import Foundation

let subscriptZero: Unicode.Scalar = "₀"
let zero: Unicode.Scalar = "0"
let vowels = CharacterSet(charactersIn: "aeui")
let alphabet = CharacterSet(charactersIn: "abdegŋḫijklmnpqrsṣšśtṭuwzʾ")
let alphabeticalOrder = Dictionary<Unicode.Scalar, Int>.init(
    uniqueKeysWithValues:
        "abdegŋḫijklmnpqrsṣšśtṭuwzʾ".unicodeScalars.enumerated().map(
            { i, c in (c, i) }))
