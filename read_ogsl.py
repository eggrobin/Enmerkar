import sys
import re
import codecs
import unicodedata

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
values = []

main_forms_by_name = {}
forms_by_name = {}

class Form:
  def __init__(self, name, form_id, sign, values, codepoints):
    self.name = name
    self.form_id = form_id
    self.sign = sign
    self.values = values
    self.codepoints = codepoints

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
    tokens = line.split()
    if not tokens:
      continue
    if tokens[0] == "@sign" or tokens[0] == "@form" or tokens[:2] == ["@end", "sign"]:
      if name:
        if form_id:
          form = Form(name, form_id, main_forms_by_name[sign_name], values, codepoints)
        else:
          form = Form(name, form_id, None, values, codepoints)
          if name in main_forms_by_name:
            raise ValueError(f"Duplicate signs {name}: {main_forms_by_name[name]} and {form}")
          main_forms_by_name[name] = form
        if name in forms_by_name:
          forms_by_name[name].append(form)
        else:
          forms_by_name[name] = [form]
      name = None
      codepoints = None
      values = []
    if tokens[0] == "@sign":
      if len(tokens) != 2:
        raise ValueError(tokens)
      name = tokens[-1]
      sign_name = tokens[-1]
      form_id = None
    if tokens[0] == "@form":
      if len(tokens) != 3 and not tokens[3][0] in ("x", "["):
        raise ValueError(tokens)
      name = tokens[-1]
      form_id = tokens[1]
    if tokens[0] == "@v":  # Excluding deprecated values @v-, as well as questionable @v? for now.
      if tokens[1].startswith("%") or tokens[1].startswith("#"):
        if tokens[1] in ("%akk", "%elx", "#nib", "#old", "#struck"):  # What do the # annotations mean?
          value = tokens[2]
        elif tokens[1] == "%akk/n":
          continue  # These values seem to be sumerograms in normalized Akkadian spelling, out of scope for now.
        else:
          raise ValueError(tokens)
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
      if "[...]" in value:
        continue
      if value[0] in '1234567890' or value == "oo":
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
    if tokens[0] == "@ucode":
      if len(tokens) != 2:
        raise ValueError(tokens)
      codepoints = ''.join((x if x in ("X", "None") else chr(int("0" + x, 16)) for x in tokens[-1].split(".")))
      for c in codepoints:
        if ord(c) >= 0xE000 and ord(c) <= 0xF8FF:
          codepoints = None
          break
except Exception as e:
  print(f"line {i}:")
  print(line)
  print(e)
  raise

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

disunify(["|NI.UD|"],  # Listed as MZL385 in OGSL.
         [Form("DAG₃", None, None,
               ["dag₃", "bar₄", "dak₃", "daq₃", "par₇", "tak₃", "taq₃"],  # MZL386.
               "𒍴"),
          Form("NA₄", None, None,
               ["na₄", "i₄", "ia₄", "za₂",  # MZL385.
               "ya₄",  # OGSL, probably goes with ia₄.
               # na₄ = abnu, https://oracc.iaas.upenn.edu/dcclt/Q000091,
               # http://classes.bnf.fr/ecritures/grand/e029.htm.
               "abnu",
               # In https://oracc.iaas.upenn.edu/dcclt/signlists/P370411 next to
               # other na₄ values (and no dag₃ values).
               "aban", "atumₓ",
               ],
               "𒎎")])
rename("|IM.NI.UD|", "|IM.NA₄|")
rename("|NI.UD.EN|", "|NA₄.EN|")
rename("|NI.UD.KI|", "|NA₄.KI|")

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

