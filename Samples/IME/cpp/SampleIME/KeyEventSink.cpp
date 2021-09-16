// THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF
// ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO
// THE IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A
// PARTICULAR PURPOSE.
//
// Copyright (c) Microsoft Corporation. All rights reserved

#include <string>

#include "Private.h"
#include "Globals.h"
#include "SampleIME.h"
#include "CandidateListUIPresenter.h"
#include "CompositionProcessorEngine.h"
#include "KeyHandlerEditSession.h"
#include "Compartment.h"

#include "𒄑𒂅𒌋/settings.h"

// 0xF003, 0xF004 are the keys that the touch keyboard sends for next/previous
#define THIRDPARTY_NEXTPAGE  static_cast<WORD>(0xF003)
#define THIRDPARTY_PREVPAGE  static_cast<WORD>(0xF004)

// Because the code mostly works with VKeys, here map a WCHAR back to a VKKey for certain
// vkeys that the IME handles specially
__inline UINT VKeyFromVKPacketAndWchar(UINT vk, WCHAR wch)
{
    UINT vkRet = vk;
    {
        if (wch == L' ')
        {
            vkRet = VK_SPACE;
        }
        else if ((wch >= L'0') && (wch <= L'9'))
        {
            vkRet = static_cast<UINT>(wch);
        }
        else if ((wch >= L'a') && (wch <= L'z'))
        {
            vkRet = (UINT)(L'A') + ((UINT)(L'z') - static_cast<UINT>(wch));
        }
        else if ((wch >= L'A') && (wch <= L'Z'))
        {
            vkRet = static_cast<UINT>(wch);
        }
        else if (wch == THIRDPARTY_NEXTPAGE)
        {
            vkRet = VK_NEXT;
        }
        else if (wch == THIRDPARTY_PREVPAGE)
        {
            vkRet = VK_PRIOR;
        }
    }
    return vkRet;
}

//+---------------------------------------------------------------------------
//
// _IsKeyEaten
//
//----------------------------------------------------------------------------

BOOL CSampleIME::_IsKeyEaten(_In_ ITfContext *pContext, UINT codeIn, _Out_ UINT *pCodeOut, _Out_writes_(1) WCHAR *pwch, _Out_opt_ _KEYSTROKE_STATE *pKeyState)
{
    pContext;

    *pCodeOut = codeIn;

    BOOL isOpen = FALSE;
    CCompartment CompartmentKeyboardOpen(_pThreadMgr, _tfClientId, GUID_COMPARTMENT_KEYBOARD_OPENCLOSE);
    CompartmentKeyboardOpen._GetCompartmentBOOL(isOpen);

    if (pKeyState)
    {
        pKeyState->Category = CATEGORY_NONE;
        pKeyState->Function = FUNCTION_NONE;
    }
    if (pwch)
    {
        *pwch = L'\0';
    }

    // if the keyboard is disabled, we don't eat keys.
    if (_IsKeyboardDisabled())
    {
        return FALSE;
    }

    //
    // Map virtual key to character code
    //
    WCHAR wch = 𒄑𒂅𒌋::LatinLayout::GetCharacter(codeIn);
    *pCodeOut = codeIn;// VKeyFromVKPacketAndWchar(codeIn, wch);

    if (pwch)
    {
        *pwch = wch;
    }

    //
    // Get composition engine
    //
    CCompositionProcessorEngine *pCompositionProcessorEngine;
    pCompositionProcessorEngine = _pCompositionProcessorEngine;

    if (GetKeyState(VK_CAPITAL) & 1) {
      return FALSE;
    }

    if (isOpen)
    {
      //
      // The candidate or phrase list handles the keys through ITfKeyEventSink.
      //
      // eat only keys that CKeyHandlerEditSession can handles.
      //
      if (pCompositionProcessorEngine->IsVirtualKeyNeed(*pCodeOut, pwch, _IsComposing(), _candidateMode, _isCandidateWithWildcard, pKeyState))
      {
        return TRUE;
      }
    }

    return FALSE;
}

//+---------------------------------------------------------------------------
//
// ConvertVKey
//
//----------------------------------------------------------------------------

