from collections import defaultdict
import re
import enum

VALUE_LETTER = re.compile(r"(?:sz|s,|t,|[abdeghiklmnpqrstuvwyz'])")
VALUE_INDEX = re.compile(r"(?:[0-9]+|x)")
VALUE = re.compile(fr"(?:{VALUE_LETTER.pattern}+{VALUE_INDEX.pattern}?)")


NAME_LETTER = re.compile(r"(?:SZ|S,|T,|[ABDEGHIKLMNPQRSTUVWYZ'])")
NAME_INDEX = re.compile(r"(?:[0-9]+|X)")
MODIFIER = re.compile(r"(?:\d+|[fgstnzkrh])")
NAME = re.compile(fr"(?:[A-Z][A-Z][A-Z]+\d\d\d|{NAME_LETTER.pattern}+{NAME_INDEX.pattern}?(?:@{MODIFIER.pattern})?)")
COMPOUND = re.compile(r"(?:\|[^|<>{}\[\] -]+\|)")
QUALIFIED =  re.compile(
  fr"(?:{VALUE.pattern}\((?:{NAME.pattern}|{COMPOUND.pattern})\))"
)

NUMBER = re.compile(
  fr"(?:(?:n|[\d/]+)\((?:{VALUE.pattern}(?:@(?:90|[cv]))?|{NAME.pattern}|{COMPOUND.pattern})\))"
)

ALTERNATIVE = re.compile(
  fr"(?:(?:{QUALIFIED.pattern}|{VALUE.pattern}|{NAME.pattern}|{NUMBER.pattern}|{COMPOUND.pattern})[#?!*]*)"
)

GRAPHEME = re.compile(
  fr"(?:{ALTERNATIVE.pattern}(?:/{ALTERNATIVE.pattern})*|x\??)"
)

PUNCTUATION = re.compile(
  r"""(?:(?<= )|^)(?:\*|:|:'|:"|:.|::|/) """
)

print(GRAPHEME.pattern)

class SpanAttribute(enum.Enum):
  LOGOGRAM = 0, "_", "_"
  MAYBE = 1, "(", ")"
  DETERMINATIVE = 2, "{", "}"
  BROKEN = 3, "[", "]"
  SUPPLIED = 4, "<", ">"
  EXCISED = 5, "<<", ">>"
  IMPLIED = 6, "<(", ")>"
  LINGUISTIC_GLOSS = 7, "{{", "}}"
  DOCUMENT_GLOSS = 8, "{(", ")}"

  def __init__(self, value: int, open: str, close: str) -> None:
    self.open = open
    self.close = close

  def __str__(self) -> str:
    return self.name

