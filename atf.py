from collections import defaultdict
import re

with open("cdli/OB akk.atf", encoding="utf-8") as f:
  lines = f.readlines()

errors : dict[str, list[str]] = defaultdict(list)

def report_error(error: str, line: str):
  errors[error].append(line)

counts : dict[str, int] = defaultdict(int)

for line in lines:
  if not line.strip():
    continue
  if line.startswith("&"):
    artefact = line.split()[0]
    continue
  elif line.startswith("#"):
    if line.startswith("#atf: lang"):
      language = line.split()[-1]
    continue
  elif line.startswith(("@", "$", "|", ">")):
    continue
  if "." not in line:
    print("*** Could not parse line number in", line)
    continue
  text = line.split(".", 1)[1].strip()
  graphemes = re.split(r"(-| |\{\{[^}]*\}\}|(?<!\{)\{[^}]*\}(?!\})|\[|\])", text)
  missing = False
  logogram = False
  maybe = False
  supplied = False
  excised = False
  implied = False
  for grapheme in graphemes:
    if grapheme in ("-", " "):
      continue
    while grapheme.startswith(("[", "<", "_", "(")):
      if grapheme.startswith("["):
        if missing:
          report_error("Nested missing", line)
        missing = True
        grapheme = grapheme[1:]
      elif grapheme.startswith("_"):
        if logogram:
          if grapheme == "_":
            break
          report_error("Nested logogram", line)
        logogram = True
        grapheme = grapheme[1:]
      elif grapheme.startswith("<<"):
        if excised:
          report_error("Nested excised", line)
        excised = True
        grapheme = grapheme[2:]
      elif grapheme.startswith("<("):
        if implied:
          report_error("Nested implied", line)
        implied = True
        grapheme = grapheme[2:]
      elif grapheme.startswith("<"):
        if supplied:
          report_error("Nested supplied", line)
        supplied = True
        grapheme = grapheme[1:]
      elif grapheme.startswith("("):
        if maybe:
          report_error("Nested maybe", line)
        maybe = True
        grapheme = grapheme[1:]
    while grapheme.endswith(("]", ">", "_", ")")):
      if grapheme.endswith("]"):
        if not missing:
          report_error("Unstarted missing", line)
        missing = False
        grapheme = grapheme[:-1]
      elif grapheme.endswith("_"):
        if not logogram:
          report_error("Unstarted logogram", line)
        logogram = False
        grapheme = grapheme[:-1]
      elif grapheme.endswith(">>"):
        if not excised:
          report_error("Unstarted excised", line)
        excised = False
        grapheme = grapheme[:-2]
      elif grapheme.endswith(")>"):
        if not implied:
          report_error("Unstarted implied", line)
        implied = False
        grapheme = grapheme[:-2]
      elif grapheme.endswith(">"):
        if not supplied:
          report_error("Unstarted supplied", line)
        supplied = False
        grapheme = grapheme[:-1]
      elif grapheme.endswith(")"):
        if "(" in grapheme:
          break
        if not maybe:
          report_error("Unstarted maybe", line)
        maybe = False
        grapheme = grapheme[:-1]
    if grapheme.startswith("{") and grapheme.endswith("}"):
      grapheme = grapheme[1:-1]
    grapheme = grapheme.rstrip("#?!")
    if not grapheme.strip():
      continue
    counts[grapheme] += 1

for error, lines in errors.items():
  print(f"*** {error}: {len(lines)} occurrences")

for value, count in sorted(counts.items(), key=lambda kv: -kv[1]):
  print(value, count)