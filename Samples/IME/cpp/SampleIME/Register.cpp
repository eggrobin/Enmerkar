// THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF
// ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO
// THE IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A
// PARTICULAR PURPOSE.
//
// Copyright (c) Microsoft Corporation. All rights reserved

#include <algorithm>
#include <optional>
#include <set>
#include <string>

#define NOMINMAX

#include "Private.h"
#include "Globals.h"

#include <wil/registry.h>

#include "logging.h"

static const WCHAR RegInfo_Prefix_CLSID[] = L"CLSID\\";
static const WCHAR RegInfo_Key_InProSvr32[] = L"InProcServer32";
static const WCHAR RegInfo_Key_ThreadModel[] = L"ThreadingModel";

static const WCHAR TEXTSERVICE_DESC[] = L"𒂗𒈨𒅕𒃸 Cuneiform IME";

static const GUID SupportCategories[] = {
    GUID_TFCAT_TIP_KEYBOARD,
    GUID_TFCAT_DISPLAYATTRIBUTEPROVIDER,
    //GUID_TFCAT_TIPCAP_UIELEMENTENABLED,
    GUID_TFCAT_TIPCAP_SECUREMODE,
    GUID_TFCAT_TIPCAP_COMLESS,
    //GUID_TFCAT_TIPCAP_INPUTMODECOMPARTMENT,
    GUID_TFCAT_TIPCAP_IMMERSIVESUPPORT,
    //GUID_TFCAT_TIPCAP_SYSTRAYSUPPORT,
};
//+---------------------------------------------------------------------------
//
//  RegisterProfiles
//
//----------------------------------------------------------------------------

