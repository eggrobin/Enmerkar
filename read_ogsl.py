from genericpath import samefile
import sys
import re
import codecs
import unicodedata

import numbers

#sys.stdout = codecs.getwriter("utf-16")(sys.stdout.detach())


MODIFIERS = {
  "g": "GUNU",
  "s": "SHESHIG",
  "t": "TENU",
  "z": "ZIDA TENU",
  "k": "KABA TENU",
  # In U+1248F CUNEIFORM SIGN DUG TIMES ASH AT LEFT, LAK561, given as
  # @uname CUNEIFORM SIGN DUG TIMES ASH FRONT in OGSL.
  "f": "AT LEFT",
  "90": "ROTATED NINETY DEGREES",
  "n": "NUTILLU",
  "180": "INVERTED",
  "h": "INVERTED",
  "v": "VARIANT",
}


def compute_expected_unicode_name_at(string, index, inner_plus):
  expected_unicode_name = ""
  i = index
  while i < len(string):
    c = string[i]
    if (i + 4 <= len(string) and
        string[i:i+3] == "LAK" and
        string[i+3].isdigit()):
      lak_number = 0
      i += 3
      while i < len(string) and string[i].isdigit():
        lak_number *= 10
        lak_number += int(string[i])
        i += 1
      expected_unicode_name += "LAK-%03d" % lak_number
      continue
    i += 1
    if c == "|":
      continue
    elif c == "(":
      opened = i-1
      (inner_sign, i) = compute_expected_unicode_name_at(string, i, inner_plus)
      if (string[i-1] != ")"):
        raise ValueError(f"unmatched parenthesis in {string},\n{string}\n{(opened)*' '+'('+(i-2-opened)*'~'+string[i-1]}")
      inner_sign = inner_sign.replace(".".join(3*["DISH"]), "THREE DISH")
      inner_sign = inner_sign.replace(".".join(3*["DISH TENU"]), "THREE DISH TENU")
      # Unicode uses PLUS for . in inner signs ×., thus
      # 𒌍 U.U.U is U U U but 𒀔 AB×(U.U.U) is AB TIMES U PLUS U PLUS U,
      # 𒀙 AB₂×(ME.EN) is AB₂ TIMES ME PLUS EN.
      # TODO(egg): It’s messier than that.  Clarify.
      expected_unicode_name += (inner_sign.replace(".", " PLUS ")
                                if inner_plus else
                                inner_sign.replace(".", " "))
    elif c == ")":
      break
    elif c == "Š":
      expected_unicode_name += "SH"
    elif c in "₀₁₂₃₄₅₆₇₈₉":
      expected_unicode_name += chr(ord("0") + ord(c) - ord("₀"))
    elif c == "%":
      expected_unicode_name += " CROSSING "
    elif c == "&":
      expected_unicode_name += " OVER "
    elif c in "+":
      expected_unicode_name += "."
    elif c == "×":
      expected_unicode_name += " TIMES "
    elif c == "@":
      ahead = name[i]
      if ahead.islower() or ahead.isdigit():
        if ahead.isdigit():
          ahead = ""
          while i < len(string) and name[i].isdigit():
            ahead += name[i]
            i += 1
        else:
          i += 1
        if ahead in MODIFIERS:
          expected_unicode_name += " " + MODIFIERS[ahead]
        else:
          raise ValueError(f"Unexpected modifier @{ahead} in {name}")
      else:
        expected_unicode_name += " OPPOSING "
    else:
      expected_unicode_name += c
  expected_unicode_name = re.sub("(^|\.)3 TIMES ([^.]*)", r"\1\2 THREE TIMES", expected_unicode_name)
  expected_unicode_name = re.sub("(^|\.)4 TIMES ([^.]*)", r"\1\2 SQUARED", expected_unicode_name)
  return (expected_unicode_name, i)


def compute_expected_unicode_name(string, inner_plus=True):
  # Unicode sometimes distributes & over ., but not always.
  if string == "|(KASKAL.LAGAB×U)&(KASKAL.LAGAB×U)|":
    string = "|(KASKAL&KASKAL).(LAGAB×U&LAGAB×U)|"
  name = compute_expected_unicode_name_at(string, 0, inner_plus)[0]
  return name.replace(".", " ") if inner_plus else name.replace(".", " PLUS ")


with open(r"..\ogsl\00lib\ogsl.asl", encoding="utf-8") as f:
  lines = f.read().split("\n")

sign_name = None
form_id = None
name = None
codepoints = None
sign_or_form_line = None
ucode_line = None
values = []

main_forms_by_name = {}
forms_by_name = {}

class Form:
  def __init__(self, name, form_id, sign, values, codepoints, sign_or_form_line=None, ucode_line=None, umap=None):
    self.name = name
    self.original_name = self.name
    self.form_id = form_id
    self.sign = sign
    self.values = values
    self.codepoints = codepoints
    self.original_codepoints = self.codepoints
    self.sign_or_form_line = sign_or_form_line
    self.ucode_line = ucode_line
    self.umap = umap
    self.lists = []

  def __str__(self):
    return (f"{self.name} {self.codepoints} (form {self.form_id} of {self.sign})"
            if self.form_id else f"{self.name} {self.codepoints}")

  def __repr__(self):
    return str(self)

