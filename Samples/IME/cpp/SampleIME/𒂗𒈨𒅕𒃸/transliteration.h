#pragma once

#include <string>

namespace 𒂗𒈨𒅕𒃸 {

std::wstring PrettyTransliterationHint(std::wstring_view composition_input,
                                     int entered_size);

// Whether left should be ordered before right.
bool InputsOrdered(std::wstring_view left, std::wstring_view right);

}  // namespace 𒂗𒈨𒅕𒃸
