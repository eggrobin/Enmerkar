import csv
from typing import Dict
import unicodedata

import asl
from asl import osl, SourceRange
import difflib

import re

forms = [form for forms in osl.forms_by_name.values() for form in forms]
signs_by_value: dict[str, asl.Sign] = {}

for sign in osl.signs:
  if isinstance(sign, asl.Sign):
    for value in sign.values:
      signs_by_value[value.text] = sign

old_formatted_osl = str(osl)

ptace = osl.sources["PTACE"]
lak = osl.sources["LAK"]

def catagnotify(osl_name, catagnoti_number):
  osl.add_source_mapping(osl_name, ptace, SourceRange("%03d" % int(catagnoti_number)))


osl.forms_by_name["LAK776"][0].unicode_cuneiform = asl.UnicodeCuneiform("𒇻𒄾")
# See comment in read_osl.
#osl.forms_by_name["LAK20"][0].unicode_cuneiform = asl.UnicodeCuneiform("𒆱")

osl_by_catagnoti = {}

unencoded_catagnoti = []
diri_variant_catagnoti = []

def to_numeric(value : str):
  value = unicodedata.normalize("NFD", value)
  if '\u0301' in value:
    value = value + "₂"
  if '\u0300' in value:
    value = value + "₃"
  value = value.replace('\u0301', '').replace('\u0300', '')
  return unicodedata.normalize("NFC", value)

def oraccify_name(name : str) -> str:
  parts = re.split("([×-])", name.replace('Ḫ', 'H'))
  result = ""
  for i, part in enumerate(parts):
    if i % 2 == 1:
      result += part.replace('-', '.')
    else:
      value = to_numeric(part.lower())
      if value in signs_by_value:
        part = signs_by_value[value].names[0]
        if part.startswith('|') and result.endswith('×'):
          result += '(' + part[1:-1] + ')'
        else:
          result += part
      else:
        result += part
  return result if '|' in result or ('.' not in result and '×' not in result) else "|%s|" % result

#print(oraccify_name("GÁ×GÉME"))
#exit(1)

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

catagnoti_easy = {}
catagnoti_not_so_easy = set()
refinements = {}
mismatches : list[str] = []