WCHAR CSampleIME::ConvertVKey(UINT code)
{
    //
    // Map virtual key to scan code
    //
    UINT scanCode = 0;
    scanCode = MapVirtualKey(code, 0);

    //
    // Keyboard state
    //
    BYTE abKbdState[256] = {'\0'};
    if (!GetKeyboardState(abKbdState))
    {
        return 0;
    }

    //
    // Map virtual key to character code
    //
    WCHAR wch = '\0';
    if (ToUnicode(code, scanCode, abKbdState, &wch, 1, 0) == 1)
    {
        return wch;
    }

    return 0;
}

//+---------------------------------------------------------------------------
//
// _IsKeyboardDisabled
//
//----------------------------------------------------------------------------

BOOL CSampleIME::_IsKeyboardDisabled()
{
    ITfDocumentMgr* pDocMgrFocus = nullptr;
    ITfContext* pContext = nullptr;
    BOOL isDisabled = FALSE;

    if ((_pThreadMgr->GetFocus(&pDocMgrFocus) != S_OK) ||
        (pDocMgrFocus == nullptr))
    {
        // if there is no focus document manager object, the keyboard 
        // is disabled.
        isDisabled = TRUE;
    }
    else if ((pDocMgrFocus->GetTop(&pContext) != S_OK) ||
        (pContext == nullptr))
    {
        // if there is no context object, the keyboard is disabled.
        isDisabled = TRUE;
    }
    else
    {
        CCompartment CompartmentKeyboardDisabled(_pThreadMgr, _tfClientId, GUID_COMPARTMENT_KEYBOARD_DISABLED);
        CompartmentKeyboardDisabled._GetCompartmentBOOL(isDisabled);

        CCompartment CompartmentEmptyContext(_pThreadMgr, _tfClientId, GUID_COMPARTMENT_EMPTYCONTEXT);
        CompartmentEmptyContext._GetCompartmentBOOL(isDisabled);
    }

    if (pContext)
    {
        pContext->Release();
    }

    if (pDocMgrFocus)
    {
        pDocMgrFocus->Release();
    }

    return isDisabled;
}

//+---------------------------------------------------------------------------
//
// ITfKeyEventSink::OnSetFocus
//
// Called by the system whenever this service gets the keystroke device focus.
//----------------------------------------------------------------------------

STDAPI CSampleIME::OnSetFocus(BOOL fForeground)
{
	fForeground;

    return S_OK;
}

static bool LetKeyDownThrough = false;
static bool LetKeyUpThrough = false;
static bool Received¹ = false;

//+---------------------------------------------------------------------------
//
// ITfKeyEventSink::OnTestKeyDown
//
// Called by the system to query this service wants a potential keystroke.
//----------------------------------------------------------------------------

STDAPI CSampleIME::OnTestKeyDown(ITfContext *pContext, WPARAM wParam, LPARAM lParam, BOOL *pIsEaten)
{
    Global::UpdateModifiers(wParam, lParam);

    _KEYSTROKE_STATE KeystrokeState;
    WCHAR wch = '\0';
    UINT code = 0;
    *pIsEaten = _IsKeyEaten(pContext, (UINT)wParam, &code, &wch, &KeystrokeState);
    if (!*pIsEaten && wch) {
      *pIsEaten = !LetKeyDownThrough;
    }
    LetKeyDownThrough = false;

    if (KeystrokeState.Category == CATEGORY_INVOKE_COMPOSITION_EDIT_SESSION)
    {
        //
        // Invoke key handler edit session
        //
        KeystrokeState.Category = CATEGORY_COMPOSING;

        _InvokeKeyHandler(pContext, code, wch, (DWORD)lParam, KeystrokeState);
    }

    return S_OK;
}

//+---------------------------------------------------------------------------
//
// ITfKeyEventSink::OnKeyDown
//
// Called by the system to offer this service a keystroke.  If *pIsEaten == TRUE
// on exit, the application will not handle the keystroke.
//----------------------------------------------------------------------------

