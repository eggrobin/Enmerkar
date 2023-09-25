# Based on https://build-oracc.museum.upenn.edu/ogsl/aslogslfileformat/index.html as built from
# https://github.com/oracc/ogsl/blob/53952bfcbe2a575f92522562fdff3b8fcfd757ab/00web/asl.xml.

from collections import defaultdict
import difflib
import re
import sys
import textwrap
from typing import Optional, Literal, Tuple

class RawEntry:
  def __init__(self, line: str, parser: "Parser"):
    if not line.startswith("@"):
      parser.raise_error(f"Tag does not start with @: {line}")
    tag, *tail = line.split(maxsplit=1)
    self.tag = tag[1:]
    self.deprecated = self.tag.endswith("-")
    if self.deprecated:
      self.tag = self.tag[:-1]
    self.text = tail[0] if tail else ""

  def validate(self, entry_type, parser):
    if self.tag != entry_type.tag:
      raise parser.raise_error(f"Expected @{entry_type.tag}, got @{self.tag} {self.text}")

class Parser:
  lines: list[str]
  line_number: int
  context: str

  def __init__(self, lines: list[str], context: str):
    self.lines = lines
    self.line_number = 0
    self.context = context

  def peek(self) -> Optional[RawEntry]:
    old_line_number = self.line_number
    entry = self.next()
    self.line_number = old_line_number
    return entry

  def next(self) -> Optional[RawEntry]:
    while self.line_number < len(self.lines):
      line = self.lines[self.line_number]
      self.line_number += 1
      if line.strip():
        result = RawEntry(line.strip(), self)
        break
    else:
      return None
    while self.line_number < len(self.lines):
      line = self.lines[self.line_number]
      if line.startswith("\t") or line.startswith(" "):
        result.text += "\n" + line.strip()
        self.line_number += 1
      else:
        break
    return result

  def raise_error(self, message: str):
    raise SyntaxError(f"{self.context}:{self.line_number}: {message}")


class TextTag:
  tag: str
  text: str

  def __init__(self, text: str):
    self.text = text

  def __str__(self):
    return "@%s\t%s" % (self.tag, "\n\t".join(self.text.splitlines()))

  @classmethod
  def parse(cls, parser: Parser, *args) -> "TextTag":
    entry = parser.next()
    entry.validate(cls, parser)
    return cls(entry.text)

# Undocumented.
class Fake(TextTag):
  tag = "fake"

class PlusName(TextTag):
  tag = "pname"

class Note(TextTag):
  tag = "note"

class InternalNote(Note):
  tag = "inote"

class Literature(Note):
  tag = "lit"

# Not actually arbitrary text.
class Reference(Note):
  tag = "ref"

# TODO(egg): Structure the Unicode fields.

class UnicodeName(TextTag):
  tag = "uname"

class UnicodeSequence(TextTag):
  tag = "useq"

class UnicodeCuneiform(TextTag):
  tag = "ucun"

class UnicodeAge(TextTag):
  tag = "uage"

class UnicodeNote(TextTag):
  tag = "unote"

class UnicodeMap(TextTag):
  tag = "umap"

class UnicodeSequence(TextTag):
  tag = "useq"

class SourceRange:
  def __init__(self, text: str, base: Optional[Literal[10, 16]] = None):
    self.hex_prefix = text.startswith("0x")
    self.base = base or (16 if self.hex_prefix else 10)
    if '-' in text:
      first, last = text.split('-')
      self.first = int(first, self.base)
      self.last = int(last, self.base)
      self.suffix = ""
      self.width = 0
    else:
      if self.hex_prefix:
        text = text[2:]
      if self.base == 10:
        number, self.suffix = re.split(r"(?!\d)", text, maxsplit=1)
      else:
        number = text
        self.suffix = ""
      self.width = len(number)
      self.first = int(number, self.base)
      self.last = self.first

  def __eq__(self, other):
    return (isinstance(other, SourceRange) and
            self.first == other.first and
            self.last == other.last and
            self.suffix == other.suffix)

  def __hash__(self):
    return hash((self.first, self.last, self.suffix))

  def __iter__(self):
    yield from (SourceRange(self.format_number(n) + self.suffix, self.base)
                for n in range(self.first, self.last + 1))

  def __len__(self):
    return self.last - self.first + 1

  def __contains__(self, n: "SourceRange"):
    return n.suffix == self.suffix and n.first >= self.first and n.last <= self.last

  def format_number(self, n: int):
    if self.base == 16:
      if self.hex_prefix:
        return f"0x%0{self.width}X" % n
      else:
        return f"%0{self.width}X" % n
    else:
      return f"%0{self.width}d" % n

  def __str__(self):
    if self.first == self.last:
      return self.format_number(self.first) + self.suffix
    else:
      return self.format_number(self.first) + "-" + self.format_number(self.last)