with open("La paleografia dei testi dell’amministrazione e della cancelleria di Ebla - Source.csv", encoding="utf-8") as f:
  lines = list(csv.reader(f))
  for catagnoti_number, catagnoti_name, laks in lines[1:]:
    if SourceRange(catagnoti_number) in osl.forms_by_source[ptace]:
      #print("+++ PTACE%s already in OSL" % catagnoti_number)
      continue
    if catagnoti_number == "331":
      break
    if not laks and catagnoti_number not in egg_concordance:
      print("No LAK number for PTACE%s %s" % (catagnoti_number, catagnoti_name))
      continue
    forms = [form for n in laks.split(", ") for form in osl.forms_by_source[lak][SourceRange(n)]] if laks else []
    if forms:
      if catagnoti_number in egg_concordance:
        raise ValueError("PTACE%s %s is %s, no need for exceptional concordance" % (catagnoti_number, catagnoti_name, "\n".join("%s" % form for form in forms)))
    oracc_name = oraccify_name(catagnoti_name)
    if oracc_name not in osl.forms_by_name:
      oracc_name = None
    if oracc_name and forms and laks:
      for form in forms:
        if oracc_name == form.names[0]:
          print("--- Name and LAK%s agree on %s for PTACE%s %s" % (laks, oracc_name, catagnoti_number, catagnoti_name))
          catagnoti_easy[catagnoti_number] = oracc_name
        elif form in osl.signs_by_name[oracc_name].forms:
          refinement = ">>> LAK%s (%s) refines name (%s) for PTACE%s %s" % (laks, form.names[0], oracc_name, catagnoti_number, catagnoti_name)
          refinements[catagnoti_number] = form.names[0]
          print(refinement)
        else:
          mismatch = "*** Name (%s) and LAK%s (%s) disagree for PTACE%s %s" % (oracc_name, laks, form.names[0], catagnoti_number, catagnoti_name)
          mismatches.append(mismatch)
          print(mismatch)
          catagnoti_not_so_easy.add(catagnoti_number)
    else:
      if not laks:
        if oracc_name:
          print("!!! Match on name (%s) no LAK for PTACE%s %s" % (oracc_name, catagnoti_number, catagnoti_name))
        else:
          print("!!! Unknown and no LAK: PTACE%s %s" % (catagnoti_number, catagnoti_name))
      elif oracc_name:
        print("!!! Match on name (%s) but not on LAK%s for PTACE%s %s" % (oracc_name, laks, catagnoti_number, catagnoti_name))
      elif forms:
        print("!!! Match on LAK%s (%s) but not on name for PTACE%s %s" % (laks, forms[0].names[0], catagnoti_number, catagnoti_name))
    continue
    if forms:
      if catagnoti_number not in osl_by_catagnoti:
          osl_by_catagnoti[catagnoti_number] = []
      osl_by_catagnoti[catagnoti_number] = forms
      log_unicode_status = False
      if log_unicode_status:
        if not any(form.unicode_cuneiform or form.sign and form.sign.unicode_cuneiform for form in forms):
          print("--- PTACE%s %s = LAK%s has no encoding: %s, %s" % (catagnoti_number, catagnoti_name, laks, [f.names[0] for f in forms], [s.source.abbreviation + str(s.number) for form in forms for s in form.sources]))
        elif not any(form.unicode_cuneiform or form.sign and len(form.sign.unicode_cuneiform.text) == 1 for form in forms):
          print("+++ PTACE%s %s = LAK%s is a variant of a diri: %s, %s" % (catagnoti_number, catagnoti_name, laks, [f.names[0] for f in forms], [s.source.abbreviation + str(s.number) for form in forms for s in form.sources]))

      values = [value.text for form in forms for value in form.values] + [
                value.text for form in forms if form.sign for value in form.sign.values]
      if oraccify_name(catagnoti_name) in set(form.names[0] for form in forms):
        continue
      elif oraccify_name(catagnoti_name) in osl.forms_by_name:
        print("*** PTACE%s %s name suggests %s instead identified with %s" %
                (catagnoti_number, catagnoti_name,
                 oraccify_name(catagnoti_name),
                 [form.names[0] for form in forms]))
      else:
        print("!!! PTACE%s %s %s" % (catagnoti_number, catagnoti_name, values))
        continue

print(len(catagnoti_easy.keys() - catagnoti_not_so_easy), "really easy")
print(len(catagnoti_easy), "partially easy")
print(len(mismatches), "mismatches")
print(len(refinements.keys() - catagnoti_not_so_easy), "easy refinements")
print(len(refinements), "total refinements")
print('\n'.join(mismatches))

for catagnoti_number, name in refinements.items():
  if catagnoti_number in catagnoti_not_so_easy:
    continue
  catagnotify(name, catagnoti_number)

with open("catagnotify.diff", "w", encoding="utf-8", newline='\n') as f:
  print("\n".join(difflib.unified_diff(old_formatted_osl.splitlines(), str(osl).splitlines(),fromfile="a/00lib/osl.asl",tofile="b/00lib/osl.asl", lineterm="")), file=f)

print(f"{len(osl_by_catagnoti)} Catagnoti signs in osl")
#print(f"{len(osl.forms_by_source[elles])} ELLes signs in osl")

elles_inter_catagnoti = [(catagnoti_number, forms) for catagnoti_number, forms in osl_by_catagnoti.items() if any(s.source == elles for form in forms for s in form.sources)]
print(f"{len(elles_inter_catagnoti)} Catagnoti signs in ELLes")

elles_inter_catagnoti_no_lak = [(catagnoti_number, [f.names[0] for f in forms], [s.source.abbreviation + str(s.number) for form in forms for s in form.sources]) for catagnoti_number, forms in elles_inter_catagnoti if not any(s.source is lak for form in forms for s in form.sources)]
print(f"{len(elles_inter_catagnoti_no_lak)} Catagnoti signs in ELLes with no LAK: {elles_inter_catagnoti_no_lak}")

if False:
  for i in range(1, 398):
    if SourceRange(str(i)) not in osl.forms_by_source[elles] and i not in (
        33,  # 33a and 33b.
        35): # AŠ.SILA₃ not in osl; dcclt/ebla instead has normal sila₃ in MEE 3 48 o 16 sq.
      print("ELLes%s not in osl" % i)