i = 0
try:
  for line in lines:
    i += 1
    if line.strip().startswith("#"):
      continue
    tokens = re.split(r'[\t\x20]', line)
    if not tokens:
      continue
    if tokens[0] == "@sign" or tokens[0] == "@form" or tokens[:2] == ["@end", "sign"]:
      if name:
        if form_id:
          form = Form(name, form_id, main_forms_by_name[sign_name], values, codepoints, sign_or_form_line, ucode_line, umap)
        else:
          form = Form(name, form_id, None, values, codepoints, sign_or_form_line, ucode_line, umap)
          if name in main_forms_by_name and name not in ("LAK499", "LAK712"):  # TODO(egg): Deduplicate.
            raise ValueError(f"Duplicate signs {name}: {main_forms_by_name[name]} and {form}")
          main_forms_by_name[name] = form
        form.lists = lists
        if name in forms_by_name:
          forms_by_name[name].append(form)
        else:
          forms_by_name[name] = [form]
      name = None
      codepoints = None
      lists = []
      values = []
      sign_or_form_line = None
      ucode_line = None
      umap = None
    if tokens[0] == "@sign":
      if len(tokens) != 2:
        raise ValueError(tokens)
      name = tokens[-1]
      sign_name = tokens[-1]
      form_id = None
      sign_or_form_line = i
    if tokens[0] == "@form":
      if len(tokens) != 2 and not tokens[2][0] in ("x", "["):
        raise ValueError(tokens)
      name = tokens[-1]
      form_id = name
      sign_or_form_line = i
    if tokens[0] == "@list" and '"' not in tokens[1] and tokens[1] != "KWU":
      [list_name, number] = re.split(r"(?=\d)", tokens[1], 1)
      number = number.lstrip("0");
      if list_name == "U+":
        continue
      if list_name == "SLLHA":
        for l in ("ŠL", "MÉA"):
          lists.append(l + number)
      else:
        lists.append(list_name.replace("OBZL", "aBZL").replace("HZL", "ḪZL") + number)
    if tokens[0] == "@v":  # Excluding deprecated values @v-, as well as questionable @v? for now.
      if tokens[1].startswith("%") or tokens[1].startswith("#"):
        if tokens[1] in ("%akk", "%elx", "#nib", "#old", "#struck"):  # What do the # annotations mean?
          value = tokens[2]
        elif tokens[1] == "%akk/n":
          continue  # These values seem to be sumerograms in normalized Akkadian spelling, out of scope for now
        else:
          raise ValueError(tokens)
      elif '@' in tokens[1]:
        print(f"@ in value: {tokens}")
        continue
      else:
        if len(tokens) > 2 and not tokens[2].startswith("["):
          raise ValueError(tokens)
        value = tokens[1]
      if value.startswith("/") and value.endswith("/"):
        continue  # Not sure what the values between slashes are.
      if "-" in value and not value.endswith("-"):
        # Not sure what those values for sign sequences, e.g., e₆-a aš₇-gi₄, etc. are about; just type the components.
        continue
      if "°" in value:  # What is up with those ° and ·?
        if value not in ("za°rahₓ", "zu°liₓ"):
          raise ValueError(value)
        continue
      if "·" in value:
        if value not in ("za·rahₓ", "zu·liₓ"):
          raise ValueError(value)
        if value == "zu·liₓ":
          # 𒆠𒆪𒊕 has zarahₓ, but 𒆉 does not have zuliₓ (reading given in epsd though, e.g. http://oracc.museum.upenn.edu/epsd2/o0025193).
          value = "zuliₓ"
        else:
          continue
      if value in ("?", "x", "xₓ") or value.endswith("?"):
        continue
      if "[...]" in value or "x" in value:
        continue
      if value[0] in '1234567890' or value == "oo" or value == "::":
        continue  # We do numeric values by hand.
      if value in "dfm":
        # We do determinative shorthands by hand.
        continue
      if value in ("𒑱", ':"', ":.", ":"):
        # We do punctuation by hand.
        continue
      if value[0] == "{":
        continue  # Weird values with determinative markup?
      if value.endswith("@d"):
        continue  # @d in Elamite values anše@d and geštin@d.
      if value.endswith("+"):
        value = value[:-1] + "⁺"
      value = value.replace("'", "ʾ")

      values.append(value)
    if tokens[0] == "@ucun":
      ucode_line = i
      if len(tokens) != 2:
        raise ValueError(tokens)
      codepoints = tokens[-1]
      for c in codepoints:
        if ord(c) >= 0xE000 and ord(c) <= 0xF8FF:
          codepoints = None
          break
    if tokens[0] == "@umap":
      if len(tokens) != 2:
        raise ValueError(tokens)
      umap = tokens[1]
except Exception as e:
  print(f"line {i}:")
  print(line)
  print(e)
  raise

# Process umap.
for name, forms in forms_by_name.items():
  for form in forms:
    if form.umap:
      if form.codepoints:
        raise ValueError(f"{form} has umap and ucun")
      if form.umap not in forms_by_name:
        raise ValueError(f"{form} has umap to unknown {form.umap}")
      if not forms_by_name[form.umap][0].codepoints:
        raise ValueError(f"{form} has umap unencoded {forms_by_name[form.umap][0]}")
      form.codepoints = forms_by_name[form.umap][0].codepoints

for name, forms in forms_by_name.items():
  encodings = sorted(set(form.codepoints for form in forms if form.codepoints))
  if len(encodings) > 1:
    raise ValueError(f"Differing signs for name {name}: {forms}")
  if encodings:
    encoding = encodings[0]
    for form in forms:
      form.codepoints = encoding


def rename(old_name, new_name):
  forms = forms_by_name[old_name]
  for form in forms:
    form.name = new_name
  del forms_by_name[old_name]
  if new_name not in forms_by_name:
    forms_by_name[new_name] = []
  forms_by_name[new_name] += forms
  if old_name in main_forms_by_name:
    main_form = main_forms_by_name[old_name]
    del main_forms_by_name[old_name]
    if new_name in main_forms_by_name:
      raise ValueError(f"Renaming yields duplicate main forms {new_name}")
    main_forms_by_name[new_name] = main_form