class Source:
  """A classical sign list, e.g., RÉC, MZL, etc.

  We use the Unicode term source so as to avoid conflicts and confusion with
  both the SignList type, representing the OGSL, and with Python lists.
  """
  tag = "listdef"

  abbreviation: str
  numbers: list[list[SourceRange]]
  notes: list[Note]
  base: Literal[10, 16]

  def ranges(self):
    yield from (r for line in self.numbers for r in line)

  def __init__(self, abbreviation: str, numbers: list[list[SourceRange]]):
    self.abbreviation = abbreviation
    self.numbers = numbers
    self.notes = []
    self.base = numbers[0][0].base
    if not all(r.base == self.base for line in numbers for r in line):
      raise ValueError(f"All list numbers do not have the same base in {self.abbreviation}")

  @classmethod
  def parse(cls, parser: Parser) -> "Source":
    entry = parser.next()
    entry.validate(cls, parser)
    abbreviation, numbers = entry.text.split(maxsplit=1)
    result = cls(abbreviation, [[SourceRange(r) for r in line.split()] for line in numbers.splitlines()])
    while entry := parser.peek():
      for entry_type in (Note, *Note.__subclasses__()):
        if entry.tag == entry_type.tag:
          result.notes.append(entry_type.parse(parser))
          break
      else:
        break
    return result

  def __str__(self):
    return "@%s %s %s\n%s" % (
      self.tag,
      self.abbreviation,
      "\n\t".join(' '.join(str(number) for number in line) for line in self.numbers),
      "\n".join(str(note) for note in self.notes))

class Value:
  tag = "v"
  deprecated: bool
  language: Optional[str]
  text: str
  notes: list[Note]

  def __init__(self, text, language: Optional[str] = None, deprecated: bool = False) -> None:
    self.deprecated = deprecated
    self.language = language
    self.text = text
    self.notes = []

  def __str__(self):
    return "\n".join((
      f"@v{'-' if self.deprecated else ''}\t{'%'+self.language + ' ' if self.language else ''}{self.text}",
      *(str(note) for note in self.notes)))

  @classmethod
  def parse(cls, parser: Parser):
    entry = parser.next()
    language = None
    args = entry.text
    if args.startswith('%'):
      language, args = args.split(maxsplit=1)
      language = language[1:]
    result = Value(args, language, entry.deprecated)
    while entry := parser.peek():
      for entry_type in (Note, *Note.__subclasses__()):
        if entry.tag == entry_type.tag:
          result.notes.append(entry_type.parse(parser))
          break
      else:
        break
    return result

class SourceReference:
  tag = "list"
  source: Source
  number: SourceRange
  questionable: bool

  def __init__(self, source: Source, number: SourceRange, questionable: bool = False):
    self.source = source
    self.number = number
    self.questionable = questionable
    if len(number) != 1:
      raise ValueError(f"SourceReference must have a single {source.abbreviation} number, got {number}")
    if not any(number in r for r in source.ranges()):
      print(f"*** Undeclared number {source.abbreviation}{number}", file=sys.stderr)

  def __str__(self):
    return f"@list\t{self.source.abbreviation}{self.number}"

  @classmethod
  def parse(cls, parser: Parser, sources: dict[str, Source]):
    entry = parser.next()
    entry.validate(cls, parser)
    abbreviation, number = re.split(r"(?=\d)", entry.text, maxsplit=1)
    source = sources[abbreviation]
    return cls(source, SourceRange(number.rstrip("?"), source.base), number.endswith("?"))

