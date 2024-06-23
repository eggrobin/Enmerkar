#include "logging.h"

#include <chrono>
#include <fstream>

namespace 𒂗𒈨𒅕𒃸 {
  void Log(std::wstring_view const message) {
    auto const now = std::chrono::utc_clock::now();
    std::wofstream(R"(C:\Users\robin\Documents\Enmerkar.log)", std::ios_base::app | std::ios_base::out)
      << now << " " << sizeof(void*) * 8 << ": " << message << "\n";
  }
}
