import atf
import re

for filename, extensions in (
  ("oracc-atf/saao/saa01/SAA01_01.atf",
   {atf.Extension.EM_DASH, atf.Extension.DOT_AS_DELIMITER, atf.Extension.PLUS_AS_DELIMITER}),
  ("cdli/OB akk.atf", set())):
  with open(filename, encoding="utf-8") as f:
    lines = f.readlines()

    artefact = ""
    language = "und"
    in_translation = False

    for line in lines:
      if not line.strip():
        continue
      if line.startswith("&"):
        artefact = line.split("=")[0][1:].strip()
        language = "und"
        in_translation = False
        continue
      elif line.startswith("#"):
        if line.startswith("#atf: lang"):
          language = line.split()[-1]
        continue
      elif line.startswith(("@", "$", "|", ">")):
        if line.startswith("@translation"):
          in_translation = True
        continue
      if in_translation:
        continue
      if line.startswith("==%"):
        text = line[2:]
      else:
        # https://oracc.org/doc/help/editinginatf/primer/structuretutorial/index.html#h_textlines
        # says space, but tabs occur even in
        # https://oracc.org/doc/help/editinginatf/primer/index.html.
        if " " not in line and "\t" not in line:
          print("*** No space in", repr(line))
          continue
        number, text = re.split(r"[ \t]", line, maxsplit=1)
        if not number.endswith("."):
          print("*** Bad line number", repr(number), "in", line)
      text = text.strip()
      try:
        graphemes = atf.parse_transliteration(text)
      except (SyntaxError, NameError) as e:
        print("***", artefact, e)
        continue  

INVALID_LINES = """
1. 1(asz@c) {gesz}kabx(|KAxMASZ)? e2-an-da
"""