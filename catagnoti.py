import csv
import unicodedata

import read_ogsl

forms = [form for forms in read_ogsl.forms_by_name.values() for form in forms]

ogsl_by_lak = {}

for form in forms:
  for number in form.lists:
    if number.startswith("LAK"):
      lak = number[3:].lstrip("0")
      if not lak in ogsl_by_lak:
        ogsl_by_lak[lak] = []
      ogsl_by_lak[lak].append(form)

def to_numeric(value):
  value = unicodedata.normalize("NFD", value)
  if '\u0301' in value:
    value = value + "₂"
  if '\u0300' in value:
    value = value + "₃"
  value = value.replace('\u0301', '').replace('\u0300', '')
  return unicodedata.normalize("NFC", value)

with open("La paleografia dei testi dell’amministrazione e della cancelleria di Ebla - Source.csv", encoding="utf-8") as f:
  lines = list(csv.reader(f))
  for catagnoti_number, catagnoti_name, laks in lines[1:]:
    if not laks:
      print("No LAK number for PACE%s %s" % (catagnoti_number, catagnoti_name))
      continue
    forms = [form for lak in laks.split(",") for form in ogsl_by_lak.get(lak, [])]
    if not forms:
      if catagnoti_name == "AŠGAB" and laks == "346":
        # LAK346? in OGSL.
        forms = read_ogsl.forms_by_name["AŠGAB"]
      elif catagnoti_name == "UM" and laks == "127":
        # OGSL has LAK127? on MES instead.
        forms = read_ogsl.forms_by_name["UM"]
      elif catagnoti_name == "GIŠGAL" and laks == "648":
        # Doubly encoded, LAK648 as an @form.
        forms = read_ogsl.forms_by_name["|URU×MIN|"]
      elif catagnoti_name == "ÁŠ" and laks == "162":
        # LAK162 split between AŠ₂ and ZIZ₂.
        forms = read_ogsl.forms_by_name["AŠ₂"]
      elif catagnoti_name == "KAD₄" and laks == "171":
        # LAK171? in OGSL.
        forms = read_ogsl.forms_by_name["KAD₄"]
      elif catagnoti_name == "ÍL" and laks == "172":
        # LAK172? in OGSL.
        forms = read_ogsl.forms_by_name["IL₂"]
      elif catagnoti_name == "ERIM" and laks == "280":
        # LAK280 in OGSL, but affected by a not-yet-upstreamed disunification
        # and I forgot to carry over the list numbers.
        forms = read_ogsl.forms_by_name["ERIN₂"]
      elif catagnoti_name == "KIBgunû" and laks == "278":
        # LAK278a in OGSL. KIB is GIŠ%GIŠ. What’s in a name?
        forms = read_ogsl.forms_by_name["|EŠ₂%EŠ₂|"]
      elif catagnoti_name == "TUMgunû" and laks == "497":
        # LAK497a in OGSL.
        forms = read_ogsl.forms_by_name["|TUM×(DIŠ.DIŠ.DIŠ)|"]
      elif catagnoti_name == "MUNŠUB" and laks == "672":
        # LAK672b in OGSL.
        forms = read_ogsl.forms_by_name["MUNSUB"]
      elif catagnoti_name == "GURUŠ" and laks == "709":
        # LAK672a in OGSL.
        forms = read_ogsl.forms_by_name["GURUŠ"]
      elif catagnoti_name == "KAL" and laks == "709":
        # LAK672b in OGSL.
        forms = read_ogsl.forms_by_name["KAL"]
      else:
        print("PACE%s %s = LAK%s not in OGSL" % (catagnoti_number, catagnoti_name, laks))

    if forms:
      if not any(form.codepoints or form.sign and form.sign.codepoints for form in forms):
        print("PACE%s %s = LAK%s not has no encoding: %s" % (catagnoti_number, catagnoti_name, laks, forms))

      if any(form.name == catagnoti_name for form in forms):
        continue
      if any(to_numeric(catagnoti_name).replace('Ḫ', 'H').lower() in form.values for form in forms):
        continue
      else:
        #print("PACE%s %s %s" % (catagnoti_number, catagnoti_name, forms))
        continue