#include "𒂗𒈨𒅕𒃸/transcription.h"

#include <algorithm>
#include <array>
#include <map>
#include <optional>
#include <set>
#include <vector>

namespace 𒂗𒈨𒅕𒃸 {

constexpr wchar_t ʾaleph = L'ʾ';

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

std::tuple<std::vector<std::vector<int>>, std::vector<std::vector<int>>, int>
ListOrderingKey(std::wstring_view composition_input) {
  std::tuple<std::vector<std::vector<int>>, std::vector<std::vector<int>>, int>
      key;
  // TODO(egg): It is dumb that we have to deal with that alephless nonsense
  // here.
  auto& [alephless_reading, reading, variant] = key;
  int name_length = 0;
  while (!IsDigit(composition_input[name_length])) {
    ++name_length;
  }
  auto const name = composition_input.substr(0, name_length);
  int number_length = 0;
  while (name_length + number_length < composition_input.size() &&
         IsDigit(composition_input[name_length + number_length])) {
    ++number_length;
  }
  auto const number = composition_input.substr(name_length, number_length);
  int tail_length = 0;
  while (name_length + number_length + tail_length < composition_input.size() &&
         composition_input[name_length + number_length + tail_length] != 'v') {
    ++tail_length;
  }
  auto const tail =
      composition_input.substr(name_length + number_length, tail_length);
  alephless_reading.emplace_back().push_back(0);
  reading.emplace_back().push_back(0);
  for (wchar_t const c : number) {
    for (int* const n :
         {&alephless_reading.back().back(), &reading.back().back()}) {
      *n *= 10;
      *n += c - L'0';
    }
  }
  alephless_reading.emplace_back();
  reading.emplace_back();
  for (wchar_t const c : tail) {
    alephless_reading.back().emplace_back(c);
    reading.back().emplace_back(c);
  }
  variant = 0;
  if (name_length + number_length < composition_input.size()) {
    for (wchar_t const c :
         composition_input.substr(name_length + number_length + tail_length)) {
      variant *= 10;
      variant += c - L'0';
    }
  }
  return key;
}

std::tuple<std::vector<std::vector<int>>,
           std::vector<std::vector<int>>,
           int>
OrderingKey(
    std::wstring_view composition_input) {
  if (composition_input.starts_with('x')) {
    return ListOrderingKey(composition_input.substr(1));
  }
  std::tuple<std::vector<std::vector<int>>,
             std::vector<std::vector<int>>,
             int>
      key;
  auto& [alephless_reading, reading, variant] = key;
  enum class InputCategory {
    ReadingNumeric,
    FractionSlash,
    ReadingAlphabetic,
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
  for (int i = 0; i < composition_input.length(); ++i) {
    const wchar_t c = composition_input[i];
    const std::optional<wchar_t> lookahead =
        i == composition_input.length()
            ? std::nullopt
            : std::optional(composition_input[i + 1]);
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
    } else if (c == L'+' || c == L'-') {
      if (lookahead.has_value() && Alphabet().contains(*lookahead)) {
        // Force ligatures to the end of the candidate list.
        reading.insert(reading.begin(), {std::numeric_limits<int>::max()});
      }
      if (last_category != InputCategory::ReadingNumeric) {
        // Treat an absence of numeric reading as a numeric reading of -1, so it
        // sorts before any numeric reading, but still allows us to append a key
        // for the sign.
        reading.emplace_back().emplace_back(-1);
        last_category = InputCategory::ReadingNumeric;
      }
      reading.back().emplace_back(c == L'-' ? 0 : 1);
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

constexpr std::array<std::pair<std::wstring_view, std::wstring_view>, 13>
    sign_lists{{
        {L"abzl", L"aBZL"},
        {L"bau", L"BAU"},
        {L"elles", L"ELLes"},
        {L"ḫzl", L"HZL"},
        {L"kwu", L"KWU"},
        {L"lak", L"LAK"},
        {L"mea", L"MÉA"},
        {L"mzl", L"MZL"},
        {L"ptaše", L"PTACE"},
        {L"reš", L"RÉC"},
        {L"rsp", L"RSP"},
        {L"šl", L"ŠL"},
        {L"zatu", L"ZATU"},
    }};

std::wstring PrettyListHint(std::wstring_view composition_input,
                            int entered_size) {
  std::wstring_view pretty_list;
  for (auto const [list_composition, list_name] : sign_lists) {
    if (composition_input.starts_with(list_composition)) {
      pretty_list = list_name;
    }
  }
  std::wstring result;
  bool in_parenthetical = false;
  for (int i = 0; i < composition_input.size(); ++i) {
    wchar_t const c = composition_input[i];
    if (c == 'v') {
      result += L" (";
      in_parenthetical = true;
    }

    std::wstring token_hint;
    if (c == 'v') {
      token_hint += L"‸variant ";
    } else {
      token_hint += L'‸';
      if (i < pretty_list.size()) {
        token_hint += pretty_list[i];
      } else if (c == L'š') {
        token_hint += L'c';
      } else {
        token_hint += c;
      }
    }
    if (i == pretty_list.size()) {
      result += ' ';
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
  result += composition_input.substr(0, entered_size);
  result += L'‸';
  result += composition_input.substr(entered_size);
  return result;
}

std::wstring PrettyTranscriptionHint(std::wstring_view composition_input,
                                     int entered_size) {
  if (composition_input.front() == 'x') {
    return PrettyListHint(composition_input.substr(1), entered_size - 1);
  }
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
    // TODO(egg): This does not work for things like il₃+suen—though admittedly
    // such compositions are silly.
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
  for (int i = 0; i < composition_input.size(); ++i) {
    if (!is_reading_character(composition_input[i])) {
      result += L" (";
      in_parenthetical = true;
    }

    std::wstring token_hint;
    if (composition_input[i] == 'v') {
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
        } else if (i == 0 && composition_input[0] == L'd' &&
                   composition_input.length() > 1 &&
                   !Alphabet().contains(composition_input[1])) {
          token_hint += L"ᵈ";
        } else if (composition_input[i] == L'+' &&
                   ((i == 1 && composition_input[0] == L'd') ||
                    composition_input.length() == i + 1 ||
                    !Alphabet().contains(composition_input[i + 1]))) {
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

}  // namespace 𒂗𒈨𒅕𒃸