BOOL RegisterProfiles()
{
    𒂗𒈨𒅕𒃸::Log(L"Registering profiles...");
    HRESULT hr = S_FALSE;
    //LANGID langid = TEXTSERVICE_LANGID;

    ITfInputProcessorProfileMgr *pITfInputProcessorProfileMgr = nullptr;
    hr = CoCreateInstance(CLSID_TF_InputProcessorProfiles, NULL, CLSCTX_INPROC_SERVER,
        IID_ITfInputProcessorProfileMgr, (void**)&pITfInputProcessorProfileMgr);
    if (FAILED(hr))
    {
        return FALSE;
    }

    WCHAR achIconFile[MAX_PATH] = {'\0'};
    DWORD cchA = 0;
    cchA = GetModuleFileName(Global::dllInstanceHandle, achIconFile, MAX_PATH);
    cchA = cchA >= MAX_PATH ? (MAX_PATH - 1) : cchA;
    achIconFile[cchA] = '\0';

    size_t lenOfDesc = 0;
    hr = StringCchLength(TEXTSERVICE_DESC, STRSAFE_MAX_CCH, &lenOfDesc);
    if (hr != S_OK)
    {
        goto Exit;
    } else {
      auto const international_user_profile = wil::reg::open_unique_key(
        HKEY_CURRENT_USER,
        LR"(Control Panel\International\User Profile)",
        wil::reg::key_access::readwrite);
      constexpr PCWSTR 𒂗𒈨𒅕𒃸_tag = L"akk-Xsux";
      std::optional<wil::unique_hkey> 𒂗𒈨𒅕𒃸_language;
      std::optional<LANGID> 𒂗𒈨𒅕𒃸_langid;
      // List from https://learn.microsoft.com/en-us/windows/win32/sysinfo/enumerating-registry-subkeys.
      std::set<LANGID> unused_transient_langids{
          0x2000, 0x2400, 0x2800, 0x2C00,
          0x3000, 0x3400, 0x3800, 0x3C00,
          0x4000, 0x4400, 0x4800, 0x4C00 };
      for (auto const& subkey : wil::make_range(wil::reg::key_iterator{international_user_profile.get()}, wil::reg::key_iterator{})) {
        auto const& language_tag = subkey.name;
        wil::unique_hkey language = wil::reg::open_unique_key(
          international_user_profile.get(),
          language_tag.c_str(),
          wil::reg::key_access::readwrite);
        if (auto const langid = wil::reg::try_get_value<DWORD>(language.get(), L"TransientLangId"); langid.has_value()) {
          if (language_tag == 𒂗𒈨𒅕𒃸_tag) {
            𒂗𒈨𒅕𒃸_langid = static_cast<LANGID>(*langid);
          }
          unused_transient_langids.erase(static_cast<LANGID>(*langid));
        }
        if (language_tag == 𒂗𒈨𒅕𒃸_tag) {
          𒂗𒈨𒅕𒃸_language = std::move(language);
        }
      }
      if (!𒂗𒈨𒅕𒃸_langid.has_value()) {
        if (unused_transient_langids.empty()) {
          MessageBoxW(
            nullptr, L"All transient LANGIDs in use", nullptr,
            MB_OK | MB_ICONERROR);
          goto Exit;
        }
        𒂗𒈨𒅕𒃸_langid = *unused_transient_langids.begin();
      }
      std::wstring const 𒂗𒈨𒅕𒃸_langid_string = std::format(L"{:04X}", *𒂗𒈨𒅕𒃸_langid);
      std::wstring const 𒂗𒈨𒅕𒃸_padded_langid_string = L"0000" + 𒂗𒈨𒅕𒃸_langid_string;
      if (!𒂗𒈨𒅕𒃸_language.has_value()) {
        𒂗𒈨𒅕𒃸_language = wil::reg::create_unique_key(international_user_profile.get(), 𒂗𒈨𒅕𒃸_tag,
          wil::reg::key_access::readwrite);
      }
      wil::reg::set_value<DWORD>(𒂗𒈨𒅕𒃸_language->get(), L"TransientLangId", *𒂗𒈨𒅕𒃸_langid);
      std::wstring const input_profile = 𒂗𒈨𒅕𒃸_langid_string + L":{F87CB858-5A61-42FF-98E4-CF3966457808}";
      if (wil::reg::try_get_value<DWORD>(𒂗𒈨𒅕𒃸_language->get(), input_profile.c_str()) != 1) {
        wil::reg::set_value(𒂗𒈨𒅕𒃸_language->get(), input_profile.c_str(), 1);
      }
      auto languages = wil::reg::get_value<std::vector<std::wstring>>(international_user_profile.get(), L"Languages");
      if (std::find(languages.begin(), languages.end(), 𒂗𒈨𒅕𒃸_tag) == languages.end()) {
        languages.emplace_back(𒂗𒈨𒅕𒃸_tag);
        wil::reg::set_value(international_user_profile.get(), L"Languages", languages);
      }
      MessageBoxW(
        nullptr, std::format(L"Registering with transient LANGID {:04X}", *𒂗𒈨𒅕𒃸_langid).c_str(), nullptr,
        MB_OK | MB_ICONINFORMATION);
      auto const keyboard_layout_preload = wil::reg::open_unique_key(
        HKEY_CURRENT_USER,
        LR"(Keyboard Layout\Preload)",
        wil::reg::key_access::readwrite);
      int highest_index = 0;
      std::optional<int> 𒂗𒈨𒅕𒃸_preload_index;
      for (auto const& value : wil::make_range(wil::reg::value_iterator{ keyboard_layout_preload.get() }, wil::reg::value_iterator{})) {
        std::string ascii_key;
        std::transform(value.name.begin(), value.name.end(),
                       std::back_inserter(ascii_key),
                       [](wchar_t c) { return c <= 0x7F ? c : '?'; });
        int index;
        if (std::from_chars(ascii_key.data(), ascii_key.data() + ascii_key.size(), index).ec == std::errc{}) {
          highest_index = std::max(highest_index, index);
          if (wil::reg::get_value<std::wstring>(keyboard_layout_preload.get(), value.name.c_str()) == 𒂗𒈨𒅕𒃸_padded_langid_string) {
            𒂗𒈨𒅕𒃸_preload_index = index;
          }
        }
      }
      if (!𒂗𒈨𒅕𒃸_preload_index.has_value()) {
        𒂗𒈨𒅕𒃸_preload_index = highest_index + 1;
        wil::reg::set_value(
            keyboard_layout_preload.get(),
            std::to_wstring(*𒂗𒈨𒅕𒃸_preload_index).c_str(),
            𒂗𒈨𒅕𒃸_padded_langid_string.c_str());
      }
      auto const keyboard_layout_substitutes = wil::reg::open_unique_key(
        HKEY_CURRENT_USER,
        LR"(Keyboard Layout\Substitutes)",
        wil::reg::key_access::readwrite);
      wil::reg::set_value(
        keyboard_layout_substitutes.get(),
        𒂗𒈨𒅕𒃸_padded_langid_string.c_str(),
        L"00000409");
      auto const hidden_dummy_layouts = wil::reg::open_unique_key(
        HKEY_CURRENT_USER,
        LR"(Software\Microsoft\CTF\HiddenDummyLayouts)",
        wil::reg::key_access::readwrite);
      wil::reg::set_value(
        hidden_dummy_layouts.get(),
        𒂗𒈨𒅕𒃸_padded_langid_string.c_str(),
        L"00000409");
      hr = pITfInputProcessorProfileMgr->RegisterProfile(Global::SampleIMECLSID,
          *𒂗𒈨𒅕𒃸_langid,
          Global::SampleIMEGuidProfile,
          TEXTSERVICE_DESC,
          static_cast<ULONG>(lenOfDesc),
          achIconFile,
          cchA,
          (UINT)TEXTSERVICE_ICON_INDEX, NULL, 0, TRUE, 0);
    }

    if (FAILED(hr))
    {
        goto Exit;
    }
    𒂗𒈨𒅕𒃸::Log(L"Success");

Exit:
    if (pITfInputProcessorProfileMgr)
    {
        pITfInputProcessorProfileMgr->Release();
    }

    return (hr == S_OK);
}

