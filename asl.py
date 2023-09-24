# Based on https://build-oracc.museum.upenn.edu/ogsl/aslogslfileformat/index.html as built from
# https://github.com/oracc/ogsl/blob/53952bfcbe2a575f92522562fdff3b8fcfd757ab/00web/asl.xml.

import re
from typing import Optional, Sequence, Tuple

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
    entry = self.entry()
    self.line_number = old_line_number
    return entry

  def entry(self) -> Optional[RawEntry]:
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
    entry = parser.entry()
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

class SourceNumber:
  pass

class Source:
  """A classical sign list, e.g., RÉC, MZL, etc.

  We use the Unicode term source so as to avoid conflicts and confusion with
  both the SignList type, representing the OGSL, and with Python lists.
  """
  tag = "listdef"
  
  abbreviation: str
  numbers: set[SourceNumber]  # TODO(egg): Represent ranges etc. and keep the line structure.
  notes: list[Note]
  
  def __init__(self, abbreviation: str, numbers: set[SourceNumber]):
    self.abbreviation = abbreviation
    self.numbers = numbers
    self.notes = []

  @classmethod
  def parse(cls, parser: Parser) -> "Source":
    entry = parser.entry()
    entry.validate(cls, parser)
    abbreviation, numbers = entry.text.split(maxsplit=1)
    result = cls(abbreviation, numbers)    
    while entry := parser.peek():
      for entry_type in (Note, *Note.__subclasses__()):
        if entry.tag == entry_type.tag:
          result.notes.append(entry_type.parse(parser))
          break
      else:
        break
    return result

  def __str__(self):
    return "@%s %s\n%s" % (
      self.tag,
      "\n\t".join(self.numbers.splitlines()),
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
    return f"@v{'-' if self.deprecated else ''}\t{'%'+self.language + ' ' if self.language else ''}{self.text}"

  @classmethod
  def parse(cls, parser: Parser):
    entry = parser.entry()
    language = None
    args = entry.text
    if args.startswith('%'):
      language, args = args.split(maxsplit=1)
      language = language[1:]
    result = Value(args, language, entry.deprecated)
    for entry_type in (Note, *Note.__subclasses__()):
      if entry.tag == entry_type.tag:
        result.notes.append(entry.parse(parser))
    return result

class SourceReference:
  tag = "list"
  source: Source
  number: SourceNumber

  def __init__(self, source: Source, number: SourceNumber):
    self.source = source
    self.number = number

  def __str__(self):
    return f"@list\t{self.source.abbreviation}{self.number}"

  @classmethod
  def parse(cls, parser: Parser, sources: dict[str, Source]):
    entry = parser.entry()
    entry.validate(cls, parser)
    abbreviation, number = re.split(r"(?=\d)", entry.text, maxsplit=1)
    return cls(sources[abbreviation], number)
    
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
    entry = parser.entry()
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

class SourceOnly(SignLike, TextTag):
  tag = "lref"

class CompoundOnly(SignLike):
  tag = "compoundonly"
  text = str
  notes: list[Note]

  def __init__(self, text: str):
    self.text = text
    self.notes = []

  def __str__(self):
    return "\n".join((
      f"@{self.tag} {self.text}",
      *(str(note) for note in self.notes)))
  
  @classmethod
  def parse(cls, parser: Parser, sources: dict[str, Source]) -> "Form":
    entry = parser.entry()
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

  @classmethod
  def check_end(cls, parser: Parser, entry: RawEntry):
    if entry.tag == "@":
      if entry.text:
        parser.raise_error(f"Unexpected args {entry.text} on endform")
      parser.entry()
      return True
    return False

  def parse_extension(self, parser: Parser, sources: dict[str, Source]) -> bool:
    return False

  def form_components_str(self):
    return "\n".join(lines for lines in (
        "\n".join("@aka %s" % name for name in self.names[1:]),
        "\n".join(str(source) for source in self.sources),
        "\n".join(str(note) for note in self.notes),
        str(self.unicode_name) if self.unicode_name else None,
        str(self.unicode_sequence) if self.unicode_sequence else None,
        str(self.unicode_cuneiform) if self.unicode_cuneiform else None,
        str(self.unicode_map) if self.unicode_map else None,
        str(self.unicode_age) if self.unicode_age else None,
        str(self.unicode_note) if self.unicode_note else None,
        "\n".join(str(value) for value in self.values),
        "\n".join(str(system) for system in self.systems)) if lines)

  def __str__(self):
    return "\n".join(lines for lines in (
        f"@{self.tag} {self.names[0]}",
        self.form_components_str(),
        "@@") if lines)


  @classmethod
  def parse(cls, parser: Parser, sources: dict[str, Source]) -> "Form":
    entry = parser.entry()
    entry.validate(cls, parser)
    result = cls(entry.text)
    result.deprecated = entry.deprecated

    while entry := parser.peek():
      if cls.check_end(parser, entry):
        break
      if entry.tag == "aka":
        result.names.append(entry.text)
        parser.entry()
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
        result.unicode_note = UnicodeMap.parse(parser)
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
        f"@{self.tag} {self.names[0]}",
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
      parser.entry()
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

  def __init__(self, name: str):
    self.name = name
    self.notes = []
    self.sources = {}
    self.systems = {}
    self.signs = []

  def add_source(self, source: Source):
    self.sources[source.abbreviation] = source
    
  def add_system(self, system: System):
    self.systems[system.name] = system

  def add_sign(self, sign: Sign):
    self.signs.append(sign)

  def __str__(self):
    return "\n\n".join((
      f"@{self.tag} {self.name}",
      "\n\n".join(str(note) for note in self.notes),
      "\n\n".join(str(source) for source in self.sources.values()),
      "\n\n".join(str(system) for system in self.systems.values()),
      "\n\n".join(str(sign) for sign in self.signs)))

  @classmethod
  def parse(cls, parser: Parser) -> "SignList":
    entry = parser.entry()
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
            result.signs.append(entry_type.parse(parser, result.sources))
            break
        else:
          parser.raise_error(f"Expected one of {SignLike.__subclasses__()}, got {entry.tag}")
    return result

with open(r"..\ogsl\00lib\ogsl.asl", encoding="utf-8") as f:
  print(SignList.parse(Parser(f.readlines(), "ogsl.asl")))
