#pragma once

#include <string>

namespace 𒂗𒈨𒅕𒃸 {

bool IsTransliterationLetter(wchar_t c);
bool IsSubscriptDigit(wchar_t c);
wchar_t ToSubscript(wchar_t c);
bool IsSubscriptable(wchar_t c);

std::wstring PrettyTransliterationHint(std::wstring_view composition_input,
                                     int entered_size);

// Whether left should be ordered before right.
bool InputsOrdered(std::wstring_view left, std::wstring_view right);

}  // namespace 𒂗𒈨𒅕𒃸