STDAPI CSampleIME::OnKeyDown(ITfContext *pContext, WPARAM wParam, LPARAM lParam, BOOL *pIsEaten)
{
    Global::UpdateModifiers(wParam, lParam);

    _KEYSTROKE_STATE KeystrokeState;
    WCHAR wch = '\0';
    UINT code = 0;

    *pIsEaten = _IsKeyEaten(pContext, (UINT)wParam, &code, &wch, &KeystrokeState);

    if (*pIsEaten)
    {
        bool needInvokeKeyHandler = true;
        //
        // Invoke key handler edit session
        //
        if (code == VK_ESCAPE)
        {
            KeystrokeState.Category = CATEGORY_COMPOSING;
        }

        // Always eat THIRDPARTY_NEXTPAGE and THIRDPARTY_PREVPAGE keys, but don't always process them.
        if ((wch == THIRDPARTY_NEXTPAGE) || (wch == THIRDPARTY_PREVPAGE))
        {
            needInvokeKeyHandler = !((KeystrokeState.Category == CATEGORY_NONE) && (KeystrokeState.Function == FUNCTION_NONE));
        }

        if (needInvokeKeyHandler)
        {
            _InvokeKeyHandler(pContext, code, wch, (DWORD)lParam, KeystrokeState);
        }
    }
    else if (KeystrokeState.Category == CATEGORY_INVOKE_COMPOSITION_EDIT_SESSION)
    {
        // Invoke key handler edit session
        KeystrokeState.Category = CATEGORY_COMPOSING;
        _InvokeKeyHandler(pContext, code, wch, (DWORD)lParam, KeystrokeState);
    }

    if (!*pIsEaten && wch && !LetKeyDownThrough) {
      if (Global::ModifiersValue & (TF_MOD_CONTROL | TF_MOD_LCONTROL | TF_MOD_RCONTROL)) {
        WORD vkey;
        if (wch >= 'a' && wch <= 'z') {
          vkey = 'A' + (wch - 'a');
        } else if (wch == L'š') {
          vkey = 'C';
        } else if (wch == L'ḫ') {
          vkey = 'H';
        } else if (wch >= '0' && wch <= '9') {
          vkey = wch;
        } else {
          vkey = static_cast<WORD>(wParam);
        }
        INPUT input = {
            .type = INPUT_KEYBOARD,
            .ki = {
                .wVk = vkey,
                .wScan = 0,
                .dwFlags = 0}};
        LetKeyDownThrough = true;
        SendInput(1, &input, sizeof(input));
      } else {
        if (GetKeyState(VK_CAPITAL) & 1 && Global::ModifiersValue & (TF_MOD_SHIFT | TF_MOD_LSHIFT | TF_MOD_RSHIFT)) {
          wch = 𒄑𒂅𒌋::LatinLayout::GetShiftedCharacter(code);
        }
        if (!Received¹ && wch == L'¹') {
          Received¹ = true;
        } else {
          if (Received¹) {
            Received¹ = false;
            wch = wch == L'd' ? L'ᵈ'
                : wch == L'f' ? L'ᶠ'
                : wch == L'm' ? L'ᵐ'
                : wch == L'+' ? L'⁺'
                : wch == L'-' ? L'⁻'
                              : wch;
          } else {
            if (wch >= L'0' && wch <= L'9') {
              wch = L'₀' + wch - L'0';
            }
            if (wch == L'x') {
              wch = L'ₓ';
            }
          }
          INPUT input = {
            .type = INPUT_KEYBOARD,
            .ki = {
                .wVk = 0,
                .wScan = wch,
                .dwFlags = KEYEVENTF_UNICODE}};
          SendInput(1, &input, sizeof(input));
        }
      }
      *pIsEaten = true;
    } else {
      LetKeyDownThrough = false;
    }

    return S_OK;
}

//+---------------------------------------------------------------------------
//
// ITfKeyEventSink::OnTestKeyUp
//
// Called by the system to query this service wants a potential keystroke.
//----------------------------------------------------------------------------

STDAPI CSampleIME::OnTestKeyUp(ITfContext *pContext, WPARAM wParam, LPARAM lParam, BOOL *pIsEaten)
{
    if (pIsEaten == nullptr)
    {
        return E_INVALIDARG;
    }

    Global::UpdateModifiers(wParam, lParam);

    WCHAR wch = '\0';
    UINT code = 0;

    *pIsEaten = _IsKeyEaten(pContext, (UINT)wParam, &code, &wch, NULL);
    if (!*pIsEaten && wch) {
      *pIsEaten = !LetKeyUpThrough;
    }
    LetKeyUpThrough = false;

    return S_OK;
}

