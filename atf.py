from collections import defaultdict
import re
import enum

VALUE_LETTER = re.compile(r"(?:sz|s,|t,|[abdeghiklmnpqrstuvwyz'])")
VALUE_INDEX = re.compile(r"(?:[0-9]+|x)")
VALUE = re.compile(fr"(?:{VALUE_LETTER.pattern}+{VALUE_INDEX.pattern}?)")


NAME_LETTER = re.compile(r"(?:SZ|S,|T,|[ABDEGHIKLMNPQRSTUVWYZ'])")
NAME_INDEX = re.compile(r"(?:[0-9]+|X)")
MODIFIER = re.compile(r"(?:\d+|[fgstnzkrhv])")
NAME = re.compile(fr"(?:[A-Z][A-Z][A-Z]+\d\d\d|{NAME_LETTER.pattern}+{NAME_INDEX.pattern}?(?:@{MODIFIER.pattern})*)")
COMPOUND = re.compile(r"(?:\|[^|<>{}\[\] -]+\|)")
QUALIFIED =  re.compile(
  fr"(?:{VALUE.pattern}\((?:{NAME.pattern}|{COMPOUND.pattern})\))"
)

NUMBER = re.compile(
  fr"(?:(?:n|[\d/]+)\((?:{VALUE.pattern}(?:@(?:90|[cvt]))*|{NAME.pattern}|{COMPOUND.pattern})\))"
)

# TODO(egg): Should a value really be allowed as a correction?
ALTERNATIVE = re.compile(
  fr"(?:(?:{NUMBER.pattern}|{QUALIFIED.pattern}|{VALUE.pattern}|{NAME.pattern}|{COMPOUND.pattern})(?:!\((?:{VALUE.pattern}|{NAME.pattern}|{COMPOUND.pattern})\)|[#?!*])*)"
)

GRAPHEME = re.compile(
  fr"(?:{ALTERNATIVE.pattern}(?:/{ALTERNATIVE.pattern})*|x\??)"
)

