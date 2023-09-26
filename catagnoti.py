import csv
import unicodedata

import asl
from asl import ogsl, SourceRange
import difflib

forms = [form for forms in ogsl.forms_by_name.values() for form in forms]

old_formatted_ogsl = str(ogsl)

elles = ogsl.sources["ELLES"]
lak = ogsl.sources["LAK"]

def ellesify(ogsl_name, elles_number):
  ogsl.add_source_mapping(ogsl_name, elles, SourceRange("%03d" % elles_number))

ellesify("|DIM×MAŠ|", 32)
ellesify("|UMUM×HA|", 86)
ellesify("|MUŠ×KUR|", 134)
ellesify("ANŠE", 140)  # Note that the ELLes reference to MEE 45 is off-by-one in column numbers.
ellesify("PIRIG", 144)
ellesify("LAK247", 145)
ellesify("LAK247", 146)
#ellesify("ERIN₂", 159)  # Lost because of the ad hoc disunification in 𒂗𒈨𒅕𒃸.
ellesify("GIDIM", 191)
ellesify("|ŠA₃×SAL|", 231)
ellesify("|LAK449×(AN.EŠ₂)|", 235)
ellesify("|LAK449×SI|", 236)
ellesify("ELLES302", 302)  # Not a terribly difficult identification…
ellesify("EREN", 327)
ellesify("|GA₂×(NE.E₂)|", 374)
ellesify("|A×HA|", 394)

with open("ellesify.diff", "w", encoding="utf-8", newline='\n') as f:
  print("\n".join(difflib.unified_diff(old_formatted_ogsl.splitlines(), str(ogsl).splitlines(),fromfile="a/00lib/ogsl.asl",tofile="b/00lib/ogsl.asl", lineterm="")), file=f)


ogsl.forms_by_name["LAK776"][0].unicode_cuneiform = asl.UnicodeCuneiform("𒇻𒄾")
# See comment in read_ogsl.
ogsl.forms_by_name["LAK20"][0].unicode_cuneiform = asl.UnicodeCuneiform("𒆱")

# Catagnoti name to OGSL name.
NAME_BASED_IDENTIFICATIONS = {
  "DAR": "DAR",
  "ZÍ": "ZE₂",
  "PIRIG": "PIRIG",
  "ITI": "|UD×(U.U.U)|",
  "IL": "IL",
  "DIB": "DIB"
}

ogsl_by_catagnoti = {}

unencoded_catagnoti = []
diri_variant_catagnoti = []

def to_numeric(value):
  value = unicodedata.normalize("NFD", value)
  if '\u0301' in value:
    value = value + "₂"
  if '\u0300' in value:
    value = value + "₃"
  value = value.replace('\u0301', '').replace('\u0300', '')
  return unicodedata.normalize("NFC", value)

egg_concordance = {
  "11": "|BAD.AŠ|",
  "19": "|LU₂×EŠ₂|",
  "28": "|MA×GAN₂@t|",
  "95": "|NE.RU|",
  "110": "|BUR.NU₁₁|",
  "143": "|ERIN₂+X|",
  "147": "|TAK₄.ALAN|",
  "158": "|PAD.MUŠ₃|",
  "165": "|SAG×TAK₄|",
  "226": "|TUM×SAL|",
  "252": "|GISAL.A|",
  "285": "|GA₂×(SAL.KUR)|",
  "286": "LAK786",
}