class System:
  tag = "sysdef"
  name: str
  notes: list[Note]

  def __init__(self, name: str):
    self.name = name
    self.notes = []

  def __str__(self):
    return "\n".join((
      f"@{self.tag} {self.name}",
      *(str(note) for note in self.notes)))

  @classmethod
  def parse(cls, parser: Parser) -> "System":
    entry = parser.next()
    entry.validate(cls, parser)
    result = cls(entry.text)
    while entry := parser.peek():
      for entry_type in (Note, *Note.__subclasses__()):
        if entry.tag == entry_type.tag:
          result.notes.append(entry_type.parse(parser))
          break
      else:
        break
    return result

class SystemBinding(TextTag):
  tag = "sys"

class SignLike:
  pass

class SourceOnly(SignLike):
  tag = "lref"
  name = str
  notes: list[Note]

  def __init__(self, name: str):
    self.name = name
    self.notes = []

  def __str__(self):
    return "\n".join((
      f"@{self.tag}\t{self.name}",
      *(str(note) for note in self.notes)))

  @classmethod
  def parse(cls, parser: Parser, sources: dict[str, Source]) -> "Form":
    entry = parser.next()
    entry.validate(cls, parser)
    result = cls(entry.text)
    result.deprecated = entry.deprecated

    while entry := parser.peek():
      for entry_type in (Note, *Note.__subclasses__()):
        if entry.tag == entry_type.tag:
          result.notes.append(entry_type.parse(parser))
          break
      else:
        break
    return result

class CompoundOnly(SignLike):
  tag = "compoundonly"
  name = str
  notes: list[Note]

  def __init__(self, name: str):
    self.name = name
    self.notes = []

  def __str__(self):
    return "\n".join((
      f"@{self.tag}\t{self.name}",
      *(str(note) for note in self.notes)))

  @classmethod
  def parse(cls, parser: Parser, sources: dict[str, Source]) -> "Form":
    entry = parser.next()
    entry.validate(cls, parser)
    result = cls(entry.text)
    result.deprecated = entry.deprecated

    while entry := parser.peek():
      for entry_type in (Note, *Note.__subclasses__()):
        if entry.tag == entry_type.tag:
          result.notes.append(entry_type.parse(parser))
          break
      else:
        break
    return result

# Omitting @sref which is not actually used.