# The history of ḪI, ŠÁR, TÍ, and DIN is confusing; as usual with these
# questions one should look at Labat.
# This section must be read with the glyphs in Noto.
# There are three ancestral forms (archaic & classical Sumerian columns in
# Labat), 𒄭 ḪI & 𒊹 ŠÁR (MÉA396), and 𒁷 DIN (MÉA465).
# 𒁷 acquires the value TÍ in OAkk times, see MZL119.
# See e.g. this UR III tablet https://cdli.ucla.edu/search/archival_view.php?ObjectID=P131069.
# 𒁷-with-the-value-TÍ then undergoes a change in glyph, and looks like 𒎗 in
# Assyrian (Labat lists it in 𒆍𒀭𒊏𒆠 only in NB).
# Meanwhile 𒁷-with-the-values-DIN &c. undergoes different changes, and despite
# a couple appearances of 𒎗-like DIN in OB/MB, it diverges and ends up looking
# like 𒌋𒁹𒌋 on top of 𒀸 in NA (I will refer to it as 𒌋𒁹𒌋 below due to the limits
# of plain text).
# Meanwhile 𒄭 and 𒊹 converge, first to something like 𒄭, then by MA/MB to 𒎗,
# so that from those three ancestors two glyphs remain in NA, 𒎗 for ḪI, ŠÁR, TÍ,
# and 𒌋𒁹𒌋 for DIN.
# In terms of encoding, this however requires four characters:
# ḪI 𒄭, ŠÁR 𒊹, TÍ 𒎗, and DIN 𒁷, where the glyphs should be
# γλ(TÍ)=γλ(DIN)=𒁷 in OAkk,  γλ(ḪI)=𒄭, γλ(ŠÁR)=𒊹, then quickly
# γλ(ḪI)=γλ(ŠÁR)=𒄭, as is the case, e.g., in
# https://cdli.ucla.edu/search/archival_view.php?ObjectID=P142654,
# and by NA γλ(DIN)=𒌋𒁹𒌋≠γλ(ḪI)=γλ(ŠÁR)=γλ(TÍ)=𒎗.
# The OGSL predates the separate encoding of TÍ 𒎗, so its values (notably tí)
# are found both in the entries for DIN and ḪI.
# The following surgery deals with that.
disunify(["DIN", "HI"],
         [Form("DIN", None, None,
               # All OGSL values for DIN except ti₂ and di₂.
               ["den", "din", "dini", "gurun₈", "kurun₂", "ten₂", "tim₃", "tin",
                "ṭen"],
               "𒁷"),
          Form("TI₂", None, None,
               # Values given in MÉA396, 231.
               ["ṭi₂", "ṭe₂", "ti₂", "te₂", "de₈", "di₂"],
               "𒎗"),
          Form("HI", None, None,
               # The OGSL values for HI, with the ones from TI₂ above removed.
               ["dab₃", "danₓ", "da₁₀", "dub₃", "dugu", "dug₃",
                "du₁₀", "ha₄", "he", "hi", "i₁₁", "kugu", "muₓ",
                "ta₈", "ʾi₃", "ṭab₆", "ṭa₃"],
               "𒄭")])

# OGSL naming bugs handled here.

# Unnormalized |GAD+TAK₄.DUH| (neither has values).
del main_forms_by_name["|GAD+KID₂.DUH|"]
del forms_by_name["|GAD+KID₂.DUH|"]
# Unnormalized |A.GISAL.GAD.GAR.A.SI| (both with the value addirₓ).
del main_forms_by_name["|A.GISAL.GADA.GAR.A.SI|"]
del forms_by_name["|A.GISAL.GADA.GAR.A.SI|"]

# Insufficiently decomposed/normalized in OGSL.
for name in ("|DIM×EŠ|", "|KA×EŠ|",
             "|LAK617×MIR|",
             "|KAR.MUŠ|",
             "|ŠE₃.TU.BU|",
             "|ŠUL.GI|",
             "|UD.MUD.NUN.KI|",
             "|IM.LAK648|",
             "|E₃.E₃|",
             "|KUD.KUD|"):
  rename(name,
         name.replace(
             "EŠ", "(U.U.U)").replace(
             "MIR", "DUN3@g@g").replace(
             "KAR", "TE.A").replace(
             "ŠE₃", "EŠ₂").replace(
             "ŠUL", "DUN").replace(
             "MUD", "HU.HI").replace(
             # Not sure what to make of the following @note in |URU×MIN|; but it is called |URU×MIN|, so shrug.
             # LAK648 is GIŠGAL, but is not properly described as URU×MIN. Many of the URU× signs are LAK648× in ED.
             "LAK648", "URU×MIN").replace(
             # The entry has the @inote this is a deliberate exception to what should be |UD.DU.UD.DU|.
             # Not sure why this exception.  There are no values for this one anyway.
             "E₃", "UD.DU").replace(
             "KUD", "TAR"))