def disunify(unified_names, new_forms):
  old_forms = []
  for unified_name in unified_names:
    forms = forms_by_name[unified_name]
    if len(forms) > 1:
      raise ValueError(f"Multiple forms {unified_name}: {forms}")
    old_forms.append(forms[0])
    if old_forms[-1].form_id:
      raise ValueError(f"{old_forms[-1]} is not a main form")
  old_values = sorted(set(value for old_form in old_forms
                          for value in old_form.values))
  new_values = sorted(set(value for new_form in new_forms
                          for value in new_form.values))
  if old_values != new_values:
    for i in range(max(len(old_values), len(new_values))):
      print(old_values[i] if i < len(old_values) else None,
            new_values[i] if i < len(new_values) else None)
    raise ValueError(f"{old_values} != {new_values}")
  for new_form in new_forms:
    other_values = set(value for other_form in new_forms
                             for value in other_form.values
                             if other_form != new_form)
    for value in new_form.values:
      if value in other_values:
        raise ValueError(f"Duplicate value {value}")
  for new_form in new_forms:
    if new_form.form_id:
      raise ValueError(f"{new_form} is not a main form")
    main_forms_by_name[new_form.name] = [new_form]
    forms_by_name[new_form.name] = [new_form]
  new_names = set(new_form.name for new_form in new_forms)
  if unified_name not in new_names:
    del main_forms_by_name[unified_name]
    del forms_by_name[unified_name]

# Unicode 7.0 disunifications.

rename("|NI.UD|", "NA₄")
rename("|IM.NI.UD|", "|IM.NA₄|")
rename("|NI.UD.EN|", "|NA₄.EN|")
rename("|NI.UD.KI|", "|NA₄.KI|")
rename("|NI.UD.KISIM₅×(U₂.GIR₂)|", "|NA₄.KISIM₅×(U₂.GIR₂)|")

disunify(["ERIN₂"],
         [Form("ERIN₂", None, None,
               ["erin₂", "erim", "erem", "eren₂", "nura", "nuri", "nuru",
                "rin₂", "rina₂", "sap₂", "ṣab", "ṣap", "ṣapa","zab", "zalag₂",
                "zap", "erena₂", "erina₂",
                # NABU 1990/12.
                "surₓ",
                # Note 𒋝 SIG; putting that there rather than with the UD-like
                # ones.
                "sigₓ",],
               "𒂟"),
          Form("PIR₂", None, None,
               [# MZL values; all homophones of 𒌓 UD.
               "pir₂", "bir₃", "hiš₃", "lah₂", "lih₂", "par₅", "per₂",
                # Other OGSL values; shoving them there, since they are
                # homophones of UD (or similar to them) and the ERIN₂ ones in
                # MZL are not.
                "udaₓ", "tam₅"],
               "𒎕")])

# Being numeric, eše₃ is disunified from either BAD or IDIM.
for form in forms_by_name["BAD"]:
  form.values = [value for value in form.values if value != "eše₃"]
for form in forms_by_name["IDIM"]:
  form.values = [value for value in form.values if value != "eše₃"]
main_forms_by_name["EŠE₃"] = Form("EŠE₃", None, None, ["eše₃"], "𒑘")
forms_by_name["EŠE₃"] = [main_forms_by_name["EŠE₃"]]

# OGSL naming bugs handled here.

# LAK207 looks to me like ŠE.HUB₂, not (ŠE&ŠE).HUB₂.
# Conventiently Unicode has the former and not the latter.
rename("|(ŠE&ŠE).HUB₂|", "|ŠE.HUB₂|")

## ASCII ugliness in form ~c |ŠU₂.3xAN| of |BAR.AN|.  OGSL correctly uses 3×AN everywhere else.
#rename("|ŠU₂.3xAN|", "|ŠU₂.3×AN|")

# ED, not decomposed in its Unicode name.  Other overdecomposed signs are
# handled below, but because of the ED garbling we actually rename this one.
# TODO(egg): It has no values, imbue it with GAN? http://oracc.museum.upenn.edu/dcclt/Q000024
rename("|AŠ.GAN|", "LAK062")

# Unicode 7.0 related things.

rename("|HI.GIR₃|", "HUŠ")

rename("|ME.U.U.U|", "MEŠ")
for name in list(forms_by_name.keys()):
  if "ME.U.U.U" in name:
    rename(name, name.replace("ME.U.U.U", "MEŠ"))

rename("|SAL.TUG₂|", "NIN")
for name in list(forms_by_name.keys()):
  if "SAL.TUG₂" in name and name != "|GU₂×(SAL.TUG₂)|":
    rename(name, name.replace("SAL.TUG₂", "NIN"))

rename("|SAL.KU|", "NIN₉")

