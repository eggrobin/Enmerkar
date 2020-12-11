#include "𒄑𒂅𒌋/latin_layout.h"

#include <codecvt>
#include <filesystem>
#include <fstream>
#include <sstream>

#include "Globals.h"

namespace 𒄑𒂅𒌋 {

constexpr std::array<wchar_t, 256> GetLayout(
    std::array<wchar_t, 48> ansi_rows) {
  std::array<wchar_t, 256> virtual_key_code_to_character{};
  for (int i = 0; i < 47; ++i) {
    virtual_key_code_to_character[ANSIPrintableVirtualKeyCodes[i]] =
        ansi_rows[i];
  }
  return virtual_key_code_to_character;
}

std::array<wchar_t, 48> GetLayoutConfiguration() {
  wchar_t dll_filename_data[MAX_PATH]{};
  auto const dll_filename_size =
      GetModuleFileName(Global::dllInstanceHandle,
                        dll_filename_data,
                        ARRAYSIZE(dll_filename_data));
  std::wstring_view dll_filename(dll_filename_data, dll_filename_size);
  std::filesystem::path dll_path(dll_filename);
  std::ifstream file(dll_path.parent_path().parent_path() / "layout.txt");
  std::array<wchar_t, 48> result{
      L"EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE"};
  wchar_t c;
  char& low = reinterpret_cast<char&>(c);
  char& high = *(&low + 1);
  for (int i = 0; i < 47;) {
    file.get(low);
    file.get(high);
    if (c == L'\uFEFF' || c == L'\r' || c == L'\n' || c == ' ') {
      continue;
    }
    result[i++] = c;
  }
  return result;
}

wchar_t LatinLayout::GetCharacter(const std::uint8_t virtual_key_code) {
  static auto layout = GetLayout(GetLayoutConfiguration());
  return layout[virtual_key_code];
}

}  // namespace 𒄑𒂅𒌋