# Insufficiently decomposed in its name, and also incorrectly decomposed in its encoding. see below.
rename("ŠITA₂", "|ŠITA.GIŠ|")

rename("|ŠU₂.NESAG|", "|ŠU₂.NISAG|")

# LAK207 looks to me like ŠE.HUB₂, not (ŠE&ŠE).HUB₂.
# Conventiently Unicode has the former and not the latter.
rename("|(ŠE&ŠE).HUB₂|", "|ŠE.HUB₂|")

# ASCII ugliness in form ~c |ŠU₂.3xAN| of |BAR.AN|.  OGSL correctly uses 3×AN everywhere else.
rename("|ŠU₂.3xAN|", "|ŠU₂.3×AN|")

# ED, not decomposed in its Unicode name.  Other overdecomposed signs are
# handled below, but because of the ED garbling we actually rename this one.
# TODO(egg): It has no values, imbue it with GAN? http://oracc.museum.upenn.edu/dcclt/Q000024
rename("|AŠ.GAN|", "LAK062")

# Unicode 7.0 related things.

# OGSL gives DUB×EŠ₂ the value gaz₃, and has no DUB×ŠE.
# MZL gives MZL243 DUB×ŠE the value gaz₃, and has no DUB×EŠ₂.
# MZL cites Revue d’Assyriologie et d’archéologie orientale 60 p. 92, wherein
# Civil writes DUB×ŠE.
# Could the origin of DUB×EŠ₂ be a misreading DUB×ŠÈ=DUB×EŠ₂ of DUB×ŠE?
# The text cited by Civil is TuM 5, 8: IV 2, which means
# Texte und Materialien der Frau Professor Hilprecht Collection of Babylonian Antiquities 5,
# Vorsargonische und sargonische Wirtschaftstexte.
# CDLI abbreviates that to TMH: the relevant tablet is
# https://cdli.ucla.edu/search/archival_view.php?ObjectID=P020422,
# Wherein IV 2 clearly is 𒊓𒍶𒉌𒀝𒈨, with a DUB×ŠE 𒍶 (a variant on
# 𒄤 gaz=GUM×ŠE perhaps?), not a DUB×EŠ₂ 𒁿.
rename("|DUB×EŠ₂|", "|DUB×ŠE|")

# Broken precedence for MZL393 usud.
rename("|GA₂×AN.KAK.A|", "|GA₂×(AN.KAK.A)|")

rename("|HI.GIR₃|", "HUŠ")