# OGSL encoding bugs handled here.
for name, forms in forms_by_name.items():
  for form in forms:
    if name == "LAK212":
      form.codepoints = "𒀷"

    if form.codepoints and form.name in ("|ŠU.DI.U.U.U|",
                                         "|ŠU.U.U.U.DI|",
                                         "|U.U.U.AŠ₃|",
                                         "|ŠU₂.U.U.U|",
                                         "|U.U.HUB₂|"):
      form.codepoints = form.codepoints.replace("𒌋𒌋𒌋", "𒌍")
      form.codepoints = form.codepoints.replace("𒌋𒌋", "𒎙")

    # Unicode and OGSL have both  𒋲 4×TAB and 𒅄 4×(IDIM&IDIM), with the same
    # values, namely burₓ, buruₓ, gurinₓ, gurunₓ, and kurunₓ.
    # 4×TAB has an @inote field
    #   #CHECK is this the same as |4×(IDIM&IDIM)|?
    # OGSL further has 4×IDIM with the values burₓ, buruₓ, gurinₓ, gurun₅, kurunₓ,
    # which also appears as part of PAP.PAP.4×IDIM.
    # The epsd2 uses 4×TAB http://oracc.museum.upenn.edu/epsd2/o0029082, and it
    # is attested in http://oracc.iaas.upenn.edu/dcclt/nineveh/P395694.
    # The epsd2 also uses 4×IDIM,
    # http://oracc.museum.upenn.edu/epsd2/cbd/sux/o0040043.html, it is
    # attested in http://oracc.iaas.upenn.edu/dcclt/nineveh/P365399 and also in
    # http://oracc.museum.upenn.edu/dcclt/signlists/X003882.21.2#X003882.16.
    # I was unable to find usages of 4×(IDIM&IDIM) as such.
    # Šašková uses that codepoint for 4×IDIM in her Sinacherib font, see
    # http://home.zcu.cz/~ksaskova/Sign_List.html.
    # We answer the @inote in the affirmative, and consider that 4×(IDIM&IDIM)
    # is actually just 4×TAB (it has the same values, and isn’t actually used
    # anyway).  We further follow usage established by Šašková and repurpose
    # that codepoint as 4×IDIM.
    # TODO(egg): ask Tinney whether that makes sense, and if it does, write a
    # proposal to add IDIM SQUARED as an alias for IDIM OVER IDIM SQUARED and to
    # change the reference glyph.
    if name == "|4×(IDIM&IDIM)|":
      form.codepoints = None
    elif name == "|4×IDIM|":
      form.codepoints = "𒅄"
    elif name == "|PAP.PAP.4×IDIM|":
      form.codepoints = form.codepoints.replace("X", "𒅄")


    # Signs that are not really there, one way or another.
    if name == "|DAG.KISIM₅×X|" or name == "|NUNUZ.AB₂×X|":
      form.codepoints = None  # If it has an X it is not encoded.
    if name == "|IM.IM.KAD₃IM.KAD₃A|":
      # What is that supposed to be? |IM.IM.KAD₃.IM.KAD₃A|?
      # In any case they have IM.A there…
      form.codepoints = None
    if name == "|LU₂@g.UŠ₂|":
      # No LU₂ gunû…
      form.codepoints = None
    if name == "|PAP.PAP×ŠE|":
      # No PAP×ŠE afaict?
      form.codepoints = None
    if name == "|SU.RU×KUR|":
      # RU×KUR removed in https://www.unicode.org/wg2/docs/n2786.pdf.
      # The @ucode for that sign only has SU, and SU.KUR.RU exists so a font
      # could ligature it.
      form.codepoints = None

    # Aggressively unifying numbers.
    # There is another |AŠ.AŠ| as form ~c of |AN.AŠ.AN|, with the value tillaₓ;
    # let’s not use 2(AŠ) there.
    if name == "|AŠ.AŠ|" and "min₅" in values:
      form.codepoints = "𒐀"
    if name == "|AŠ.AŠ.AŠ|":
      form.codepoints = "𒐁"
    if name == "|TAB.AŠ|":
      form.codepoints = "𒐻"
    if name == "|AŠ&AŠ&AŠ|":
      # TODO(egg): This also has the value šušur which seems unrelated to the
      # (numeric) value eš₁₆; maybe šušur should be AŠ&AŠ&AŠ 𒀼?
      form.codepoints = "𒐺"
    if name == "LIMMU₂":
      # TODO(egg): Why is 𒇹 separate from 𒐂?  Unifying.
      form.codepoints = "𒐂"
    if name == "|AŠ&AŠ&AŠ.AŠ|":
      form.codepoints = "𒐽"
    if name == "|TAB.TAB.AŠ|":
      form.codepoints = "𒐃"
    if name == "|TAB.TAB.TAB|":
      form.codepoints = "𒐄"
    if name == "|AŠ&AŠ&AŠ.AŠ&AŠ&AŠ|":
      form.codepoints = "𒑀"
    if name == "|AŠ&AŠ&AŠ.AŠ&AŠ&AŠ.AŠ|":
      form.codepoints = "𒑁"
    if name == "|TAB.TAB.TAB.AŠ|":
      form.codepoints = "𒐅"
    if name == "|TAB.TAB.TAB.TAB|":
      form.codepoints = "𒐆"
    if name == "|AŠ&AŠ&AŠ.AŠ&AŠ&AŠ.TAB|":
      form.codepoints = "𒑅"
    if name == "|TAB.TAB.TAB.TAB.AŠ|":
      form.codepoints = "𒐇"
    if name == "IMIN":
      form.codepoints = "𒐌"
    if name == "|DIŠ.DIŠ.DIŠ|":
      form.codepoints = "𒐈"
    if name == "|DIŠ.DIŠ.DIŠ.U.U|":
      form.codepoints = "𒐈𒎙"
    if name == "|DIŠ.DIŠ.DIŠ.U.U.U|":
      form.codepoints = "𒐈𒌍"

    # Unicode 7.0 fanciness, except disunifications.
    if "NI.UD" in name:
      raise ValueError(f"NI.UD in {form}")

# Assign encodings from components.
for name, forms in forms_by_name.items():
  if name.startswith("|") and name.endswith("|") and not forms[0].codepoints:
    encoding = ""
    components = []
    for component in re.findall(r"(?:[^.()]|\([^()]+\))+", name[1:-1]):
      if "×" in component or "%" in component or "&" in component:
        component = f"|{component}|"
      if component in forms_by_name and forms_by_name[component][0].codepoints:
        encoding += forms_by_name[component][0].codepoints
        components.append(component)
      else:
        break
    else:
      if encoding:
        print(f"WARNING: {name} has no ucun but it can be derived as {encoding} from {components}")
      for form in forms:
        form.codepoints = encoding
      print(f"Encoding {forms[0] if len(forms) == 1 else forms} from {components}")


