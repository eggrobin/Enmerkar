﻿import sys
import codecs

#sys.stdout = codecs.getwriter("utf-16")(sys.stdout.detach())

with open(r"..\ogsl\00lib\ogsl.asl", encoding="utf-8") as f:
  lines = f.read().split("\n")

sign_name = None
form_id = None
name = None
codepoints = None
values = []

main_forms_by_name = {}
forms_by_name = {}
encoded_forms_by_value = {}

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
    if tokens[0] == "@sign" or tokens[0] == "@form":
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
      name = tokens[-1]
      codepoints = None
      values = []
    if tokens[0] == "@sign":
      if len(tokens) != 2:
        raise ValueError(tokens)
      sign_name = tokens[-1]
      form_id = None
    if tokens[0] == "@form":
      if len(tokens) != 3 and not tokens[3][0] in ("x", "["):
        raise ValueError(tokens)
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
      if "-" in value:
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
      values.append(value)
    if tokens[0] == "@ucode":
      if len(tokens) != 2:
        raise ValueError(tokens)
      codepoints = ''.join('X' if x in ('X', 'None') else chr(int("0" + x, 16)) for x in tokens[-1].split("."))
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
      for value in form.values:
        if not value in encoded_forms_by_value:
          encoded_forms_by_value[value] = {}
        if encoding not in encoded_forms_by_value[value]:
          encoded_forms_by_value[value][encoding] = []
        encoded_forms_by_value[value][encoding].append(form)
  else:
    for form in forms:
      if form.values:
        print(f"No codepoints for {form}: {'; '.join(form.values)}")

for value, forms_by_codepoints in encoded_forms_by_value.items():
  if "ₓ" not in value and len(forms_by_codepoints) > 1:
    print(f"Multiple signs with value {value}: {'; '.join(forms_by_codepoints.keys())}")
    print(forms_by_codepoints.values())

for value, forms_by_codepoints in encoded_forms_by_value.items():
  if value[0] in '1234567890':
    continue  # Not looking at numbers for now.
  for c in value:
    if c not in 'bdgptkʾṭqzšsṣhmnrlwyjaeiu₁₂₃₄₅₆₇₈₉₀ₓŋ:⁺⁻ś':  # Oracc uses ḫ for h.
      print(f"Unexpected character {c} in value {value} for {'; '.join(forms_by_codepoints.keys())}")
      print(forms_by_codepoints.values())
      break