def parse_transliteration(source: str, language: str):
  graphemes : list[tuple[str, str, set[SpanAttribute]]] = []
  i = 0
  after_delimiter = " "
  delimiter_before_determinative = None
  attributes : set[SpanAttribute] = set()
  def start_span(attribute: SpanAttribute):
    if attribute in attributes:
      raise SyntaxError(f"Nested {attribute}: {source[:i]}☞{source[i:]}")
    attributes.add(attribute)
  def end_span(attribute: SpanAttribute):
    if attribute not in attributes:
      raise SyntaxError(f"Unstarted {attribute}: {source[:i]}☞{source[i:]}")
    attributes.remove(attribute)
  while i < len(source):
    while source[i] == " ":
      i += 1
      after_delimiter = " "
    match = GRAPHEME.match(source, i)
    if match:
      graphemes.append((match.group(), language, set(attributes)))
      i = match.end()
      after_delimiter = None
      continue
    if source[i] == "-":
      if after_delimiter:
        raise SyntaxError(f"Double delimiter: {source[:i]}☞{source[i:]}")
      i += 1
      after_delimiter = "-"
      continue
    if source[i] == "_":
      if after_delimiter:
        start_span(SpanAttribute.LOGOGRAM)
      else:
        end_span(SpanAttribute.LOGOGRAM)
      i += 1
      continue
    match = PUNCTUATION.match(source, i)
    if match:
      i = match.end()
      continue
    if source.startswith("...", i):
      if SpanAttribute.BROKEN not in attributes:
        raise SyntaxError(f"... outside breakage brackets: {source[:i]}☞{source[i:]}")
      after_delimiter = None
      i += 3
      continue
    if (source.startswith(
      ("# ", '" ', "~ ", "| ", "= ", "^ ", "@ ", "& "), i) and
      (i == 0 or source[i-1] == " ")):
      # Column in lexical text.
      i += 2
      continue
    found = False
    for abbreviation, language_tag in (
        ("a", "akk"),
        ("s", "sux"),
        ("a/n", "akk-x-norm")):
      if source.startswith(f"%{abbreviation} ", i):
        i += len(abbreviation) + 2
        after_delimiter = " "
        language = language_tag
        found = True
        break
    if found:
      continue
    if source.startswith("($", i):
      i = source.index("$)", i + 2) + 2
      continue
    for attribute in (
        SpanAttribute.LINGUISTIC_GLOSS,
        SpanAttribute.DOCUMENT_GLOSS,
        SpanAttribute.IMPLIED,
        SpanAttribute.EXCISED,
        SpanAttribute.SUPPLIED,
        SpanAttribute.MAYBE,
        SpanAttribute.BROKEN):
      if source.startswith(attribute.open, i):
        start_span(attribute)
        i += len(attribute.open)
        break
      elif source.startswith(attribute.close, i):
        end_span(attribute)
        i += len(attribute.open)
        break
    else:
      if source[i] == "{":
        start_span(SpanAttribute.DETERMINATIVE)
        delimiter_before_determinative = after_delimiter
        i += 1
        if source[i] == "+":
          # TODO(egg): Representation for phonetic complements?
          i += 1
      elif source[i] == "}":
        end_span(SpanAttribute.DETERMINATIVE)
        after_delimiter = delimiter_before_determinative
        i += 1
      else:
        raise SyntaxError(f"Syntax error: {source[:i]}☞{source[i:]}")
  return graphemes

def get_value_counts(file: str, target_language: str, exclude: set[SpanAttribute]):
  with open(file, encoding="utf-8") as f:
    lines = f.readlines()

  counts : dict[str, int] = defaultdict(int)

  erroneous_texts : dict[str, list[str]] = defaultdict(list)

  artefact = ""
  language = "und"

  for line in lines:
    if not line.strip():
      continue
    if line.startswith("&"):
      artefact = line.split("=")[0][1:].strip()
      language = "und"
      continue
    elif line.startswith("#"):
      if line.startswith("#atf: lang"):
        language = line.split()[-1]
      continue
    elif line.startswith(("@", "$", "|", ">")):
      continue
    if " " not in line:
      print("*** No space in", repr(line))
      continue
    number, text = line.split(" ", 1)
    if not number.endswith("."):
      print("*** Bad line number in", line)
    text = text.strip()
    try:
      graphemes = parse_transliteration(text, language)
    except SyntaxError as e:
      error_title = e.msg.split(":")[0]
      erroneous_texts[error_title].append(artefact)
      continue
    for grapheme, language, attributes in graphemes:
      grapheme = grapheme.rstrip("#?!*")
      if not grapheme.strip():
        continue

      if any(c.isupper() for c in grapheme):
        continue
      if "/" in grapheme or "(" in grapheme:
        continue
      if grapheme in ("x", "n"):
        continue
      if language != target_language:
        continue
      if any(attribute in exclude for attribute in attributes):
        continue
      grapheme = grapheme.replace("sz", "š").replace("s,", "ṣ").replace("t,", "ṭ")
      grapheme = grapheme.replace(
          "0", "₀").replace(
          "1", "₁").replace(
          "2", "₂").replace(
          "3", "₃").replace(
          "4", "₄").replace(
          "5", "₅").replace(
          "6", "₆").replace(
          "7", "₇").replace(
          "8", "₈").replace(
          "9", "₉")
      counts[grapheme] += 1

  for error_title, occurrences in erroneous_texts.items():
    print(f"*** {error_title}: {len(occurrences)} in {len(set(occurrences))} texts")
  return counts