for name, forms in forms_by_name.items():
  encoding = forms[0].codepoints
  if not encoding:
    continue

  if 'X' in encoding:
    continue

  if name == "ASAL₂~a":
    # Very weird entry and very weird Unicode name.  Merging with LAK 212,
    # see above.
    continue

  if name == "|LAGAB×(IM.IM.ŠU₂LU)|":
    # Very explicitly mapped to CUNEIFORM SIGN LAGAB TIMES IM PLUS LU.
    # |LAGAB×(IM.LU)| exists as a variant of elamkuš₂ but is given no readings.
    # This one has elamkušₓ, which seems appropriate.
    continue

  if name == "|LAGAB×AŠ@t|":
    # The unicode name is LAGAB×LIŠ, which is variant ~a of this one.
    # Both are given the reading gigir₃.  Shrug.
    continue

  if name== "OO" or name=="O":
    continue

  expected_unicode_name = compute_expected_unicode_name(name)

  if expected_unicode_name == "PESH2~v":
    expected_unicode_name = "PESH2 ASTERISK"

  # Misnaming in Unicode? U+12036 ARKAB 𒀶 is (looking at the reference
  # glyph) LAK296, to which OGSL gives the value arkab₂, arkab being
  # GAR.IB 𒃻𒅁.
  expected_unicode_name = expected_unicode_name.replace("ARKAB2", "ARKAB")

  # OGSL decomposes 𒍧 and 𒍦, Unicode does not (perhaps for length reasons?).
  expected_unicode_name = expected_unicode_name.replace(
      " OVER ".join(4 * ["ASH KABA TENU"]),
      "ZIB KABA TENU")
  expected_unicode_name = expected_unicode_name.replace(
      " OVER ".join(4 * ["ASH ZIDA TENU"]),
      "ZIB")

  if expected_unicode_name == "BURU5":
    # Quoth the OGSL: @note The NB source for Ea II (LKU 1) describes BURU₅ as NAM nutillû.
    expected_unicode_name = "NAM NUTILLU"

  if expected_unicode_name == "ELLES396":
    # The unicode name is a value here rather than the catalogue number.
    expected_unicode_name = "ZAMX"

  # OGSL never decomposes LAL₂, so lets’ treat this as intentional.
  expected_unicode_name = expected_unicode_name.replace("LAL2", "LAL TIMES LAL")

  if expected_unicode_name == "SHAR2 TIMES U":
    expected_unicode_name = "HI TIMES U"

  if expected_unicode_name == "URU TIMES MIN TIMES IGI":
    expected_unicode_name = "LAK-648 TIMES IGI"

  if expected_unicode_name == "KU4~a":
    expected_unicode_name = "KU4 VARIANT FORM"

  if expected_unicode_name == "LAGAB TIMES SHITA TENU PLUS GISH":
    expected_unicode_name = "LAGAB TIMES SHITA PLUS GISH TENU"

  # The reference glyph is more over than plus…
  if expected_unicode_name == "LAGAB TIMES GUD OVER GUD":
    expected_unicode_name = "LAGAB TIMES GUD PLUS GUD"
  if expected_unicode_name == "PA LAGAB TIMES GUD OVER GUD":
    expected_unicode_name = "PA LAGAB TIMES GUD PLUS GUD"
  if expected_unicode_name == "SAL LAGAB TIMES GUD OVER GUD":
    expected_unicode_name = "SAL LAGAB TIMES GUD PLUS GUD"
  if expected_unicode_name == "LAGAB TIMES GUD OVER GUD A":
    expected_unicode_name = "LAGAB TIMES GUD PLUS GUD A"
  if expected_unicode_name == "LAGAB TIMES GUD OVER GUD HUL2":
    expected_unicode_name = "LAGAB TIMES GUD PLUS GUD HUL2"

  # OGSL has no MA×TAK₄, Unicode has no MA GUNU TIMES TAK4.
  # This is probably fine, though I don’t know where the gunû went.
  if expected_unicode_name == "MA GUNU TIMES TAK4":
    expected_unicode_name = "MA TIMES TAK4"

  if expected_unicode_name == "MURUB4":
    # @note MURUB₄(LAK157) merges with NISAG(LAK159)
    expected_unicode_name = "NISAG"

  if expected_unicode_name == "DE2":
    # See above.
    expected_unicode_name = "UMUM TIMES KASKAL"

  # Various variants.
  if expected_unicode_name == "TA VARIANT":
    expected_unicode_name = expected_unicode_name.replace("VARIANT", "ASTERISK")
  if expected_unicode_name == "U OVER U U VARIANT OVER U VARIANT":
    expected_unicode_name = expected_unicode_name.replace("VARIANT", "REVERSED")
  if expected_unicode_name == "KAP0":
    expected_unicode_name = "KAP ELAMITE"

  # Aliases from https://www.unicode.org/wg2/docs/n4277.pdf.
  # Looking up by alias work, but the name is the name, and there is no API to
  # get the alias...
  if expected_unicode_name == "NU11 TENU":
    expected_unicode_name = "SHIR TENU"
  if expected_unicode_name == "NU11 TENU SILA3":
    expected_unicode_name = "SHIR TENU SILA3"
  elif expected_unicode_name == "NU11 OVER NU11 BUR OVER BUR":
    expected_unicode_name = "SHIR OVER SHIR BUR OVER BUR"

  # See the discussion above.  Maybe someday this will be an alias...
  if "IDIM SQUARED" in expected_unicode_name:
    expected_unicode_name = expected_unicode_name.replace("IDIM SQUARED", "IDIM OVER IDIM SQUARED")

  # Probably a misnomer in Unicode.
  if expected_unicode_name == "LAK-212":
    expected_unicode_name = "ASAL2"

  # Not decomposed in Unicode.
  expected_unicode_name = expected_unicode_name.replace("SHE NUN OVER NUN", "TIR")
  expected_unicode_name = expected_unicode_name.replace("SHE PLUS NUN OVER NUN", "TIR")



  # Quirky Unicode 7.0 names.
  # Unicode has KU3 but AMAR TIMES KUG.
  if expected_unicode_name == "AMAR TIMES KU3":
    expected_unicode_name = "AMAR TIMES KUG"
  # Similarly DUN but KA TIMES SHUL.
  if expected_unicode_name == "KA TIMES DUN":
    expected_unicode_name = "KA TIMES SHUL"
  # And SIX DISH but KA TIMES ASH3.
  if expected_unicode_name == "KA TIMES 6DISH":
    expected_unicode_name = "KA TIMES ASH3"

  # Sometimes (but not always) decomposed in OGSL, not decomposed in Unicode.
  if expected_unicode_name == "SHU2 DUN3 GUNU GUNU SHESHIG":
    expected_unicode_name = "SHU2 DUN4"

  # ED oddities.
  if expected_unicode_name == "SAG TIMES TAK4 AT LEFT":
    # LAK 310 in the OGSL and in N4278, despite the different description.
    expected_unicode_name = "TAK4 PLUS SAG"
  if expected_unicode_name == "SAR TIMES SHE":
    # LAK 216 in the OGSL and in N4278, despite the different description.
    expected_unicode_name = "SHE PLUS SAR"
  if expected_unicode_name == "URU GUNU":
    # The mangled @ucode entry matched URU TIMES LU3 in N4179, and the reference
    # glyph seems close enough to https://cdli.ucla.edu/dl/photo/P226011.jpg
    # referenced in the @note.
    expected_unicode_name = "URU TIMES LU3"
  if expected_unicode_name == "SHE VARIANT NAM2":
    # At some point prior to N4179 the word variant was lost.
    # The @uname entry has SHE VARIANT FORM JOINING NAM2.
    expected_unicode_name = "SHE PLUS NAM2"
  if expected_unicode_name == "KA TIMES SHE AT LEFT":
    # At some point prior to N4179 this was renamed; note the typo in N4179
    # which has SANG for SAG.
    expected_unicode_name = "SAG TIMES SHE AT LEFT"

  actual_unicode_name = " ".join(unicodedata.name(c).replace("CUNEIFORM SIGN ", "") if ord(c) >= 0x12000 else c for c in encoding)
  if ("CUNEIFORM NUMERIC SIGN" in actual_unicode_name or
      "CUNEIFORM PUNCTUATION SIGN" in actual_unicode_name):
    continue  # TODO(egg): deal with that.

  if expected_unicode_name == "SHU OVER SHU INVERTED":  # Magical Unicode word order.
    expected_unicode_name = "SHU OVER INVERTED SHU"

  if expected_unicode_name == "SILA3 LAK-449a":  # Newly identified interior structure.
    expected_unicode_name = "LAK-450"

  # TODO(egg): Figure out the PLUS dance someday...
  if actual_unicode_name.replace(" PLUS ", " ") != expected_unicode_name.replace(" PLUS ", " "):
    raise ValueError(f"{name} encoded as {encoding}, {expected_unicode_name} != {actual_unicode_name}")


