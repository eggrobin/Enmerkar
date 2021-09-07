import sys
import re
import codecs
import unicodedata

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

for name, forms in forms_by_name.items():
  if name.startswith("|") and name.endswith("|") and not forms[0].codepoints:
    encoding = ""
    components = []
    for component in re.findall(r"(?:[^.()]|\([^()]+\))+", name[1:-1]):
      if "×" in component:
        component = f"{component}"
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
  if encoding:
    for form in forms:
      for value in form.values:
        if not value in encoded_forms_by_value:
          encoded_forms_by_value[value] = {}
        if encoding not in encoded_forms_by_value[value]:
          encoded_forms_by_value[value][encoding] = []
        encoded_forms_by_value[value][encoding].append(form)

for name, forms in forms_by_name.items():
  values = [value for form in forms for value in form.values if "@c" not in value]
  if values and not forms[0].codepoints:
    print(f"No encoding for {name} with values {values}")

for value, forms_by_codepoints in encoded_forms_by_value.items():
  if "ₓ" not in value and len(forms_by_codepoints) > 1:
    print(f"Multiple signs with value {value}: {'; '.join(forms_by_codepoints.keys())}")
    print(forms_by_codepoints.values())

for value, forms_by_codepoints in encoded_forms_by_value.items():
  if value[0] in '1234567890':
    continue  # We do numbers separately.
  for c in value:
    if c not in 'bdgptkʾṭqzšsṣhmnrlwyjaeiu₁₂₃₄₅₆₇₈₉₀ₓŋ:⁺⁻ś':  # Oracc uses ḫ for h.
      print(f"Unexpected character {c} in value {value} for {'; '.join(forms_by_codepoints.keys())}")
      print(forms_by_codepoints.values())
      break

encoded_signs = set(form.codepoints for forms in forms_by_name.values() for form in forms)
encoded_signs_with_values = set(form.codepoints for forms in forms_by_name.values() for form in forms if form.values)

for u in range(0x12000, 0x12550):  # Cuneiform, Cuneiform numbers and punctuation, Early Dynastic cuneiform.
  if unicodedata.category(chr(u)) == "Cn":
    continue
  if chr(u) not in encoded_signs:
    print(f"No form U+{u:X} {unicodedata.name(chr(u))} {chr(u)}")
  if chr(u) not in encoded_signs_with_values:
    print(f"No values for U+{u:X} {unicodedata.name(chr(u))} {chr(u)}")