//+---------------------------------------------------------------------------
//
// ITfKeyEventSink::OnKeyUp
//
// Called by the system to offer this service a keystroke.  If *pIsEaten == TRUE
// on exit, the application will not handle the keystroke.
//----------------------------------------------------------------------------

STDAPI CSampleIME::OnKeyUp(ITfContext *pContext, WPARAM wParam, LPARAM lParam, BOOL *pIsEaten)
{
    Global::UpdateModifiers(wParam, lParam);

    WCHAR wch = '\0';
    UINT code = 0;

    *pIsEaten = _IsKeyEaten(pContext, (UINT)wParam, &code, &wch, NULL);
    if (!*pIsEaten && wch && !LetKeyUpThrough) {
      INPUT input;
      if (Global::ModifiersValue & (TF_MOD_CONTROL | TF_MOD_LCONTROL | TF_MOD_RCONTROL)) {
        WORD vkey;
        if (wch >= 'a' && wch <= 'z') {
          vkey = 'A' + (wch - 'a');
        } else if (wch == L'š') {
          vkey = 'C';
        } else if (wch == L'ḫ') {
          vkey = 'H';
        } else if (wch >= '0' && wch <= '9') {
          vkey = wch;
        } else {
          vkey = static_cast<WORD>(wParam);
        }
        input = {
            .type = INPUT_KEYBOARD,
            .ki = {
                .wVk = vkey,
                .wScan = 0,
                .dwFlags = KEYEVENTF_KEYUP}};
        LetKeyUpThrough = true;
      } else {
        input = {
          .type = INPUT_KEYBOARD,
          .ki = {
              .wVk = 0,
              .wScan = wch,
              .dwFlags = KEYEVENTF_KEYUP | KEYEVENTF_UNICODE}};
      }
      SendInput(1, &input, sizeof(input));
      *pIsEaten = true;
    } else {
      LetKeyUpThrough = false;
    }

    return S_OK;
}

//+---------------------------------------------------------------------------
//
// ITfKeyEventSink::OnPreservedKey
//
// Called when a hotkey (registered by us, or by the system) is typed.
//----------------------------------------------------------------------------

STDAPI CSampleIME::OnPreservedKey(ITfContext *pContext, REFGUID rguid, BOOL *pIsEaten)
{
	pContext;

    CCompositionProcessorEngine *pCompositionProcessorEngine;
    pCompositionProcessorEngine = _pCompositionProcessorEngine;

    pCompositionProcessorEngine->OnPreservedKey(rguid, pIsEaten, _GetThreadMgr(), _GetClientId());

    return S_OK;
}

//+---------------------------------------------------------------------------
//
// _InitKeyEventSink
//
// Advise a keystroke sink.
//----------------------------------------------------------------------------

BOOL CSampleIME::_InitKeyEventSink()
{
    ITfKeystrokeMgr* pKeystrokeMgr = nullptr;
    HRESULT hr = S_OK;

    if (FAILED(_pThreadMgr->QueryInterface(IID_ITfKeystrokeMgr, (void **)&pKeystrokeMgr)))
    {
        return FALSE;
    }

    hr = pKeystrokeMgr->AdviseKeyEventSink(_tfClientId, (ITfKeyEventSink *)this, TRUE);

    pKeystrokeMgr->Release();

    return (hr == S_OK);
}

//+---------------------------------------------------------------------------
//
// _UninitKeyEventSink
//
// Unadvise a keystroke sink.  Assumes we have advised one already.
//----------------------------------------------------------------------------

void CSampleIME::_UninitKeyEventSink()
{
    ITfKeystrokeMgr* pKeystrokeMgr = nullptr;

    if (FAILED(_pThreadMgr->QueryInterface(IID_ITfKeystrokeMgr, (void **)&pKeystrokeMgr)))
    {
        return;
    }

    pKeystrokeMgr->UnadviseKeyEventSink(_tfClientId);

    pKeystrokeMgr->Release();
}