encoded_forms_by_value = {}
encoded_forms_by_list_number = {}

for name, forms in forms_by_name.items():
  encoding = forms[0].codepoints
  if encoding and all(ord(c) >= 0x12000 for c in encoding):
    for form in forms:
      for value in form.values:
        if value not in encoded_forms_by_value:
          encoded_forms_by_value[value] = {}
        if encoding not in encoded_forms_by_value[value]:
          encoded_forms_by_value[value][encoding] = []
        encoded_forms_by_value[value][encoding].append(form)
      for list_number in form.lists:
        encoded_forms_by_list_number.setdefault(list_number, {}).setdefault(encoding, []).append(form)

for name, forms in forms_by_name.items():
  values = [value for form in forms for value in form.values]
  unencoded_basic_values = [
      value for value in values
      if re.match("^[bdgptkʾṭqzšsṣhmnrlwyaeiu]{1,3}[₁₂₃₄₅₆₇₈₉₀]?$", value) and
      value not in encoded_forms_by_value]
  if values and not forms[0].codepoints and unencoded_basic_values:
    print(f"No encoding for {name} with values {values}; "
          f"{unencoded_basic_values} not otherwise encoded")

for value, forms_by_codepoints in encoded_forms_by_value.items():
  main_forms = [form for encoding, forms in forms_by_codepoints.items()
                for form in forms if not form.form_id]
  if "ₓ" not in value and len(forms_by_codepoints) > 1:
    if len(main_forms) > 1:
      raise ValueError(f"Multiple main forms with non-ₓ value {value}: {main_forms}")
    elif not main_forms:
      #print(f"Multiple variant forms and no main form with non-ₓ value {value}: {forms_by_codepoints.values()}")
      pass
    else:
      #print(f"Multiple forms (one main) with non-ₓ value {value}: {forms_by_codepoints.values()}")
      pass

for value, forms_by_codepoints in encoded_forms_by_value.items():
  for c in value:
    if c not in 'bdgptkʾṭqzšsṣhmnrlwyaeiu₁₂₃₄₅₆₇₈₉₀ₓŋ⁺⁻ś':  # Oracc uses h for ḫ, y for j.
      print(forms_by_codepoints.values())
      raise ValueError(f"Unexpected character {c} in value {value} for {'; '.join(forms_by_codepoints.keys())}")
      break

encoded_signs = {form.codepoints: form for forms in forms_by_name.values() for form in forms}
encoded_signs_with_list_numbers = {form.codepoints: form.lists for forms in forms_by_name.values() for form in forms if form.lists}
encoded_signs_with_values = {form.codepoints: form.values for forms in forms_by_name.values() for form in forms if form.values}