class Form:
  tag = "form"
  deprecated: bool
  names: list[str]
  pname: Optional[str]
  fake: Optional[Fake]
  sources: list[SourceReference]
  notes: list[Note]
  # TODO(egg): Structure.
  unicode_name: Optional[UnicodeName]
  unicode_sequence: Optional[UnicodeSequence]
  unicode_cuneiform: Optional[UnicodeCuneiform]
  unicode_age: Optional[UnicodeAge]
  unicode_note: Optional[UnicodeNote]
  unicode_map: Optional[UnicodeNote]

  values: list[Value]
  # system* is missing from formblock in the documentation, but really is used.
  systems: list[SystemBinding]

  def __init__(self, name: str):
    self.names = [name]
    self.pname = None
    self.sources = []
    self.values = []
    self.systems = []
    self.notes = []
    self.unicode_name = None
    self.unicode_sequence = None
    self.unicode_cuneiform = None
    self.unicode_age = None
    self.unicode_note = None
    self.unicode_map = None
    self.fake = None

  @classmethod
  def check_end(cls, parser: Parser, entry: RawEntry):
    if entry.tag == "@":
      if entry.text:
        parser.raise_error(f"Unexpected args {entry.text} on endform")
      parser.next()
      return True
    return False

  def parse_extension(self, parser: Parser, sources: dict[str, Source]) -> bool:
    return False

  def form_components_str(self):
    return "\n".join(lines for lines in (
        str(self.pname) if self.pname else None,
        "\n".join("@aka\t%s" % name for name in self.names[1:]),
        str(self.fake) if self.fake else None,
        "\n".join(str(source) for source in self.sources if source.source.abbreviation != "U+"),
        "\n".join(str(note) for note in self.notes),
        str(self.unicode_name) if self.unicode_name else None,
        "\n".join(str(source) for source in self.sources if source.source.abbreviation == "U+"),
        str(self.unicode_sequence) if self.unicode_sequence else None,
        str(self.unicode_cuneiform) if self.unicode_cuneiform else None,
        str(self.unicode_map) if self.unicode_map else None,
        str(self.unicode_age) if self.unicode_age else None,
        str(self.unicode_note) if self.unicode_note else None,
        "\n".join(str(value) for value in self.values),
        "\n".join(str(system) for system in self.systems)) if lines)

  def __str__(self):
    return "\n".join(lines for lines in (
        f"@{self.tag}{'-' if self.deprecated else ''} {self.names[0]}",
        self.form_components_str(),
        "@@") if lines)


  @classmethod
  def parse(cls, parser: Parser, sources: dict[str, Source]) -> "Form":
    entry = parser.next()
    entry.validate(cls, parser)
    result = cls(entry.text)
    result.deprecated = entry.deprecated

    while entry := parser.peek():
      if cls.check_end(parser, entry):
        break
      if entry.tag == "aka":
        result.names.append(entry.text)
        parser.next()
      elif entry.tag == PlusName.tag:
        result.pname = PlusName.parse(parser)
      elif entry.tag == SourceReference.tag:
        result.sources.append(SourceReference.parse(parser, sources))
      elif entry.tag == UnicodeName.tag:
        result.unicode_name = UnicodeName.parse(parser)
      elif entry.tag == UnicodeSequence.tag:
        result.unicode_sequence = UnicodeSequence.parse(parser)
      elif entry.tag == UnicodeCuneiform.tag:
        result.unicode_cuneiform = UnicodeCuneiform.parse(parser)
      elif entry.tag == UnicodeAge.tag:
        result.unicode_age = UnicodeAge.parse(parser)
      elif entry.tag == UnicodeNote.tag:
        result.unicode_note = UnicodeNote.parse(parser)
      elif entry.tag == UnicodeMap.tag:
        result.unicode_map = UnicodeMap.parse(parser)
      elif entry.tag == Value.tag:
        result.values.append(Value.parse(parser))
      elif entry.tag == SystemBinding.tag:
        result.systems.append(SystemBinding.parse(parser))
      elif entry.tag == Fake.tag:
        result.fake = Fake.parse(parser)
      else:
        for entry_type in (Note, *Note.__subclasses__()):
          if entry.tag == entry_type.tag:
            result.notes.append(entry_type.parse(parser))
            break
        else:
          if not result.parse_extension(parser, sources):
            parser.raise_error(f"Unexpected tag @{entry.tag} {entry.text}")
    else:
      parser.raise_error(f"Reached end of file within {cls.__name__} block")
    return result

class Sign(Form, SignLike):
  tag = "sign"
  forms: list[Form]

  def __str__(self):
    return "\n".join(lines for lines in (
        f"@{self.tag}{'-' if self.deprecated else ''} {self.names[0]}",
        self.form_components_str(),
        "\n".join(str(form) for form in self.forms),
        "@end sign") if lines)

  def __init__(self, name):
    super().__init__(name)
    self.forms = []

  def parse_extension(self, parser: Parser, sources: dict[str, Source]):
    entry = parser.peek()
    if entry.tag == Form.tag:
      self.forms.append(Form.parse(parser, sources))
      return True
    return False

  @classmethod
  def check_end(cls, parser: Parser, entry: RawEntry):
    if entry.tag == "end" and entry.text == "sign":
      parser.next()
      return True
    return False