# Probably broken precedence for MZL532, see MZL514.
# TODO(egg): Borger cites MSL 14 461f. and MSL 16 212 42; I think the former
# is https://cdli.ucla.edu/search/archival_view.php?ObjectID=P258842, check
# that.
rename("|LU₂×EŠ₂.LAL|", "|LU₂×(EŠ₂.LAL)|")

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
    if name == "|A₂.ZA.AN.MUŠ₃|":
      if form.codepoints != "𒀀𒍝𒀭𒈹":
        raise ValueError("OGSL bug fixed")
      else:
        # TODO(egg): check Emar 6/2, p. 508-515 and Emar 6/2, p. 730, Msk 74209a: o i 33–36',
        # see http://oracc.museum.upenn.edu/epsd2/o0024610,
        # https://cdli.ucla.edu/search/search_results.php?SearchMode=Text&ObjectID=P271911.
        form.codepoints = "𒀉𒍝𒀭𒈹"
    if name == "|DAG.KISIM₅×GA|":
      # Off by one codepoint.
      if form.codepoints != "𒁜":
        raise ValueError("OGSL bug fixed")
      form.codepoints = "𒁛"
    if name in ("|BI.ZIZ₂|", "|BI.ZIZ₂.A.AN|", "|BI.ZIZ₂.AN|", "|BI.ZIZ₂.AN.NA|"):
      # OGSL sometimes (but not always) uses 𒀾 AŠ₂ for 𒍩 ZIZ₂).
      if "𒀾" not in form.codepoints:
        raise ValueError("OGSL bug fixed")
      form.codepoints = form.codepoints.replace("𒀾", "𒍩")
    if name == "|LU₂.SU|":
      # šimašgi is very blatantly LU₂.SU, not LU.SU.
      # https://cdli.ucla.edu/search/search_results.php?SearchMode=Text&PrimaryPublication=&MuseumNumber=&Provenience=&Period=&TextSearch=szimaszgi&ObjectID=&requestFrom=Submit
      if form.codepoints != "𒇻𒋢":
        raise ValueError("OGSL bug fixed")
      form.codepoints = "𒇽𒋢"
    if name == "|LU₂.SU.A|":
      # Same as above.
      # https://cdli.ucla.edu/search/search_results.php?SearchMode=Text&PrimaryPublication=&MuseumNumber=&Provenience=&Period=&TextSearch=szimaszgi2&ObjectID=&requestFrom=Submit
      if form.codepoints != "𒇻𒋢𒀀":
        raise ValueError("OGSL bug fixed")
      form.codepoints = "𒇽𒋢𒀀"
    if name == "|LU₃.PAP.PAP|":
      # The entry has the encoding for BARA₂.PAP.PAP (which exists as its own form).
      # See http://oracc.museum.upenn.edu/epsd2/cbd/sux/o0040424.html, see, e.g.,
      # http://oracc.museum.upenn.edu/epsd2/sux
      # https://cdli.ucla.edu/dl/lineart/P221674_l.jpg,
      # titab₂ is pretty clearly meant to be 𒈖𒉽𒉽 (especially since 𒁈𒉽𒉽 is
      # titab already).
      if form.codepoints != "𒁈𒉽𒉽":
        raise ValueError("OGSL bug fixed")
      form.codepoints = "𒈖𒉽𒉽"
    if name == "|PA.DAG.KISIM₅×GUD|":
      # DAG instead of DAG.KISIM₅×GUD.
      if form.codepoints != "𒉺𒁖":
        raise ValueError("OGSL bug fixed")
      form.codepoints = "𒉺𒁟"
    if name == "|PA.DAG.KISIM₅×KAK|":
      # DAG instead of DAG.KISIM₅×KAK.
      if form.codepoints != "𒉺𒁖":
        raise ValueError("OGSL bug fixed")
      form.codepoints = "𒉺𒁣"
    if name == "|ŠITA.GIŠ|" and not form.form_id:
      # ŠITA₂ before the renaming pass above.
      # Note that OGSL gives |ŠITA.GIŠ| as a valueless form ~c.
      # TODO(egg): Consult Labat.
      # GA₂.GIŠ seems pretty clearly wrong for the OB form, see, e.g.,
      # https://cdli.ucla.edu/search/archival_view.php?ObjectID=P241971,
      # https://cdli.ucla.edu/search/archival_view.php?ObjectID=P345503.
      # Šašková goes with ŠITA.GIŠ which looks more like it.
      # In NA ŠITA = GA₂ which may explain the confusion.
      if form.codepoints != "𒂷𒄑":
        raise ValueError("OGSL bug fixed")
      form.codepoints = "𒋖𒄑"
    if name == "|BAR.3×AN|":  # Weirdly decomposing 𒀯.
      if form.codepoints != "𒁇𒀮𒀭":
        raise ValueError("OGSL bug fixed")
      form.codepoints = "𒁇𒀯"
    if name == "|ŠU₂.DUN₃@g@g@s|":
      # Missing DUN₃@g@g@s seems to just be DUN₄.
      if form.codepoints != "𒋙":
        raise ValueError("OGSL bug fixed")
      form.codepoints = "𒋙𒂈"
    if name == "|ŠEŠ.KI.DIM×ŠE|":
      # Probably copied over from another munzerₓ, see http://oracc.museum.upenn.edu/epsd2/cbd/sux/o0034493.html.
      # Attested in https://cdli.ucla.edu/search/search_results.php?SearchMode=Text&ObjectID=P010677 (RTL?)
      # and https://cdli.ucla.edu/search/search_results.php?SearchMode=Text&ObjectID=P010087 (partial).
      if form.codepoints != "𒀖𒀭𒋀𒆠":
        raise ValueError("OGSL bug fixed")
      form.codepoints = "𒋀𒆠𒁵"
    if name == "|UD.MA₂.AB×(U.U.U).ŠIR|":
      # http://oracc.museum.upenn.edu/epsd2/o0047595. No source for that form,
      # so can’t check, but let’s trust the description and assume there is a
      # stray U and None in the encoding.
      if form.codepoints != "𒌓𒈣𒀔𒌋None𒋓":
        raise ValueError("OGSL bug fixed")
      form.codepoints = "𒌓𒈣𒀔𒋓"
    if name == "|U.GIŠ%GIŠ|":
      # http://oracc.museum.upenn.edu/epsd2/o0039173.
      # Attested in http://oracc.iaas.upenn.edu/epsd2/praxis/P273907 where it is
      # transliterated U.KIB, clearly looks like KIB=GIŠ%GIŠ in
      # https://cdli.ucla.edu/search/search_results.php?SearchMode=Text&ObjectID=P273907.
      if form.codepoints != "𒌋𒉣":
        raise ValueError("OGSL bug fixed")
      form.codepoints = "𒌋𒄒"

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
    if name == "|AŠ&AŠ&AŠ.AŠ&AŠ&AŠ|":
      form.codepoints = "𒑀"
    if name == "|AŠ&AŠ&AŠ.AŠ&AŠ&AŠ|":
      form.codepoints = "𒑀"
    if name == "|AŠ&AŠ&AŠ.AŠ&AŠ&AŠ.AŠ|":
      form.codepoints = "𒑁"
    if name == "|AŠ&AŠ&AŠ.AŠ&AŠ&AŠ.TAB|":
      form.codepoints = "𒑅"
    if name == "IMIN":
      form.codepoints = "𒐌"
    if name == "|DIŠ.DIŠ.DIŠ|":
      form.codepoints = "𒐈"
    if name == "|DIŠ.DIŠ.DIŠ.U.U|":
      form.codepoints = "𒐈𒎙"
    if name == "|DIŠ.DIŠ.DIŠ.U.U.U|":
      form.codepoints = "𒐈𒌍"


    # See https://github.com/oracc/ogsl/commit/11f04981b49131894bc5cba543f09b255985b1a2.
    # There may be a problem, but not having a codepoint for de₂ is not a
    # solution.  We let UMUM×KASKAL = de₂, and consider that making it
    # look like an UMUM šeššig is a problem for the font.
    if name == "DE₂":
      form.codepoints = "𒌤"


    # Unicode 7.0 fanciness, except disunifications.
    if name == "GIG":
      form.codepoints = "𒍼"
    if "GIG" in name and form.codepoints and "X" in form.codepoints:
      form.codepoints = form.codepoints.replace("X", "𒍼")
    if name == "KAP₀":
      form.codepoints = "𒍯"
    if name == "|AB×NUN|":
      form.codepoints = "𒍰"
    if "NI.UD" in name:
      raise ValueError(f"NI.UD in {form}")
    if form.codepoints and "𒉌𒌓" in form.codepoints:
      form.codepoints = form.codepoints.replace("𒉌𒌓", "𒎎")
    if name == "|DUB×ŠE|":
      form.codepoints = "𒍶"
    if name == "|EZEN×GUD|":
      form.codepoints = "𒍷"
    if name == "|EZEN×ŠE|":
      form.codepoints = "𒍸"
    if name == "|GA₂×(AN.KAK.A)|":
      form.codepoints = "𒍹"
    if name == "|GA₂×AŠ₂|":
      form.codepoints = "𒍺"
    if name == "GE₂₂":
      form.codepoints = "𒍻"
    if name == "HUŠ":
      form.codepoints = "𒍽"
    if name == "|KA×GIŠ|":
      form.codepoints = "𒎀"
    if name == "|KA×HI×AŠ₂|":
      form.codepoints = "𒎂"
    if name == "|KA×LUM|":
      form.codepoints = "𒎃"
    if name == "|KA×PA|":
      form.codepoints = "𒎄"
    if name == "|KA×TU|":
      form.codepoints = "𒎆"
    if name == "|KA×UR₂|":
      form.codepoints = "𒎇"
    if name == "|LU₂@s×BAD|":
      form.codepoints = "𒎉"
    if name == "|LU₂×(EŠ₂.LAL)|":
      form.codepoints = "𒎊"
    if name == "|LU₂×ŠU|":
      form.codepoints = "𒎋"
    if "MEŠ" in name:
      form.codepoints = form.codepoints.replace("𒈨𒌍", "𒎌").replace("𒈨𒌋𒌋𒌋", "𒎌")
    if name == "|MUŠ₃×ZA|":
      form.codepoints = "𒎍"
    if form.codepoints and "NIN" in name:
      form.codepoints = form.codepoints.replace("𒊩𒌆", "𒎏")
    if name == "NIN₉":
      form.codepoints = "𒎐"
    if name == "|NINDA₂×BAL|":
      form.codepoints = "𒎑"
    if name == "|NINDA₂×GI|":
      form.codepoints = "𒎒"
    if name == "NU₁₁@90":
      form.codepoints = "𒎓"
    if name == "|U.U|":
      form.codepoints = "𒎙"

    if (name == "|GA₂×ZIZ₂|" or
        form.codepoints and any(ord(sign) >= 0x12480 for sign in form.codepoints) or
        name in ("LAK617", "|LAK648×NI|", "|ŠE.NAM₂|")):
      # The Early Dynastic block is garbled in OGSL.
      if name == "|ŠE&ŠE.NI|":
        form.codepoints = chr(0x12532) + "𒉌"
      elif name == "|MUŠ₃.ZA₇|":
        form.codepoints = "𒈹" + chr(0x12541)
      elif name == "|ŠE&ŠE.KIN|":
        form.codepoints = chr(0x12532) + "𒆥"
      elif name in ("|KA×ŠE@f|", "|KUŠU₂×SAL|", "LAK20", "|SAG×TAK₄@f|", "|SAR×ŠE|",
                    "|ŠE@v+NAM₂|", "URU@g"):
        # Seemingly unencoded, |KUŠU₂×SAL| is present an early proposal,
        # http://unicode.org/wg2/docs/n4179.pdf.
        # Post-scriptum: It looks like some of those got renamed from × to +…
        form.codepoints = None
      else:
        # For some reason Unicode has unpredictable rules for PLUS in the ED block.
        try:
          form.codepoints = unicodedata.lookup(
              "CUNEIFORM SIGN " + compute_expected_unicode_name(name, inner_plus=False))
        except KeyError:
          form.codepoints = unicodedata.lookup(
              "CUNEIFORM SIGN " + compute_expected_unicode_name(name, inner_plus=True))