//+---------------------------------------------------------------------------
//
//  UnregisterProfiles
//
//----------------------------------------------------------------------------

void UnregisterProfiles()
{
    HRESULT hr = S_OK;
    LANGID langid = TEXTSERVICE_LANGID;

    ITfInputProcessorProfileMgr *pITfInputProcessorProfileMgr = nullptr;
    hr = CoCreateInstance(CLSID_TF_InputProcessorProfiles, NULL, CLSCTX_INPROC_SERVER,
        IID_ITfInputProcessorProfileMgr, (void**)&pITfInputProcessorProfileMgr);
    if (FAILED(hr))
    {
        goto Exit;
    } else {
      hr = pITfInputProcessorProfileMgr->UnregisterProfile(Global::SampleIMECLSID, langid, Global::SampleIMEGuidProfile, 0);
      if (FAILED(hr))
      {
          goto Exit;
      }
    }

Exit:
    if (pITfInputProcessorProfileMgr)
    {
        pITfInputProcessorProfileMgr->Release();
    }

    return;
}

//+---------------------------------------------------------------------------
//
//  RegisterCategories
//
//----------------------------------------------------------------------------

BOOL RegisterCategories()
{
    𒂗𒈨𒅕𒃸::Log(L"Registering categories...");
    ITfCategoryMgr* pCategoryMgr = nullptr;
    HRESULT hr = S_OK;

    hr = CoCreateInstance(CLSID_TF_CategoryMgr, NULL, CLSCTX_INPROC_SERVER, IID_ITfCategoryMgr, (void**)&pCategoryMgr);
    if (FAILED(hr))
    {
        return FALSE;
    }

    for (GUID guid : SupportCategories)
    {
        hr = pCategoryMgr->RegisterCategory(Global::SampleIMECLSID, guid, Global::SampleIMECLSID);
    }

    pCategoryMgr->Release();
    if ((hr == S_OK)) {
    𒂗𒈨𒅕𒃸::Log(L"Success");
    }
    return (hr == S_OK);
}

//+---------------------------------------------------------------------------
//
//  UnregisterCategories
//
//----------------------------------------------------------------------------

void UnregisterCategories()
{
    ITfCategoryMgr* pCategoryMgr = nullptr;
    HRESULT hr = S_OK;

    hr = CoCreateInstance(CLSID_TF_CategoryMgr, NULL, CLSCTX_INPROC_SERVER, IID_ITfCategoryMgr, (void**)&pCategoryMgr);
    if (FAILED(hr))
    {
        return;
    }

    for (GUID guid : SupportCategories)
    {
        pCategoryMgr->UnregisterCategory(Global::SampleIMECLSID, guid, Global::SampleIMECLSID);
    }

    pCategoryMgr->Release();

    return;
}

//+---------------------------------------------------------------------------
//
// RecurseDeleteKey
//
// RecurseDeleteKey is necessary because on NT RegDeleteKey doesn't work if the
// specified key has subkeys
//----------------------------------------------------------------------------