class SignList:
  tag = "signlist"
  name: str
  # Not documented, nor really used, except that one of the listdefs is
  # @inoted out.
  notes: list[Note]
  sources: dict[str, Source]
  systems: dict[str, System]
  signs: list[SignLike]
  signs_by_name: dict[str, SignLike]
  forms_by_name: defaultdict[str, list[SignLike]]
  forms_by_source: defaultdict[Tuple[Source, SourceRange], list[SignLike]]

  def __init__(self, name: str):
    self.name = name
    self.notes = []
    self.sources = {}
    self.systems = {}
    self.signs = []
    self.signs_by_name = {}
    self.forms_by_name = defaultdict(list)
    self.forms_by_source = defaultdict(list)

  def add_source(self, source: Source):
    self.sources[source.abbreviation] = source

  def add_system(self, system: System):
    self.systems[system.name] = system

  def add_sign(self, sign: SignLike, parser: Parser):
    self.signs.append(sign)
    if isinstance(sign, Sign):
      for name in sign.names:
        self.forms_by_name[name].append(sign)
      for s in sign.sources:
        self.forms_by_source[(s.source, s.number)].append(sign)
      for form in sign.forms:
        for name in form.names:
          self.forms_by_name[name].append(form)
        for s in form.sources:
          self.forms_by_source[(s.source, s.number)].append(form)
    if isinstance(sign, Form):
      names = sign.names
    else:
      names = [sign.name]
    for name in names:
      if name in self.signs_by_name:
        if self.signs_by_name[name].deprecated and not sign.deprecated:
          del self.signs_by_name[name]
        elif not self.signs_by_name[name] and sign.deprecated:
          return
        else:
          parser.raise_error(
              "Duplicate sign %s. Existing:\n%s\nNew:\n%s" % (
                  name,
                  textwrap.indent(str(self.signs_by_name[name]), '  '),
                  textwrap.indent(str(sign), '  ')))
      self.signs_by_name[name] = sign

  def __str__(self):
    return "\n\n".join((
      f"@{self.tag} {self.name}",
      "\n\n".join(str(note) for note in self.notes),
      "\n\n".join(str(source) for source in self.sources.values()),
      "\n\n".join(str(system) for system in self.systems.values()),
      "\n\n".join(str(sign) for sign in self.signs)))

  @classmethod
  def parse(cls, parser: Parser) -> "SignList":
    entry = parser.next()
    entry.validate(cls, parser)
    result = cls(entry.text)

    while entry := parser.peek():
      if entry.tag == InternalNote.tag:
        result.notes.append(InternalNote.parse(parser))
      elif entry.tag == Source.tag:
        result.add_source(Source.parse(parser))
      elif entry.tag == System.tag:
        result.add_system(System.parse(parser))
      else:
        for entry_type in SignLike.__subclasses__():
          if entry.tag == entry_type.tag:
            result.add_sign(entry_type.parse(parser, result.sources), parser)
            break
        else:
          parser.raise_error(f"Expected one of {SignLike.__subclasses__()}, got {entry.tag}")
    return result

with open(r"..\ogsl\00lib\ogsl.asl", encoding="utf-8") as f:
  original_lines = f.read().splitlines()
  ogsl = SignList.parse(Parser(original_lines, "ogsl.asl"))

print("\n".join(difflib.unified_diff(
    original_lines, str(ogsl).splitlines(),
    fromfile="ogsl.asl", tofile="formatted")))
if str(SignList.parse(Parser(str(ogsl).splitlines(), "str(ogsl)"))) != str(ogsl):
  raise ValueError("Not idempotent")

for l in ogsl.sources.values():
  missing = []
  for r in l.ranges():
    for n in r:
      if (l, n) not in ogsl.forms_by_source:
        if not n.suffix and any(m.suffix and m.first == n.first for r in l.ranges() for m in r):
          continue
        missing.append(n)
  if missing:
    print(f"*** {len(missing)} missing numbers from {l.abbreviation}", file=sys.stderr)
  else:
    print(f"--- {len(missing)} missing numbers from {l.abbreviation}", file=sys.stderr)
  if len(missing) < 20:
    print(f"***   {' '.join(str(n) for n in missing)}", file=sys.stderr)
