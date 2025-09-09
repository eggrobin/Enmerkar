from collections import defaultdict
import re
import enum

VALUE_LETTER = re.compile(r"(?:sz|s,|t,|[abdeghiklmnpqrstuvwyz'šṣṭʾŋ])",)
VALUE_INDEX = re.compile(r"(?:[0-9₀-₉]+|x|ₓ)")
VALUE = re.compile(fr"(?:{VALUE_LETTER.pattern}+{VALUE_INDEX.pattern}?)")

class Extension(enum.Enum):
  # https://oracc.museum.upenn.edu/ns/gdl/1.0/gdltut.html#Words
  # In ATF words are separated by spaces, and graphemes within words are joined
  # by hyphens. Note that periods (.) are only permitted inside compound
  # graphemes.
  DOT_AS_DELIMITER = 0,
  UNICODE = 1,
  # SAAo em dash, represented as --.
  EM_DASH = 2,
  # + between separate ligatured graphemes.
  PLUS_AS_DELIMITER = 3,
  DIŠLESS_NUMBERS = 4,

NAME_LETTER = re.compile(r"(?:SZ|S,|T,|[ABDEGHIKLMNPQRSTUVWYZ'ŠṢṬʾŊ])")
NAME_INDEX = re.compile(r"(?:[0-9₀-₉]+|X|ₓ)")
MODIFIER = re.compile(r"(?:\d+|[fgstnzkrhv])")
ALLOGRAPH = re.compile(r"(?:~[a-wyz0-9]+)")
FORMVARIANT = re.compile(r"(?:\\[a-z0-9]+)")
NAME = re.compile(
  fr"""(?:
      [A-Z][A-Z][A-Z]+\d\d\d
    | {NAME_LETTER.pattern}+{NAME_INDEX.pattern}?(?:@{MODIFIER.pattern})*(?:{ALLOGRAPH.pattern})?
  )""",
  re.VERBOSE)
COMPOUND = re.compile(r"(?:\|[^|<>{}\[\] -]+\|)")
QUALIFIED =  re.compile(
  fr"""(?:
    {VALUE.pattern}
    \(
    (?:{NAME.pattern}
      |{COMPOUND.pattern})
    \)
  )""",
  re.VERBOSE
)

DIŠLESS_NUMBER = re.compile(r"[0-5]?[0-9]")

NUMBER = re.compile(
  fr"""(?:
      (?:n|[\d/]+)
      \(
        (?:{VALUE.pattern}(?:@(?:90|[cvt]))*
          |{NAME.pattern}
          |{COMPOUND.pattern})
      \)
    | {DIŠLESS_NUMBER.pattern}
  )""",
  re.VERBOSE
)

# TODO(egg): Should a value really be allowed as a correction?
ALTERNATIVE = re.compile(
  fr"""(?:
      (?:{NUMBER.pattern}
        |{QUALIFIED.pattern}
        |{VALUE.pattern}
        |{NAME.pattern}
        |{COMPOUND.pattern})
      (?: !
          \(
          (?:{VALUE.pattern}
            |{NAME.pattern}
            |{COMPOUND.pattern})
          \)
        | [#?!*]
        | {FORMVARIANT.pattern}
      )*
  )""",
  re.VERBOSE
)

GRAPHEME = re.compile(
  fr"""(?:
      {ALTERNATIVE.pattern}(?:/{ALTERNATIVE.pattern})*
    | x[#?]*
  )""",
  re.VERBOSE
)

PUNCTUATION = re.compile(
  r"""(?:(?<= )|^)(?:\*|:|:'|:"|:.|::|/)(?:\(P[1-9₁-₉]\))?(?: |$)"""
)

ASCII_DIGRAPHS = re.compile(r"(sz|s,|t,|SZ|S,|T,)")
NON_ASCII = re.compile(r"[^\x00-\x7F]")

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

INTRAWORD_DELIMITER = re.compile(r"--|[-:.+]")
SHIFT = re.compile("%[a-z/-]+")
COMMENT = re.compile(r"\(\#(?:[^#]|\#[^)])*\#\)|\(\$(?:[^$]|\$[^)])*\$\)")

class Token:
  def __init__(self, text: str, after: int):
    self.text = text
    self.after = after

class EndOfText(Token):
  pass

class Grapheme(Token):
  pass

class UnknownMissing(Token):
  pass

class Comment(Token):
  pass

class Space(Token):
  pass

class Delimiter(Token):
  pass

class FieldSeparator(Token):
  pass

class Bracket(Token):
  pass

class LanguageShift(Token):
  pass

TOKENS : list[tuple[re.Pattern[str], type[Token]]] = [
  (COMMENT, Comment),
  (GRAPHEME, Grapheme),
  (re.compile(r"%[a-z]+"), LanguageShift),
  (re.compile(r" +"), Space),
  (re.compile(re.escape("...")), UnknownMissing),
  (INTRAWORD_DELIMITER, Delimiter),
] + [(re.compile(re.escape(c)), FieldSeparator) for c in ("#", '"', "~", "|", "=", "^", "@", "&")
] + [(re.compile(re.escape(t)), Bracket) for a in SpanAttribute for t in ((a.open, a.close) if a.open != a.close else (a.open,))]

