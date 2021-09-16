#include "𒄑𒂅𒌋/transcription.h"

#include <algorithm>
#include <array>
#include <map>
#include <optional>
#include <set>
#include <vector>

namespace 𒄑𒂅𒌋 {

constexpr wchar_t ʾaleph = L'ʾ';

struct Source {
  // Name with caret before the input character, e.g., "Borger ‸MesZL".
  std::wstring_view input_hint;
  // Year.
  int publication_date;
};

std::map<wchar_t, Source> const& Sources() {
  static const std::map<wchar_t, Source>& sources = ([]() -> auto const& {
    return *new std::map<wchar_t, Source>{{
        {L'A', {L"Borger ‸ABZ", 1978}},
        {L'L', {L"‸Labat", 1976}},
        {L'M', {L"Borger ‸MesZL", 2004}},
    }};
  })();
  return sources;
}

std::map<wchar_t, int> const& Alphabet() {
  static const std::map<wchar_t, int>& alphabetical_order =
      ([]() -> auto const& {
        constexpr std::array<wchar_t, 26> alphabet{
            {'a', 'b', 'd', 'e', 'g', L'ŋ', L'ḫ', 'i', 'j', 'k', 'l', 'm', 'n',
             'p', 'q', 'r', 's', L'ṣ', L'š', L'ś', 't', L'ṭ', 'u', 'w', 'z', ʾaleph}};
        auto& alphabetical_order = *new std::map<wchar_t, int>();
        for (int i = 0; i < alphabet.size(); ++i) {
          alphabetical_order.emplace(alphabet[i], i);
        }
        return alphabetical_order;
      })();
  return alphabetical_order;
}

// Like std::isdigit but with less UB.
constexpr bool IsDigit(wchar_t const c) {
  return c >= '0' && c <= '9';
}

std::tuple<std::vector<std::vector<int>>,
           std::vector<std::vector<int>>,
           std::optional<int>,
           int>
OrderingKey(
    std::wstring_view composition_input) {
  std::tuple<std::vector<std::vector<int>>,
             std::vector<std::vector<int>>,
             std::optional<int>,
             int>
      key;
  auto& [alephless_reading, reading, source_order, variant] = key;
  enum class InputCategory {
    ReadingNumeric,
    FractionSlash,
    ReadingAlphabetic,
    Source,
    Variant,
  };
  // Note that we want fractions to be ordered after their numerator and by
  // increasing denumerator, and we do not want to worry about the ordering of /
  // vs. other input symbols, i.e., 1 < 1iku < 1/2 < 1/2iku < 1/4 < 1/4iku < 2.
  // We achieve that by putting fractions in a single segment {numerator,
  // denominator}, thus
  // {{1}} < {{1}, iku} < {{1, 2}} < {{1, 2}, iku}
  //       < {{1, 4}} < {{1, 4}, iku} < {{2}}.

  std::optional<InputCategory> last_category;
  for (const wchar_t c : composition_input) {
    if (Alphabet().contains(c)) {
      if (last_category != InputCategory::ReadingAlphabetic) {
        reading.emplace_back();
      }
      reading.back().push_back(Alphabet().at(c));
      last_category = InputCategory::ReadingAlphabetic;
    } else if (IsDigit(c)) {
      if (last_category == InputCategory::Variant) {
        variant *= 10;
        variant += c - L'0';
      } else {
        if (last_category == InputCategory::ReadingNumeric) {
          reading.back().back() *= 10;
        } else if (last_category == InputCategory::FractionSlash) {
          reading.back().emplace_back();
        } else {
          reading.emplace_back().emplace_back();
        }
        reading.back().back() += c - L'0';
        last_category = InputCategory::ReadingNumeric;
      }
    } else if (c == L'x') {
      reading.emplace_back().emplace_back();
      reading.back().back() = std::numeric_limits<int>::max();
      last_category = InputCategory::ReadingNumeric;
    } else if (Sources().contains(c)) {
      source_order = -Sources().at(c).publication_date;
      last_category = InputCategory::Source;
    } else if (c == L'/') {
      last_category = InputCategory::FractionSlash;
    } else if (c == L'v') {
      last_category = InputCategory::Variant;
    }
  }
  for (auto const& word : reading) {
    alephless_reading.emplace_back();
    for (int const c : word) {
      if (c != ʾaleph) {  // TODO(egg): How do we distinguish 702 from ʾaleph?
        alephless_reading.back().push_back(c);
      }
    }
  }
  return key;
}

std::wstring PrettyTranscriptionHint(std::wstring_view composition_input,
                                     int entered_size) {
  const std::set<wchar_t> vowels = {'a', 'e', 'u', 'i'};
  constexpr auto is_reading_character = [](wchar_t c) {
    // Reading alphanumeric, and a handful of symbols for fractions,
    // punctuation, and determinative shorthands.
    return IsDigit(c) || Alphabet().contains(c) || c == '/' || c == ':' ||
           c == L'⫶' || c == 'f' || c == 'x' || c == '+' || c == '-';
  };
  bool subscript_has_been_entered = true;
  int vowel_count = 0;
  int homophone_index = 0;
  for (int i = 0; i < composition_input.size(); ++i) {
    if (!is_reading_character(composition_input[i])) {
      break;
    }
    if (vowel_count == 0 && !Alphabet().contains(composition_input[i])) {
      // Skip leading digits and get to the unit, if any.
      continue;
    }
    if (IsDigit(composition_input[i]) && entered_size <= i) {
      subscript_has_been_entered = false;
    }
    if (vowels.contains(composition_input[i])) {
      ++vowel_count;
    }
    if (IsDigit(composition_input[i])) {
      homophone_index *= 10;
      homophone_index += composition_input[i] - '0';
    }
  }
  std::wstring_view accent;
  if (subscript_has_been_entered && vowel_count == 1) {
    if (homophone_index == 2) {
      accent = L"\u0301";
    } else if (homophone_index == 3) {
      accent = L"\u0300";
    }
  }
  std::wstring result;
  bool in_parenthetical = false;
  bool after_letters = false;
  bool has_source = false;
  for (int i = 0; i < composition_input.size(); ++i) {
    if (!is_reading_character(composition_input[i])) {
      result += L" (";
      in_parenthetical = true;
    }

    std::wstring token_hint;
    if (Sources().contains(composition_input[i])) {
      token_hint += Sources().at(composition_input[i]).input_hint;
    } else if (composition_input[i] == 'v') {
      if (has_source) {
        token_hint += L", ";
      }
      token_hint += L"‸variant ";
    } else {
      token_hint += L'‸';
      if (IsDigit(composition_input[i]) || composition_input[i] == L'x') {
        if (!after_letters || in_parenthetical) {
          token_hint += composition_input[i];
        } else if (accent.empty()) {
          token_hint += composition_input[i] == L'x'
                            ? L'ₓ'
                            : L'₀' + (composition_input[i] - L'0');
        }
      } else {
        if (Alphabet().contains(composition_input[i])) {
          after_letters = true;
        }
        if (composition_input == L"m") {
          token_hint += L"ᵐ";
        } else if (composition_input == L"f") {
          token_hint += L"ᶠ";
        } else if (composition_input == L"d") {
          token_hint += L"ᵈ";
        } else if (composition_input[i] == L'+') {
          token_hint += L'⁺';
        } else if (composition_input[i] == L'-') {
          token_hint += L'⁻';
        } else {
          token_hint += composition_input[i];
        }
        if (!in_parenthetical && !accent.empty() &&
            vowels.contains(composition_input[i])) {
          token_hint += accent;
        }
      }
    }
    for (wchar_t c : token_hint) {
      if (c != L'‸' || entered_size == i) {
        result += c;
      }
    }
  }
  if (in_parenthetical) {
    result += L')';
  }
  if (entered_size == composition_input.size()) {
    result += L'‸';
  }
  return result;
}

bool InputsOrdered(std::wstring_view left, std::wstring_view right) {
  return OrderingKey(left) < OrderingKey(right);
}

}  // namespace 𒄑𒂅𒌋
