#pragma once

#include <string>

namespace 𒄑𒂅𒌋 {

std::wstring PrettyTranscriptionHint(std::wstring_view composition_input,
                                     int entered_size);

// Whether left should be ordered before right.
bool InputsOrdered(std::wstring_view left, std::wstring_view right);

}  // namespace 𒄑𒂅𒌋