PUNCTUATION = re.compile(
  r"""(?:(?<= )|^)(?:\*|:|:'|:"|:.|::|/)(?: |$)"""
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
  graphemes : list[tuple[str, str, set[SpanAttribute], str|None]] = []
  i = 0
  after_delimiter = " "
  delimiter_before_determinative = None
  delimiter_before_linguistic_gloss = None
  attribute_run_lengths : dict[SpanAttribute, int] = {}
  def start_span(attribute: SpanAttribute):
    if attribute in attribute_run_lengths:
      raise SyntaxError(f"Nested {attribute}: {source[:i]}☞{source[i:]}")
    attribute_run_lengths[attribute] = 0
  def end_span(attribute: SpanAttribute):
    if attribute not in attribute_run_lengths:
      raise SyntaxError(f"Unstarted {attribute}: {source[:i]}☞{source[i:]}")
    del attribute_run_lengths[attribute]
  while i < len(source):
    while source[i] == " ":
      i += 1
      after_delimiter = " "
    match = GRAPHEME.match(source, i)
    if match:
      if (not after_delimiter and
          attribute_run_lengths.get(SpanAttribute.DETERMINATIVE) != 0 and
          attribute_run_lengths.get(SpanAttribute.IMPLIED) != 0 and
          attribute_run_lengths.get(SpanAttribute.LINGUISTIC_GLOSS) != 0):
        raise SyntaxError(f"Missing delimiter: {source[:i]}☞{source[i:]}")
      graphemes.append((match.group(), language, set(attribute_run_lengths), after_delimiter))
      i = match.end()
      after_delimiter = None
      continue
    if source[i] in ("-", ":"):
      if after_delimiter:
        raise SyntaxError(f"Double delimiter: {source[:i]}☞{source[i:]}")
      after_delimiter = source[i]
      i += 1
      continue
    if source[i] == ";":
      # Newline in case, see http://oracc.org/ns/gdl/1.0/gdltut.html#Intrusions.
      i += 1
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
      if SpanAttribute.BROKEN not in attribute_run_lengths:
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
        i += len(attribute.close)
        break
    else:
      if source.startswith(SpanAttribute.LINGUISTIC_GLOSS.open, i):
        start_span(SpanAttribute.LINGUISTIC_GLOSS)
        delimiter_before_linguistic_gloss = after_delimiter
        i += len(SpanAttribute.LINGUISTIC_GLOSS.open)
      elif source.startswith(SpanAttribute.LINGUISTIC_GLOSS.close, i):
        end_span(SpanAttribute.LINGUISTIC_GLOSS)
        after_delimiter = delimiter_before_linguistic_gloss
        i += len(SpanAttribute.LINGUISTIC_GLOSS.close)
      elif source[i] == "{":
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

def get_base(value: str) -> str:
  if "-" in value:
    v = None
    cv, vc = value.split("-", maxsplit=1)
    if "-" in vc:
      v, vc = vc.split("-")
    if not is_cv(cv) and is_vc(vc) and get_vowel(cv) == get_vowel(vc) and (
      not v or (is_v(v) and get_vowel(v) == get_vowel(vc))):
      raise ValueError(value)
    return get_base(cv) + get_base(vc)[1:]
  else:
    return value.rstrip("₀₁₂₃₄₅₆₇₈₉")
def is_consonant(letter: str):
  return letter in set("ʾbdghklmnpqrsṣštṭvwyz")
def is_vowel(letter: str):
  return letter in set("aeui")
def is_v(value: str):
  base = get_base(value)
  return len(base) == 1 and is_vowel(base[0])
def is_cv(value: str):
  base = get_base(value)
  return len(base) == 2 and is_consonant(base[0]) and is_vowel(base[1])
def is_vc(value: str):
  base = get_base(value)
  return len(base) == 2 and is_vowel(base[0]) and is_consonant(base[1])
def is_cvc(value: str):
  base = get_base(value)
  return len(base) == 3 and is_consonant(base[0]) and is_vowel(base[1]) and is_consonant(base[2])
def get_vowel(syllable_value: str, *args: None):
  base = get_base(syllable_value)
  if args:
    return next((v for v in base if is_vowel(v)), *args)
  vowel, = (v for v in base if is_vowel(v))
  return vowel

def get_value_counts(file: str, target_language: str, exclude: set[SpanAttribute]):
  with open(file, encoding="utf-8") as f:
    lines = f.readlines()
  with open(file + ".log", mode="w", encoding="utf-8") as log:
    occurrences : dict[str, list[str]] = defaultdict(list)

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
        print("*** No space in", repr(line), file=log)
        continue
      number, text = line.split(" ", 1)
      if not number.endswith("."):
        print("*** Bad line number", repr(number), "in", line,
              file=log)
      text = text.strip()
      try:
        graphemes = parse_transliteration(text, language)
      except SyntaxError as e:
        print("***", e.msg, file=log)
        error_title = e.msg.split(":")[0]
        erroneous_texts[error_title].append(artefact)
        continue
      previous_graphemes : list[str] = []
      for grapheme, grapheme_language, attributes, after_delimiter in graphemes:
        if after_delimiter != "":
          previous_graphemes = []
        grapheme = grapheme.rstrip("#?!*")
        if not grapheme.strip():
          previous_graphemes = []
          continue

        if any(c.isupper() for c in grapheme):
          previous_graphemes = []
          continue
        if "/" in grapheme or "(" in grapheme:
          previous_graphemes = []
          continue
        if grapheme in ("x", "n"):
          previous_graphemes = []
          continue
        if grapheme_language != target_language:
          previous_graphemes = []
          continue
        if any(attribute in exclude for attribute in attributes):
          previous_graphemes = []
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
        occurrences[grapheme].append(artefact)
        if previous_graphemes and is_vc(grapheme):
          this_vowel = get_vowel(grapheme)
          previous_grapheme = previous_graphemes[-1]
          if get_vowel(previous_grapheme, None) == this_vowel:
            if is_cv(previous_grapheme):
              occurrences[previous_grapheme + "-" + grapheme].append(artefact)
            elif is_v(previous_grapheme) and len(previous_graphemes) >= 2:
              if is_cv(previous_graphemes[-2]) and get_vowel(previous_graphemes[-2]) == this_vowel:
                occurrences[previous_graphemes[-2] + "-" + previous_grapheme + "-" + grapheme].append(artefact)

        previous_graphemes.append(grapheme)

    for error_title, error_occurrences in erroneous_texts.items():
      print(f"*** {error_title}: {len(error_occurrences)} in {len(set(error_occurrences))} texts")
    return occurrences