NON_SIGNS = set((
  # @nosign |A×GAN₂@t|
  # @note LAK refers to CT 7, 32b which has zah₃ (line 3; collated from photograph)
  # Note: zah₃ is A×HA 𒀄.
  "𒀃",
  # @nosign KUL@g
  # @note Does this sign exist? Not found in LAK, Krebernik OBO 160/1, ELLES, ARES 4. Does not seem to represent LAK20 (related to BALA, not to KUL).
  # Note: LAK20 seems unencoded, see above; maybe it *is* that, misnamed.
  "𒆱",
  # No reference to SAG×TAB nor to U+122A1 in the OGSL.
  "𒊡",
  # @nosign UŠUMX
  # @note KWU089 is a by-form of MUŠ (not related to BUR₂). 𒍘
  # @v- ušumₓ
  # Note: MUŠ is 𒈲, BUR₂ is 𒁔.
  # But see https://cdli.ucla.edu/search/archival_view.php?ObjectID=P212207,
  # https://books.google.fr/books?id=gkJRhioLVOIC&lpg=PA134&ots=rnchJ9pnlo&dq=%22U%C5%A0UMX%22&hl=fr&pg=PA134#v=onepage&q=%22U%C5%A0UMX%22&f=false?
  # It probably isn’t KWU089 contrary to Koslova, but the variant of 𒁔, consistent with both the name and the reference glyph,
  # exists—whether it deserved its own codepoint is another question…
  "𒍘",
  # MZL811, with explanations given at MZL748 𒁹:
  # 60šu, šuššu^šu resp. 60+šu, šuššu^+šu, the number 60.
  # Borgers writes this can be transcribed 60(KU) in assyrian, but differs from
  # KU in babylonian.  This is probably why we have a separate codepoint.
  # See CAD, entry šūši.
  # Numeric, so let’s handle that separately.
  #"𒍵",
  # A misreading of MZL for gaz₃, and gaz₃ itself.
  # See https://github.com/oracc/ogsl/pull/7#issuecomment-1304608990.
  "𒁿", "𒍶",
  # No idea where that comes from.  Maybe look for it HethZL?
  "𒍾",
  # No idea for that one either.
  "𒎁",
  "𒎅",
  # MZL741, variant of MZL882.  Not clear how it differs, does it have the same
  # values?  Does it only have a specific logographic value like TA*?  Punt for
  # now.
  # "𒎔",
  # MZL488, a variant of 𒌝𒈨.
  # TODO(egg): should it take its place (and should the UM.ME rendition be a
  # matter for the font?)
  #"𒎘",
  # Unified in favour of the numeric versions.
  "𒀼", "𒅓", "𒇹",
  "𒊪", # Turned into a @nosign with: @inote unicode revision needed/deleted; sign is |ZUM×TUG₂| = LAK524.
  "𒍴", # Baffling disunification.
  # EZEN×ḪA@g: https://oracc.iaas.upenn.edu/dcclt/signlists/P365252?P365252.57
  # MSL 14, 497 A1.
  # MZL 291 (EZEN×ḪA) cites MSL 14 497 101 (? Lw. z.T. abgebrochen).
  # https://www.britishmuseum.org/collection/object/W_1880-1112-11, no photo.
  "𒂪",
  "𒃀", # GA₂×(BAR.RA) eburra? gaburraₓ?  ???
  "𒃬", # GA₂×(UD.DU) [...]e  ???
  # GABA%GABA: http://oracc.iaas.upenn.edu/dcclt/P368988?P368988.22,P368988.23#P368988.17
  # MSL 14 484.
  # MZL does cite it for other signs, but does not mention this.
  "𒃯",
  "𒄺", # HUB₂×HAL. ???
  "𒄼", # HUB₂×LIŠ. ???
  "𒅟", # KA×BI. ???
  # KA×GI. DCCLT ED Metals; even in MEE 03, 026:
  # http://oracc.iaas.upenn.edu/dcclt/P240968/ o vi 8 sqq.
  # But ELLes has 26 r. VI 8 at ELLes 182 = LAK 318, normal 𒅗.
  "𒅧",
  "𒅳",  # KA×LU pu-udu.  ???
  "𒅹",  # KA×(MI.NUNUZ). ???
  # KA₂×KA₂: http://oracc.museum.upenn.edu/dcclt/signlists/P391514?P391514.7#P391514.2
  # MSL 14, 353 A
  "𒆎",
  "𒆖", # KAK×IGI@g. ???
  # LAGAB×ME: http://oracc.museum.upenn.edu/dcclt/signlists/P365261?P365261.140,
  # variant form of LAGAB×A.
  # MSL 14, 207 A.  Note the transliteration LAGAB×A is inconsistent with the copy.
  # Also LAGAB×ME in LAGAB×ME.EN http://oracc.iaas.upenn.edu/dcclt/signlists/Q000145?Q000145.173
  # But not in the score; could it be LAGAB×(ME.EN)?
  "𒇘",
  # [...]tallu. https://oracc.museum.upenn.edu/dcclt/P258842?P258842.46
  # MSL 14, pp. 461—65.
  "𒈍",
  "𒊛", # SAG×KUR http://oracc.museum.upenn.edu/dcclt/signlists/P230117.5.3
  "𒌭", # UR₂×(A.NA). ???
  "𒌳", # UR₂×(U₂.BI) ar[...]. https://oracc.museum.upenn.edu/dcclt/P258842?P258842.140
  "𒍅", # URU×KI https://oracc.museum.upenn.edu/dcclt/P345354?P345354.399
  "𒍆", # URU×LUM ???
  "𒎆", # KA×TU, variant form of šeg₅ e.g. in http://oracc.iaas.upenn.edu/dcclt/Q003221/
  "𒎍", # MUŠ₃×ZA, variant form of something.
))

