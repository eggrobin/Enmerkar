#pragma once

#include <cstdint>

#include <array>
#include <string>

#include <Windows.h>
#include <WinUser.h>

namespace 𒄑𒂅𒌋 {

inline constexpr std::array<std::uint8_t, 47> ANSIPrintableVirtualKeyCodes{{
    // clang-format off
VK_OEM_3,'1','2','3','4','5','6','7','8','9','0',VK_OEM_MINUS,VK_OEM_PLUS,
            'Q','W','E','R','T','Y','U','I','O','P',VK_OEM_4,VK_OEM_6,VK_OEM_5,
              'A','S','D','F','G','H','J','K','L',VK_OEM_1,VK_OEM_7,
                'Z','X','C','V','B','N','M',VK_OEM_COMMA,VK_OEM_PERIOD,VK_OEM_2,
    // clang-format on
}};

std::wstring GetUserLatinFont();
std::wstring GetUserCuneiformFont();

class LatinLayout {
 public:
  static wchar_t GetCharacter(std::uint8_t virtual_key_code);
};

}