with open("La paleografia dei testi dell’amministrazione e della cancelleria di Ebla - Source.csv", encoding="utf-8") as f:
  lines = list(csv.reader(f))
  for catagnoti_number, catagnoti_name, laks in lines[1:]:
    if catagnoti_number == "331":
      break
    if not laks and catagnoti_number not in egg_concordance:
      print("No LAK number for PACE%s %s" % (catagnoti_number, catagnoti_name))
      continue
    forms = [form for n in laks.split(", ") for form in ogsl.forms_by_source[lak][SourceRange(n)]] if laks else []
    if forms:
      if catagnoti_number in egg_concordance:
        raise ValueError("PACE%s %s is %s, no need for exceptional concordance" % (catagnoti_number, catagnoti_name, forms))
    else:
      if catagnoti_number in egg_concordance:
        forms = ogsl.forms_by_name[egg_concordance[catagnoti_number]]
        #print("PACE%s %s has no LAK, but is %s" % (catagnoti_number, catagnoti_name, forms))
      elif catagnoti_name == "AŠGAB" and laks == "346":
        # LAK346? in OGSL.
        forms = ogsl.forms_by_name["AŠGAB"]
      elif catagnoti_name == "UM" and laks == "127":
        # OGSL has LAK127? on MES instead.
        forms = ogsl.forms_by_name["UM"]
      elif catagnoti_name == "GIŠGAL" and laks == "648":
        # Doubly encoded, LAK648 as an @form.
        forms = ogsl.forms_by_name["|URU×MIN|"]
      elif catagnoti_name == "ÁŠ" and laks == "162":
        # LAK162 split between AŠ₂ and ZIZ₂.
        forms = ogsl.forms_by_name["AŠ₂"]
      elif catagnoti_name == "KAD₄" and laks == "171":
        # LAK171? in OGSL.
        forms = ogsl.forms_by_name["KAD₄"]
      elif catagnoti_name == "ÍL" and laks == "172":
        # LAK172? in OGSL.
        forms = ogsl.forms_by_name["IL₂"]
      elif catagnoti_name == "ERIM" and laks == "280":
        # LAK280 in OGSL, but affected by a not-yet-upstreamed disunification
        # and I forgot to carry over the list numbers.
        forms = ogsl.forms_by_name["ERIN₂"]
      elif catagnoti_name == "KIBgunû" and laks == "278":
        # LAK278a in OGSL. KIB is GIŠ%GIŠ. What’s in a name?
        forms = ogsl.forms_by_name["|EŠ₂%EŠ₂|"]
      elif catagnoti_name == "TUMgunû" and laks == "497":
        # LAK497a in OGSL.
        forms = ogsl.forms_by_name["|TUM×(DIŠ.DIŠ.DIŠ)|"]
      elif catagnoti_name == "MUNŠUB" and laks == "672":
        # LAK672b in OGSL.
        forms = ogsl.forms_by_name["MUNSUB"]
      elif catagnoti_name == "GURUŠ" and laks == "709":
        # LAK672a in OGSL.
        forms = ogsl.forms_by_name["GURUŠ"]
      elif catagnoti_name == "KAL" and laks == "709":
        # LAK672b in OGSL.
        forms = ogsl.forms_by_name["KAL"]
      else:
        print("PACE%s %s = LAK%s not in OGSL" % (catagnoti_number, catagnoti_name, laks))

    if catagnoti_name in NAME_BASED_IDENTIFICATIONS:
      for form in forms:
        form.sign = ogsl.signs_by_name[NAME_BASED_IDENTIFICATIONS[catagnoti_name]]
    if forms:
      if catagnoti_number not in ogsl_by_catagnoti:
          ogsl_by_catagnoti[catagnoti_number] = []
      ogsl_by_catagnoti[catagnoti_number] = forms
      if not any(form.unicode_cuneiform or form.sign and form.sign.unicode_cuneiform for form in forms):
        print("PACE%s %s = LAK%s has no encoding: %s, %s" % (catagnoti_number, catagnoti_name, laks, [f.names[0] for f in forms], [s.source.abbreviation + str(s.number) for form in forms for s in form.sources]))
      elif not any(form.unicode_cuneiform or form.sign and len(form.sign.unicode_cuneiform.text) == 1 for form in forms):
        print("PACE%s %s = LAK%s is a variant of a diri: %s, %s" % (catagnoti_number, catagnoti_name, laks, [f.names[0] for f in forms], [s.source.abbreviation + str(s.number) for form in forms for s in form.sources]))

      if any(form.names[0] == catagnoti_name for form in forms):
        continue
      if any(to_numeric(catagnoti_name).replace('Ḫ', 'H').lower() in form.values for form in forms):
        continue
      else:
        #print("PACE%s %s %s" % (catagnoti_number, catagnoti_name, forms))
        continue

print(f"{len(ogsl_by_catagnoti)} Catagnoti signs in OGSL")
print(f"{len(ogsl.forms_by_source[elles])} ELLes signs in OGSL")

elles_inter_catagnoti = [(catagnoti_number, forms) for catagnoti_number, forms in ogsl_by_catagnoti.items() if any(s.source == elles for form in forms for s in form.sources)]
print(f"{len(elles_inter_catagnoti)} Catagnoti signs in ELLes")

elles_inter_catagnoti_no_lak = [(catagnoti_number, [f.names[0] for f in forms], [s.source.abbreviation + str(s.number) for form in forms for s in form.sources]) for catagnoti_number, forms in elles_inter_catagnoti if not any(s.source is lak for form in forms for s in form.sources)]
print(f"{len(elles_inter_catagnoti_no_lak)} Catagnoti signs in ELLes with no LAK: {elles_inter_catagnoti_no_lak}")

for i in range(1, 398):
  if SourceRange(str(i)) not in ogsl.forms_by_source[elles] and i not in (
      33,  # 33a and 33b.
      35): # AŠ.SILA₃ not in OGSL; dcclt/ebla instead has normal sila₃ in MEE 3 48 o 16 sq.
    print("ELLes%s not in OGSL" % i)