LONG RecurseDeleteKey(_In_ HKEY hParentKey, _In_ LPCTSTR lpszKey)
{
    HKEY regKeyHandle = nullptr;
    LONG res = 0;
    FILETIME time;
    WCHAR stringBuffer[256] = {'\0'};
    DWORD size = ARRAYSIZE(stringBuffer);

    if (RegOpenKey(hParentKey, lpszKey, &regKeyHandle) != ERROR_SUCCESS)
    {
        return ERROR_SUCCESS;
    }

    res = ERROR_SUCCESS;
    while (RegEnumKeyEx(regKeyHandle, 0, stringBuffer, &size, NULL, NULL, NULL, &time) == ERROR_SUCCESS)
    {
        stringBuffer[ARRAYSIZE(stringBuffer)-1] = '\0';
        res = RecurseDeleteKey(regKeyHandle, stringBuffer);
        if (res != ERROR_SUCCESS)
        {
            break;
        }
        size = ARRAYSIZE(stringBuffer);
    }
    RegCloseKey(regKeyHandle);

    return res == ERROR_SUCCESS ? RegDeleteKey(hParentKey, lpszKey) : res;
}

//+---------------------------------------------------------------------------
//
//  RegisterServer
//
//----------------------------------------------------------------------------

BOOL RegisterServer()
{
    DWORD copiedStringLen = 0;
    HKEY regKeyHandle = nullptr;
    HKEY regSubkeyHandle = nullptr;
    BOOL ret = FALSE;
    WCHAR achIMEKey[ARRAYSIZE(RegInfo_Prefix_CLSID) + CLSID_STRLEN] = {'\0'};
    WCHAR achFileName[MAX_PATH] = {'\0'};

    if (!CLSIDToString(Global::SampleIMECLSID, achIMEKey + ARRAYSIZE(RegInfo_Prefix_CLSID) - 1))
    {
        return FALSE;
    }

    memcpy(achIMEKey, RegInfo_Prefix_CLSID, sizeof(RegInfo_Prefix_CLSID) - sizeof(WCHAR));

    if (RegCreateKeyEx(HKEY_CLASSES_ROOT, achIMEKey, 0, NULL, REG_OPTION_NON_VOLATILE, KEY_WRITE, NULL, &regKeyHandle, &copiedStringLen) == ERROR_SUCCESS)
    {
        if (RegSetValueEx(regKeyHandle, NULL, 0, REG_SZ, (const BYTE *)TEXTSERVICE_DESC, (_countof(TEXTSERVICE_DESC))*sizeof(WCHAR)) != ERROR_SUCCESS)
        {
            goto Exit;
        }

        if (RegCreateKeyEx(regKeyHandle, RegInfo_Key_InProSvr32, 0, NULL, REG_OPTION_NON_VOLATILE, KEY_WRITE, NULL, &regSubkeyHandle, &copiedStringLen) == ERROR_SUCCESS)
        {
            copiedStringLen = GetModuleFileNameW(Global::dllInstanceHandle, achFileName, ARRAYSIZE(achFileName));
            copiedStringLen = (copiedStringLen >= (MAX_PATH - 1)) ? MAX_PATH : (++copiedStringLen);
            if (RegSetValueEx(regSubkeyHandle, NULL, 0, REG_SZ, (const BYTE *)achFileName, (copiedStringLen)*sizeof(WCHAR)) != ERROR_SUCCESS)
            {
                goto Exit;
            }
            if (RegSetValueEx(regSubkeyHandle, RegInfo_Key_ThreadModel, 0, REG_SZ, (const BYTE *)TEXTSERVICE_MODEL, (_countof(TEXTSERVICE_MODEL)) * sizeof(WCHAR)) != ERROR_SUCCESS)
            {
                goto Exit;
            }

            ret = TRUE;
        }
    }

Exit:
    if (regSubkeyHandle)
    {
        RegCloseKey(regSubkeyHandle);
        regSubkeyHandle = nullptr;
    }
    if (regKeyHandle)
    {
        RegCloseKey(regKeyHandle);
        regKeyHandle = nullptr;
    }

    return ret;
}

//+---------------------------------------------------------------------------
//
//  UnregisterServer
//
//----------------------------------------------------------------------------

void UnregisterServer()
{
    WCHAR achIMEKey[ARRAYSIZE(RegInfo_Prefix_CLSID) + CLSID_STRLEN] = {'\0'};

    if (!CLSIDToString(Global::SampleIMECLSID, achIMEKey + ARRAYSIZE(RegInfo_Prefix_CLSID) - 1))
    {
        return;
    }

    memcpy(achIMEKey, RegInfo_Prefix_CLSID, sizeof(RegInfo_Prefix_CLSID) - sizeof(WCHAR));

    RecurseDeleteKey(HKEY_CLASSES_ROOT, achIMEKey);
}