# Assign encodings from components.
for name, forms in forms_by_name.items():
  if name.startswith("|") and name.endswith("|") and not forms[0].codepoints:
    encoding = ""
    components = []
    for component in re.findall(r"(?:[^.()]|\([^()]+\))+", name[1:-1]):
      if "×" in component:
        component = f"|{component}|"
      if component in forms_by_name and forms_by_name[component][0].codepoints:
        encoding += forms_by_name[component][0].codepoints
        components.append(component)
      else:
        break
    else:
      for form in forms:
        form.codepoints = encoding
      print(f"Encoding {forms[0] if len(forms) == 1 else forms} from {components}")


for name, forms in forms_by_name.items():
  encoding = forms[0].codepoints
  if not encoding:
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

  if name== "OO":
    continue

  expected_unicode_name = compute_expected_unicode_name(name)

  # Misnaming in Unicode? U+12036 ARKAB 𒀶 is (looking at the reference
  # glyph) LAK296, to which OGSL gives the value arkab₂, arkab being
  # GAR.IB 𒃻𒅁.
  expected_unicode_name = expected_unicode_name.replace("ARKAB2", "ARKAB")

  # OGSL decomposes 𒍧 and 𒍦, Unicode does not (perhaps for length reasons?).
  if expected_unicode_name == " OVER ".join(4 * ["ASH KABA TENU"]):
    expected_unicode_name = "ZIB KABA TENU"
  if expected_unicode_name == " OVER ".join(4 * ["ASH ZIDA TENU"]):
    expected_unicode_name = "ZIB"

  if expected_unicode_name == "BURU5":
    # Quoth the OGSL: @note The NB source for Ea II (LKU 1) describes BURU₅ as NAM nutillû.
    expected_unicode_name = "NAM NUTILLU"

  if expected_unicode_name == "ELLES396":
    # The unicode name is a value here rather than the catalogue number.
    expected_unicode_name = "ZAMX"

  # OGSL never decomposes LAL₂, so lets’ treat this as intentional.
  expected_unicode_name = expected_unicode_name.replace("LAL2", "LAL TIMES LAL")

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
  elif expected_unicode_name == "NU11 OVER NU11 BUR OVER BUR":
    expected_unicode_name = "SHIR OVER SHIR BUR OVER BUR"

  # See the discussion above.  Maybe someday this will be an alias...
  if "IDIM SQUARED" in expected_unicode_name:
    expected_unicode_name = expected_unicode_name.replace("IDIM SQUARED", "IDIM OVER IDIM SQUARED")

  # Probably a misnomer in Unicode.
  if expected_unicode_name == "LAK-212":
    expected_unicode_name = "ASAL2"

  if expected_unicode_name == "SHE NUN OVER NUN":  # Not decomposed in Unicode.
    expected_unicode_name = "TIR"
  if "SHE PLUS NUN OVER NUN" in expected_unicode_name:
    expected_unicode_name = expected_unicode_name.replace("SHE PLUS NUN OVER NUN", "TIR")

  # Sometimes (but not always) decomposed in OGSL, not decomposed in Unicode.
  if expected_unicode_name == "SHU2 DUN3 GUNU GUNU SHESHIG":
    expected_unicode_name = "SHU2 DUN4"

  actual_unicode_name = " ".join(unicodedata.name(c).replace("CUNEIFORM SIGN ", "") if ord(c) >= 0x12000 else c for c in encoding)
  if ("CUNEIFORM NUMERIC SIGN" in actual_unicode_name or
      "CUNEIFORM PUNCTUATION SIGN" in actual_unicode_name):
    continue  # TODO(egg): deal with that.

  if expected_unicode_name == "SHU OVER SHU INVERTED":  # Magical Unicode word order.
    expected_unicode_name = "SHU OVER INVERTED SHU"

  # TODO(egg): Figure out the PLUS dance someday...
  if actual_unicode_name.replace(" PLUS ", " ") != expected_unicode_name.replace(" PLUS ", " "):
    raise ValueError(f"{name} encoded as {encoding}, {expected_unicode_name} != {actual_unicode_name}")


