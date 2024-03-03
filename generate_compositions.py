import re

import asl
from asl import osl
import numbers

ERIN2 = osl.forms_by_name["ERIN₂"][0]

ERIN2_values = ["erin₂", "erim", "erem", "eren₂", "nura", "nuri", "nuru",
                "rin₂", "rina₂", "sap₂", "ṣab", "ṣap", "ṣapa","zab", "zalag₂",
                "zap", "erena₂", "erina₂",
                # NABU 1990/12.
                "surₓ",
                # Note 𒋝 SIG; putting that there rather than with the UD-like
                # ones.
                "sigₓ",]
PIR2_values = [# MZL values; all homophones of 𒌓 UD.
               "pir₂", "bir₃", "hiš₃", "lah₂", "lih₂", "par₅", "per₂",
                # Other OGSL values; shoving them there, since they are
                # homophones of UD (or similar to them) and the ERIN₂ ones in
                # MZL are not.
                "udaₓ", "tam₅"]

ERIN2.values = [value for value in ERIN2.values if value.text in ERIN2_values]

for forms in osl.forms_by_name.values():
  for form in forms:
    if form.unicode_cuneiform:
      old = form.unicode_cuneiform.text
      new = old.replace(
          "𒁹𒁹𒁹", "𒐈").replace(
          "𒇹", "𒐂").replace(
          "𒋰𒋰𒋰𒋰𒀸", "𒐇").replace(
          "𒋰𒋰𒋰𒋰", "𒐆").replace(
          "𒋰𒋰𒋰𒀸", "𒐅").replace(
          "𒋰𒋰𒋰", "𒐄").replace(
          "𒋰𒋰𒀸", "𒐃").replace(
          "𒀼𒀼𒀸", "𒑁").replace(
          "𒀼𒀼", "𒑀").replace(
          "𒀼", "𒐺").replace(
          "𒅓", "𒐌")
      if new != old:
        print(f"*** Changing encoding of {form.names[0]} from {old} to {new}")
        form.unicode_cuneiform.text = new

for forms in (osl.forms_by_name["BAD"], osl.forms_by_name["IDIM"]):
  for form in forms:
    for v in form.values:
      if v.text == "eše₃":
        form.values.remove(v)

encoded_forms_by_value: dict[str, dict[str, list[asl.Form]]] = {}
encoded_forms_by_list_number: dict[str, dict[str, list[asl.Form]]] = {}

for name, forms in osl.forms_by_name.items():
  if any (form.unicode_cuneiform for form in forms):
    encodings = set(form.unicode_cuneiform.text for form in forms if form.unicode_cuneiform)
    if len(encodings) != 1:
      raise ValueError(f"Multiple encodings for {name}: {encodings}")
    encoding = list(encodings)[0]
    for form in forms:
      if not form.unicode_cuneiform:
        print(f"*** Missing {encoding} on {form.names[0]}")
        form.unicode_cuneiform = asl.UnicodeCuneiform(encoding)

for name, forms in osl.forms_by_name.items():
  for form in forms:
    if form.deprecated:
      continue
    if form.unicode_cuneiform or form.unicode_map:
      xsux = (form.unicode_cuneiform or osl.forms_by_name[form.unicode_map.text][0].unicode_cuneiform).text;
      if "X" in xsux:
        continue
      if "O" in xsux:
        continue
      for value in form.values:
        if value.deprecated:
          continue
        if value.language and "/n" in value.language:
          continue
        if value.text in ("/", "𒑱", ':"', ":.", ":", "::"):
          continue
        if value.text in ("d", "f", "m"):
          continue
        if "x" in value.text:
          continue
        if "-" in value.text:
          continue
        if "?" in value.text:
          continue
        if "@" in value.text:
          continue
        if "{" in value.text:
          continue
        if value.text in ("o", "o"):
          continue
        if re.match(r"p[₁-₅]", value.text):
          continue
        if re.match("[0-9]", value.text):
          continue
        if value.text not in encoded_forms_by_value:
          encoded_forms_by_value[value.text] = {}
        if xsux not in encoded_forms_by_value[value.text]:
          encoded_forms_by_value[value.text][xsux] = []
        encoded_forms_by_value[value.text][xsux].append(form)
      for source in form.sources:
        if source.source.abbreviation == "U+" or source.questionable:
          continue
        abbreviations = ("ŠL", "MÉA") if source.source.abbreviation == "SLLHA" else (source.source.abbreviation,);
        for abbreviation in abbreviations:
          number = abbreviation + str(source.number.first) + source.number.suffix
          if number not in encoded_forms_by_list_number:
            encoded_forms_by_list_number[number] = {}
          if xsux not in encoded_forms_by_list_number[number]:
            encoded_forms_by_list_number[number][xsux] = []
          encoded_forms_by_list_number[number][xsux].append(form)

compositions: dict[str, str] = {}

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
  main_form_encodings = [encoding for encoding, forms in forms_by_codepoints.items()
                          for form in forms if not form.sign]
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
  main_form_encodings = [encoding for encoding, forms in forms_by_codepoints.items()
                          for form in forms if not form.sign]
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