for u in range(0x12000, 0x12550):  # Cuneiform, Cuneiform numbers and punctuation, Early Dynastic cuneiform.
  if unicodedata.category(chr(u)) == "Cn":
    continue
  if unicodedata.name(chr(u)).startswith("CUNEIFORM NUMERIC SIGN"):
    continue
  if unicodedata.name(chr(u)).startswith("CUNEIFORM PUNCTUATION SIGN"):
    continue
  if chr(u) in NON_SIGNS:
    if chr(u) in encoded_signs_with_values:
      raise KeyError(f"""Non-sign U+{u:X} {
        unicodedata.name(chr(u))} {chr(u)} has values {
        encoded_signs_with_values[chr(u)]}""")
    if chr(u) in encoded_signs_with_list_numbers:
      raise KeyError(f"""Non-sign U+{u:X} {
        unicodedata.name(chr(u))} {chr(u)} has list numbers {
        encoded_signs_with_list_numbers[chr(u)]}""")
    continue
  if chr(u) not in encoded_signs:
    raise KeyError(f"No form U+{u:X} {unicodedata.name(chr(u))} {chr(u)}")
  if (chr(u) not in encoded_signs_with_values and
      chr(u) not in encoded_signs_with_list_numbers):
    message = f"""Neither form nor list number for U+{u:X} {
        unicodedata.name(chr(u))} {chr(u)} {encoded_signs[chr(u)]}"""
    if u >= 0x12480:
      print("ED: " + message)
    else:
      raise KeyError(message)

compositions = {}

for value, forms_by_codepoints in sorted(encoded_forms_by_value.items()):
  normalized_value = ""
  for c in value:
    if c in "₀₁₂₃₄₅₆₇₈₉":
      normalized_value += chr(ord("0") + ord(c) - ord("₀"))
    elif c == "ₓ":
      normalized_value += "x"
    elif c == "h":
      normalized_value += "ḫ"
    elif c == "y":
      normalized_value += "j"
    elif c == "⁺":
      normalized_value += "+"
    elif c == "⁻":
      normalized_value += "-"
    else:
      normalized_value += c
  main_form_encodings = [form.codepoints for encoding, forms in forms_by_codepoints.items()
                          for form in forms if not form.form_id]
  form_index = 0
  for encoding, forms in forms_by_codepoints.items():
    if "ₓ" in value or (
        len(forms_by_codepoints) > 1 and (
            encoding not in main_form_encodings or
            len(main_form_encodings) != 1)):
      form_index += 1
      compositions.setdefault(f"{normalized_value}v{form_index}", []).append(encoding)
    else:
      compositions.setdefault(normalized_value, []).append(encoding)


for list_number, forms_by_codepoints in encoded_forms_by_list_number.items():
  composition = "x" + list_number.lower().replace("é", "e").replace("c", "š").replace("hzl", "ḫzl").replace("'", "ʾ")
  if not re.match(r"^[bdgptkʾṭqzšsṣḫmnrlwyaeiuŋśaeui0-9xf]+$", composition):
    print("Weird characters in list number %s" % list_number)
    continue
  main_form_encodings = [form.codepoints for encoding, forms in forms_by_codepoints.items()
                          for form in forms if not form.form_id]
  form_index = 0
  for encoding, forms in forms_by_codepoints.items():
    if len(forms_by_codepoints) > 1:
      form_index += 1
      compositions.setdefault(f"{composition}v{form_index}", []).append(encoding)
    else:
      compositions.setdefault(composition, []).append(encoding)

for composition, encoding in numbers.compositions.items():
  compositions.setdefault(composition, []).append(encoding)


# Punctuation, common determinatives, edge cases.
for encoding, composition in {
    # MesZL 592.
    '𒑱' : ':',
    # MesZL 576: Trennungszeichen (wie n592; Umschrift :).  Disunified from GAM
    # in Unicode.
    '𒑲' : ':v1',
    # MesZL 577: Trennungs- und Wiederholungszeichen (Umschrift mit Parpola,
    # LASEA pXX ⫶).  Disunified from ILIMMU4 in Unicode.
    '𒑳' : '⫶',
    # Word divider.  See MesZL 748, p. 418: In Kültepe wird ein senkrechter Keil
    # als Worttrenner gebraucht.  Disunified from DIŠ in Unicode.
    # See AAA 1/3, 01 for an example usage:
    # https://cdli.ucla.edu/search/archival_view.php?ObjectID=P360975.
    # We use a transliteration inspired by CDLI’s, a forward slash; however we
    # use that for the normal word divider ZWSP as well, making the OA one v1.
    '𒑰' : '/v1',
    '\u200B': '/',
    # Determinatives for personal names and gods.
    '𒁹' : 'm',
    '𒊩' : 'f',
    '𒀭' : 'd',
    '𒍵' : '60šu',  # See above.
    '𒋬' : 'tav1',  # Variant of TA with a specific logographic value (ištu).
  }.items():
  compositions.setdefault(composition, []).append(encoding)

# Uniqueness of compositions.
for composition, encodings in compositions.items():
  if len(encodings) != 1:
    raise ValueError(f"Multiple signs with composition {composition}: {encodings}")

# Sanity check of numbers: 1meow and meow must map to the same sign.
for composition, encodings in compositions.items():
  if re.match('^1\D', composition):
    if composition[1:] in compositions:
      if encodings[0] != compositions[composition[1:]][0]:
        if composition in ('1iku', "1šargal"):
          # Borger gives iku as a reading for 𒃷 in 𒀸𒃷.  Friberg sees that as
          # a determinative, and transcribes it 1iku GAN2.  Shrug.
          # Conversely our šargal numerals contain the 𒃲.
          continue
        raise ValueError(f"Inconsistent numeric readings: {composition}={encodings[0]},"
                         f" {composition[1:]}={compositions[composition[1:]][0]}")

for filename, encoding in (("sign_list.txt", "utf-16"),
                           ("sign_list.utf-8.txt", "utf-8")):
  with open(fr".\Samples\IME\cpp\SampleIME\Dictionary\{filename}",
            "w", encoding=encoding) as f:
    for composition, encodings in sorted(compositions.items()):
      print(f'"{composition}"="{encodings[0]}"', file=f)