encoded_forms_by_value = {}

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
      print(f"Multiple main forms with non-ₓ value {value}: {main_forms}")
    elif not main_forms:
      print(f"Multiple variant forms and no main form with non-ₓ value {value}: {forms_by_codepoints.values()}")
    else:
      print(f"Multiple forms (one main) with non-ₓ value {value}: {forms_by_codepoints.values()}")

for value, forms_by_codepoints in encoded_forms_by_value.items():
  for c in value:
    if c not in 'bdgptkʾṭqzšsṣhmnrlwyaeiu₁₂₃₄₅₆₇₈₉₀ₓŋ⁺⁻ś':  # Oracc uses h for ḫ, y for j.
      print(forms_by_codepoints.values())
      raise ValueError(f"Unexpected character {c} in value {value} for {'; '.join(forms_by_codepoints.keys())}")
      break

encoded_signs = set(form.codepoints for forms in forms_by_name.values() for form in forms)
encoded_signs_with_values = set(form.codepoints for forms in forms_by_name.values() for form in forms if form.values)

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
  # MZL680, Hittite, no values, not in the OGSL.
  "𒍱",
  # MZL697, HZL276, Hittite, no values, not in the OGSL.
  "𒍲",
  # MZL454, no values, not in the OGSL.
  "𒍳",
  # MZL811, with explanations given at MZL748 𒁹:
  # 60šu, šuššu^šu resp. 60+šu, šuššu^+šu, the number 60.
  # Borgers writes this can be transcribed 60(KU) in assyrian, but differs from
  # KU in babylonian.  This is probably why we have a separate codepoint.
  # See CAD, entry šūši.
  # Numeric, so let’s handle that separately.
  # TODO(egg): Handle it.
  "𒍵",
  # Probably not actually a thing; see above.
  "𒁿",
  # No idea where that comes from.  Maybe look for it HethZL?
  "𒍾",
  # MZL067, Hittite, no values, not in the OGSL.
  "𒍿",
  # No idea for that one either.
  "𒎁",
  "𒎅",
  # MZL763, no values, not in the OGSL.
  "𒎈",
  # MZL741, variant of MZL882.  Not clear how it differs, does it have the same
  # values?  Does it only have a specific logographic value like TA*?  Punt for
  # now.
  "𒎔",
  # MZL194, no values, not in the OGSL.
  "𒎖",
  # MZL488, a variant of 𒌝𒈨.
  # TODO(egg): should it take its place (and should the UM.ME rendition be a
  # matter for the font?)
  "𒎘",
  # Mystery ED things.
  # TODO(egg): Do another pass over these.
  "𒔯", "𒔵", "𒔹", "𒔼", "𒕀",
  # Unified in favour of the numeric versions.
  "𒀼", "𒅓", "𒇹"
))