# https://oracc.org/doc/help/editinginatf/primer/inlinetutorial/index.html#h_languages
INLINE_LANGUAGE_CODES = {
  "a"    : "akk",
  "akk"  : "akk",
  "eakk" : "akk-x-earakk",
  "oakk" : "akk-x-oldakk",
  "oa"   : "akk-x-oldass",
  "ob"   : "akk-x-oldbab",
  "ma"   : "akk-x-midass",
  "mb"   : "akk-x-midbab",
  "na"   : "akk-x-neoass",
  "nb"   : "akk-x-neobab",
  "sb"   : "akk-x-stdbab",
  "a/n"  : "akk-x-norm",
  "s"    : "sux",
  "e"    : "sux-x-emesal",
}

class Lexer:
  def __init__(self, source: str):
    self.source = source
    self.i = 0
    self.ahead = None

  def accept(self, token: type[Token], text: str|None = None):
    ahead = self.lookahead()
    if isinstance(ahead, token) and (
        text is None or ahead.text == text):
      self.advance()
      return True
    return False

  def lookahead(self) -> Token:
    if self.ahead is None:
      self.ahead = self._next()
    return self.ahead

  def advance(self):
    self.lookahead()
    if self.ahead:
      self.i = self.ahead.after
    self.ahead = None

  def _next(self) -> Token:
    if self.i == len(self.source):
      return EndOfText("", self.i)
    matches : list[tuple[re.Match[str], type[Token]]] = []
    for pattern, t in TOKENS:
      match = pattern.match(self.source, self.i)
      if match:
        matches.append((match, t))
    if not matches:
      self._raise_error(f"Could not recognize token")
    if len(matches) > 1:
      matches = sorted(matches, key=lambda mt: -len(mt[0].group(0)))
      #print(f"Multiple matching tokens {', '.join(f'{token.__name__} {match.group(0)}' for match, token in matches)}: {self.source[:self.i]}☞{self.source[self.i:]}")
    match, t = matches[0]
    return t(match.group(), match.end())

  def _raise_error(self, message: str):
    raise SyntaxError(f"{message}: {self.source[:self.i]}☞{self.source[self.i:]}")

  def raise_syntax_error(self, message: str):
    self._raise_error(f"{message}, got {type(self.lookahead()).__name__}")

def parse_transliteration(source: str):
  lexer = Lexer(source)
  while True:
    parse_word(lexer)
    if not lexer.accept(Space):
      if lexer.accept(EndOfText):
        break
      lexer.raise_syntax_error("Expected space between words")
    continue

def parse_word(lexer: Lexer):
  if lexer.accept(FieldSeparator):
    return
  if lexer.accept(LanguageShift):
    return
  parse_delimited_text(lexer)
  while lexer.accept(Delimiter):
    parse_delimited_text(lexer)

def parse_delimited_text(lexer: Lexer):
  while accept_textual_span_opening(lexer):
    pass
  while accept_determinative(lexer):
    while accept_textual_span_opening(lexer) or accept_textual_span_closing_bracket(lexer):
      pass
  if lexer.accept(Grapheme):
    pass
  elif lexer.accept(UnknownMissing):
    pass
  elif lexer.accept(Comment):
    pass
  else:
    lexer.raise_syntax_error("Expected Grapheme or ...")
  while accept_textual_span_closure(lexer):
    pass
  if accept_textual_span_opening_bracket(lexer):
    if not accept_determinative(lexer):
      lexer.raise_syntax_error("Expected Determinative")
  while accept_determinative(lexer):
    pass
  while accept_textual_span_closure(lexer):
    pass

def accept_determinative(lexer: Lexer):
  if lexer.accept(Bracket, "{"):
    if lexer.accept(LanguageShift):
      if not lexer.accept(Space):
        lexer.raise_syntax_error("Expected space after language shift")
    parse_delimited_determinative_text(lexer)
    while lexer.accept(Delimiter):
      parse_delimited_determinative_text(lexer)
    if not lexer.accept(Bracket, "}"):
      lexer.raise_syntax_error("Expected }")
    return True
  return False

def parse_delimited_determinative_text(lexer: Lexer):
  while accept_textual_span_opening(lexer):
    pass
  if not lexer.accept(Grapheme):
    lexer.raise_syntax_error("Expected Grapheme")
  while accept_textual_span_closure(lexer):
    pass

def accept_textual_span_opening(lexer: Lexer):
  return lexer.accept(Bracket, "_") or accept_textual_span_opening_bracket(lexer)

def accept_textual_span_closure(lexer: Lexer):
  return lexer.accept(Bracket, "_") or accept_textual_span_closing_bracket(lexer)

def accept_textual_span_opening_bracket(lexer: Lexer):
  for bracket in ("[", "(", "<", "<<"):
    if lexer.accept(Bracket, bracket):
      return True
  return False

def accept_textual_span_closing_bracket(lexer: Lexer):
  for bracket in ("]", ")", ">", ">>"):
    if lexer.accept(Bracket, bracket):
      return True
  return False

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