for u in range(0x12000, 0x12550):  # Cuneiform, Cuneiform numbers and punctuation, Early Dynastic cuneiform.
  if unicodedata.category(chr(u)) == "Cn":
    continue
  if unicodedata.name(chr(u)).startswith("CUNEIFORM NUMERIC SIGN"):
    continue
  if unicodedata.name(chr(u)).startswith("CUNEIFORM PUNCTUATION SIGN"):
    continue
  if chr(u) in NON_SIGNS:
    continue
  if chr(u) not in encoded_signs:
    raise KeyError(f"No form U+{u:X} {unicodedata.name(chr(u))} {chr(u)}")

with open(".\ogsl.txt", "w", encoding="utf-16") as f:
  for value, forms_by_codepoints in sorted(encoded_forms_by_value.items()):
    main_form_encodings = [form.codepoints for encoding, forms in forms_by_codepoints.items()
                           for form in forms if not form.form_id]
    for encoding, forms in forms_by_codepoints.items():
      if "ₓ" in value or (len(forms_by_codepoints) > 1 and len(main_form_encodings) != 1):
        name = forms[0].name[1:-1] if forms[0].name.startswith("|") else forms[0].name
        print(f"{value}({name}):{encoding}", file=f)
      else:
        print(f"{value}:{encoding}", file=f)
