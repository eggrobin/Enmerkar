# Based on http://oracc.org/osl/asloslfileformat/index.html.

from collections import defaultdict
import datetime
import difflib
import re
import sys
import textwrap
from typing import DefaultDict, Optional, Literal, Tuple, TypeVar
import subprocess
import unicodedata

class Tag:
  tag: str

class RawEntry:
  def __init__(self, line: str, parser: "Parser"):
    if not line.startswith("@"):
      parser.raise_error(f"Tag does not start with @: {line}")
    tag, *tail = re.split(r"[ \t]+", line, maxsplit=1)
    self.tag = tag[1:]
    self.default = self.tag.endswith("+")
    self.deprecated = self.tag.endswith("-")
    if self.default or self.deprecated:
      self.tag = self.tag[:-1]
    self.text = tail[0] if tail else ""

  def validate(self, entry_type: type[Tag], parser: "Parser"):
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
      if line.strip(" \t"):
        result = RawEntry(line.strip(" \t"), self)
        break
    else:
      return None
    while self.line_number < len(self.lines):
      line = self.lines[self.line_number]
      if line.startswith("\t") or line.startswith(" "):
        result.text += "\n" + line.strip(" \t")
        self.line_number += 1
      else:
        break
    return result

  def next_expecting(self, cls: type[Tag]) -> RawEntry:
    entry = self.next()
    if not entry:
      self.raise_error(f"Expected @{cls.tag} at end of file")
    entry.validate(cls, self)
    return entry

  def raise_error(self, message: str):
    raise SyntaxError(f"{self.context}:{self.line_number}: {message}")

TextTagSubclass = TypeVar("TextTagSubclass", bound="TextTag")

class TextTag(Tag):
  tag: str
  text: str

  def __init__(self, text: str):
    self.text = text

  def __str__(self):
    return "@%s\t%s" % (self.tag, "\n\t".join(self.text.splitlines()))

  @classmethod
  def parse(cls: type[TextTagSubclass], parser: Parser) -> TextTagSubclass:
    entry = parser.next_expecting(cls)
    return cls(entry.text)

# Undocumented.
class Fake(TextTag):
  tag = "fake"

class OID(TextTag):
  tag = "oid"

class PlusName(TextTag):
  tag = "pname"

class Note(TextTag):
  tag = "note"

class InternalNote(Note):
  tag = "inote"

class Literature(Note):
  tag = "lit"

class Ligature(TextTag):
  tag = "liga"

class Project(TextTag):
  tag = "project"

class Domain(TextTag):
  tag = "domain"

class ScriptDef(TextTag):
  tag = "scriptdef"

class Script(TextTag):
  tag = "script"

class Images(TextTag):
  tag = "images"

# Not actually arbitrary text.
class Reference(Note):
  tag = "ref"

# TODO(egg): Structure the Unicode fields.

class UnicodeName(TextTag):
  tag = "uname"

class UnicodePrivateUseArea(TextTag):
  tag = "upua"

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
  base: Literal[10, 16]

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

  def __eq__(self, other: object):
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

class Source(Tag):
  """A classical sign list, e.g., RÉC, MZL, etc.

  We use the Unicode term source so as to avoid conflicts and confusion with
  both the SignList type, representing the OSL, and with Python lists.
  """
  tag = "listdef"

  abbreviation: str
  range_lines: list[list[SourceRange]]
  notes: list[Note]
  base: Literal[10, 16]

  def __init__(self, abbreviation: str, range_lines: list[list[SourceRange]]):
    self.abbreviation = abbreviation
    self.range_lines = range_lines
    self.notes = []
    self.base = next(self.ranges()).base
    if not all(r.base == self.base for line in range_lines for r in line):
      raise ValueError(f"All list numbers do not have the same base in {self.abbreviation}")

  def ranges(self):
    yield from (r for line in self.range_lines for r in line)

  def __iter__(self):
    for r in self.ranges():
      yield from r

  def __contains__(self, n: "SourceRange"):
    return any(n in r for r in self.ranges())

  @classmethod
  def parse(cls, parser: Parser) -> "Source":
    entry = parser.next_expecting(cls)
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
      "\n\t".join(' '.join(str(number) for number in line) for line in self.range_lines),
      "\n".join(str(note) for note in self.notes))

class Value(Tag):
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
    entry = parser.next_expecting(cls)
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

class SourceReference(Tag):
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
    if number not in source:
      print(f"*** Undeclared number {source.abbreviation}{number}", file=sys.stderr)

  def __str__(self):
    return f"@list\t{self.source.abbreviation}{self.number}{'?' if self.questionable else ''}"

  @classmethod
  def parse(cls, parser: Parser, sources: dict[str, Source]):
    entry = parser.next_expecting(cls)
    abbreviation, number = re.split(r"(?=\d)|(?<=\+)", entry.text, maxsplit=1)
    source = sources[abbreviation]
    return cls(source, SourceRange(number.rstrip("?"), source.base), number.endswith("?"))

class System(Tag):
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
    entry = parser.next_expecting(cls)
    result = cls(entry.text)
    while entry := parser.peek():
      for entry_type in (Note, *Note.__subclasses__()):
        if entry.tag == entry_type.tag:
          result.notes.append(entry_type.parse(parser))
          break
      else:
        break
    return result

class LinkType(Tag):
  tag = "linkdef"
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
  def parse(cls, parser: Parser) -> "LinkType":
    entry = parser.next_expecting(cls)
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

class Link(Tag):
  tag = "link"
  system: str
  identifier: str
  url: str

  def __init__(self, system: str, identifier: str, url: str):
    self.system = system
    self.identifier = identifier
    self.url = url

  def __str__(self):
    return f"@{self.tag} {self.system} {self.identifier} {self.url}"

  @classmethod
  def parse(cls, parser: Parser, *args) -> "Link":
    entry = parser.next_expecting(cls)
    system, identifier, url = entry.text.split(maxsplit=2)
    return cls(system, identifier, url)

class SignLike:
  pass

class SourceOnly(Tag, SignLike):
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
    entry = parser.next_expecting(cls)
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

class CompoundOnly(Tag, SignLike):
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
    entry = parser.next_expecting(cls)
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

class Form(Tag):
  tag = "form"
  oid: Optional[OID]
  deprecated: bool
  default: bool
  names: list[str]
  pname: Optional[PlusName]
  fake: Optional[Fake]
  sources: list[SourceReference]
  notes: list[Note]
  ligatures: list[Ligature]
  # TODO(egg): Structure.
  unicode_name: Optional[UnicodeName]
  unicode_sequence: Optional[UnicodeSequence]
  unicode_pua: Optional[UnicodePrivateUseArea]
  unicode_cuneiform: Optional[UnicodeCuneiform]
  unicode_age: Optional[UnicodeAge]
  unicode_note: Optional[UnicodeNote]
  unicode_map: Optional[UnicodeMap]
  script: Optional[Script]

  sign: Optional["Sign"]

  values: list[Value]
  # system* is missing from formblock in the documentation, but really is used.
  systems: list[SystemBinding]
  links: list[Link]

  def __init__(self, name: str):
    self.oid = None
    self.names = [name]
    self.pname = None
    self.sources = []
    self.values = []
    self.systems = []
    self.links = []
    self.notes = []
    self.ligatures = []
    self.unicode_name = None
    self.unicode_pua = None
    self.unicode_sequence = None
    self.unicode_cuneiform = None
    self.unicode_age = None
    self.unicode_note = None
    self.unicode_map = None
    self.script = None
    self.fake = None
    self.sign = None

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
        str(self.oid) if self.oid else None,
        str(self.pname) if self.pname else None,
        "\n".join("@aka\t%s" % name for name in self.names[1:]),
        str(self.fake) if self.fake else None,
        "\n".join(str(source) for source in self.sources if source.source.abbreviation != "U+"),
        "\n".join(str(note) for note in self.notes),
        str(self.unicode_name) if self.unicode_name else None,
        "\n".join(str(source) for source in self.sources if source.source.abbreviation == "U+"),
        str(self.unicode_pua) if self.unicode_pua else None,
        str(self.unicode_sequence) if self.unicode_sequence else None,
        str(self.unicode_cuneiform) if self.unicode_cuneiform else None,
        str(self.unicode_map) if self.unicode_map else None,
        str(self.unicode_age) if self.unicode_age else None,
        str(self.unicode_note) if self.unicode_note else None,
        str(self.script) if self.script else None,
        "\n".join(str(value) for value in self.values),
        "\n".join(str(system) for system in self.systems),
        "\n".join(str(link) for link in self.links),
        "\n".join(str(ligature) for ligature in self.ligatures)) if lines)

  def __str__(self):
    return "\n".join(lines for lines in (
        f"@{self.tag}{'-' if self.deprecated else '+' if self.default else ''} {self.names[0]}",
        self.form_components_str(),
        "@@") if lines)


  @classmethod
  def parse(cls, parser: Parser, sources: dict[str, Source]) -> "Form":
    entry = parser.next_expecting(cls)
    result = cls(entry.text)
    result.deprecated = entry.deprecated
    result.default = entry.default

    while entry := parser.peek():
      if cls.check_end(parser, entry):
        break
      if entry.tag == "aka":
        result.names.append(entry.text)
        parser.next()
      elif entry.tag == OID.tag:
        result.oid = OID.parse(parser)
      elif entry.tag == PlusName.tag:
        result.pname = PlusName.parse(parser)
      elif entry.tag == SourceReference.tag:
        result.sources.append(SourceReference.parse(parser, sources))
      elif entry.tag == UnicodeName.tag:
        result.unicode_name = UnicodeName.parse(parser)
      elif entry.tag == UnicodeSequence.tag:
        result.unicode_sequence = UnicodeSequence.parse(parser)
      elif entry.tag == UnicodePrivateUseArea.tag:
        result.unicode_pua = UnicodePrivateUseArea.parse(parser)
      elif entry.tag == UnicodeCuneiform.tag:
        result.unicode_cuneiform = UnicodeCuneiform.parse(parser)
      elif entry.tag == UnicodeAge.tag:
        result.unicode_age = UnicodeAge.parse(parser)
      elif entry.tag == UnicodeNote.tag:
        result.unicode_note = UnicodeNote.parse(parser)
      elif entry.tag == UnicodeMap.tag:
        result.unicode_map = UnicodeMap.parse(parser)
      elif entry.tag == Script.tag:
        result.script = Script.parse(parser)
      elif entry.tag == Value.tag:
        result.values.append(Value.parse(parser))
      elif entry.tag == SystemBinding.tag:
        result.systems.append(SystemBinding.parse(parser))
      elif entry.tag == Link.tag:
        result.links.append(Link.parse(parser))
      elif entry.tag == Fake.tag:
        result.fake = Fake.parse(parser)
      elif entry.tag == Ligature.tag:
        result.ligatures.append(Ligature.parse(parser))
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
    result.sources = sorted(result.sources, key=lambda s: s.source.abbreviation)
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
      form = Form.parse(parser, sources)
      form.sign = self
      self.forms.append(form)
      return True
    return False

  @classmethod
  def check_end(cls, parser: Parser, entry: RawEntry):
    if entry.tag == "end" and entry.text == "sign":
      parser.next()
      return True
    return False

class Pcun(Form, SignLike):
  tag = "pcun"
  forms: list[Form]

  def __str__(self):
    return "\n".join(lines for lines in (
        f"@{self.tag}{'-' if self.deprecated else ''} {self.names[0]}",
        self.form_components_str(),
        "\n".join(str(form) for form in self.forms),
        "@end pcun") if lines)

  def __init__(self, name):
    super().__init__(name)
    self.forms = []

  def parse_extension(self, parser: Parser, sources: dict[str, Source]):
    entry = parser.peek()
    if entry.tag == Form.tag:
      form = Form.parse(parser, sources)
      form.sign = self
      self.forms.append(form)
      return True
    return False

  @classmethod
  def check_end(cls, parser: Parser, entry: RawEntry):
    if entry.tag == "end" and entry.text == "pcun":
      parser.next()
      return True
    return False

class SignList(Tag):
  tag = "signlist"
  project: Project
  domain: Domain
  name: str
  # Not documented, nor really used, except that one of the listdefs is
  # @inoted out.
  notes: list[Note]
  sources: dict[str, Source]
  systems: dict[str, System]
  scripts: list[ScriptDef]
  images: list[Images]
  signs: list[SignLike]
  signs_by_name: dict[str, SignLike]
  forms_by_name: defaultdict[str, list[Form]]
  forms_by_source: defaultdict[Source, defaultdict[SourceRange, list[Form]]]
  revision: str|None = None
  date: datetime.datetime|None = None

  def __init__(self, project: Project, name: str, domain: Domain):
    self.project = project
    self.name = name
    self.domain = domain
    self.notes = []
    self.sources = {}
    self.systems = {}
    self.link_types = {}
    self.scripts = []
    self.images = []
    self.signs = []
    self.revision = None
    self.date = None

    self.signs_by_name = {}
    self.forms_by_name = defaultdict(list)
    self.forms_by_source = defaultdict(lambda: defaultdict(list))

  def add_source(self, source: Source):
    self.sources[source.abbreviation] = source

  def add_system(self, system: System):
    self.systems[system.name] = system

  def add_link_type(self, link_type: LinkType):
    self.link_types[link_type.name] = link_type

  def add_sign(self, sign: SignLike, parser: Parser):
    self.signs.append(sign)
    if isinstance(sign, Sign):
      for name in sign.names:
        self.forms_by_name[name].append(sign)
      for s in sign.sources:
        self.forms_by_source[s.source][s.number].append(sign)
      for form in sign.forms:
        for name in form.names:
          self.forms_by_name[name].append(form)
        for s in form.sources:
          self.forms_by_source[s.source][s.number].append(form)
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
          # TODO(egg): Talk to Steve about deduplicating this.
          if name in ("1(DIŠ)",):
            continue
          parser.raise_error(
              "Duplicate sign %s. Existing:\n%s\nNew:\n%s" % (
                  name,
                  textwrap.indent(str(self.signs_by_name[name]), '  '),
                  textwrap.indent(str(sign), '  ')))
      self.signs_by_name[name] = sign

  def add_source_mapping(self, name: str, source: Source, n: SourceRange):
    if len(n) != 1:
      raise ValueError(f"{n} should be a singleton")
    if name not in self.forms_by_name:
      raise KeyError(f"{name} not found")
    for form in self.forms_by_name[name]:
      form.sources.append(SourceReference(source, n))
      form.sources = sorted(form.sources, key=lambda s: s.source.abbreviation)
      self.forms_by_source[source][n].append(form)

  def __str__(self):
    return "\n\n".join((
      str(self.project),
      f"@{self.tag} {self.name}",
      str(self.domain),
      "\n\n".join(str(note) for note in self.notes),
      "\n\n".join(str(source) for source in self.sources.values()),
      "\n\n".join(str(system) for system in self.systems.values()),
      "\n".join(str(script) for script in self.scripts),
      "\n\n".join(str(link_type) for link_type in self.link_types.values()),
      "\n\n".join(str(sign) for sign in self.signs)))

  @classmethod
  def parse(cls, parser: Parser) -> "SignList":
    project = Project.parse(parser)
    entry = parser.next_expecting(cls)
    domain = Domain.parse(parser)
    result = cls(project, entry.text, domain)

    while entry := parser.peek():
      if entry.tag == InternalNote.tag:
        result.notes.append(InternalNote.parse(parser))
      elif entry.tag == Source.tag:
        result.add_source(Source.parse(parser))
      elif entry.tag == System.tag:
        result.add_system(System.parse(parser))
      elif entry.tag == LinkType.tag:
        result.add_link_type(LinkType.parse(parser))
      elif entry.tag == ScriptDef.tag:
        result.scripts.append(ScriptDef.parse(parser))
      elif entry.tag == Images.tag:
        result.images.append(Images.parse(parser))
      else:
        for entry_type in SignLike.__subclasses__():
          if entry.tag == entry_type.tag:
            result.add_sign(entry_type.parse(parser, result.sources), parser)
            break
        else:
          parser.raise_error(f"Expected one of {SignLike.__subclasses__()}, got {entry.tag}")
    return result

osl_hash = subprocess.check_output(
  ['git', 'describe', '--tags', '--always', '--dirty', '--abbrev=40', '--long'],
  cwd=r"..\osl").decode('ascii').strip()
osl_date = datetime.datetime.fromisoformat(
  subprocess.check_output(
    ['git', 'show', '--no-patch', '--format=%cI', 'HEAD'],
    cwd=r"..\osl").decode('ascii').strip()).astimezone(datetime.timezone.utc)

with open(r"..\osl\00lib\osl.asl", encoding="utf-8") as f:
  original_lines = f.read().splitlines()
  osl = SignList.parse(Parser(original_lines, "osl.asl"))

osl.date = osl_date
osl.revision = osl_hash

diff = list(difflib.unified_diff(
    original_lines, str(osl).splitlines(),
    fromfile="osl.asl", tofile="formatted"))

if len(diff) > 40:
  print("*** Large diff when regenerating OSL")
else:
  print("\n".join(diff))
if str(SignList.parse(Parser(str(osl).splitlines(), "str(osl)"))) != str(osl):
  raise ValueError("Not idempotent")

print(len([sign for sign in osl.signs if isinstance(sign, Sign) and (sign.sources or sign.values or sign.unicode_cuneiform) and sign.unicode_cuneiform and not sign.deprecated]), "typeable encoded signs")
print(len([sign for sign in osl.signs if isinstance(sign, Sign) and (sign.sources or sign.values or sign.unicode_cuneiform) and not sign.deprecated]), "potential typeable signs")
print(sum([len(sign.values) for forms in osl.forms_by_name.values() for sign in forms if (sign.sources or sign.values or sign.unicode_cuneiform) and sign.unicode_cuneiform and not sign.deprecated]), "typeable encoded values")

for source in osl.sources.values():
  missing = []
  total = 0
  for n in source:
    if n in osl.forms_by_source[source]:
      total += 1
    else:
      if not n.suffix and any(m.suffix and m.first == n.first for m in source):
        continue
      missing.append(n)
      total += 1
  if missing:
    print(f"*** {len(missing)} / {total} missing numbers from {source.abbreviation}", file=sys.stderr)
  else:
    print(f"--- {len(missing)} / {total} missing numbers from {source.abbreviation}", file=sys.stderr)
  if len(missing) < 20:
    print(f"***   {' '.join(str(n) for n in missing)}", file=sys.stderr)

for forms in osl.forms_by_name.values():
  for form in forms:
    if form.unicode_cuneiform:
      ucun = form.unicode_cuneiform.text.upper().replace("O", "X")
      if len(ucun) == 1:
        useq_from_ucun = f"U+{ord(ucun):04X}"
      else:
        useq_from_ucun = ".".join(f"x{ord(c):04X}" for c in ucun)
      from_hex = None
      if form.unicode_sequence:
        from_hex = "".join("X" if hex in "XO" else chr(int("0" + hex, 16))
                           for hex in form.unicode_sequence.text.split("."))
      usource = None
      for ref in form.sources:
        if ref.source.abbreviation == "U+":
          usource = ref
          if from_hex:
            raise ValueError(f"Both @useq and @list U+ in {form}")
          from_hex = chr(usource.number.first)
      if from_hex and from_hex != ucun:
        raise ValueError(f"*** Inconsistent @ucun ({useq_from_ucun} =) {ucun}) and @list U+/@useq {form.unicode_sequence or usource} (= {from_hex})) in {form}")


# TODO(egg): Some of this wants to be in the SignList object.

signs_by_value : dict[str, list[Sign]] = defaultdict(list)
for sign in osl.signs:
    if isinstance(sign, Sign):
        if sign.deprecated:
            continue
        for value in sign.values:
            if value.deprecated:
                continue
            if value.language:
                continue
            if value.text in signs_by_value and "ₓ" not in value.text:
                raise ValueError(f"Multiple signs with value {value.text}: {signs_by_value[value.text][0].names}, {sign.names}")
            signs_by_value[value.text].append(sign)

forms_by_list_number = {source.abbreviation + str(number): form
                        for source, forms in osl.forms_by_source.items()
                        for number, form in forms.items()}

def xsux_sequence(name: str):
    sequence_parts : list[str] = []
    depth = 0
    start = 1
    for i, c in enumerate(name):
        if i == 0:
            continue
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
        elif depth == 0 and c == '.' or i == len(name) - 1:
            part_name = name[start:i]
            for form in (osl.forms_by_name.get(part_name) or
                         osl.forms_by_name.get(f"|{part_name}|") or
                         signs_by_value.get(part_name.lower()) or
                         forms_by_list_number.get(part_name) or
                         []):
                if form.unicode_cuneiform:
                    sequence_parts.append(form.unicode_cuneiform.text)
                    break
            else:
                sequence_parts = []
                break
            start = i + 1
    return sequence_parts


atomic_sequences: dict[str, str] = {}
for name, forms in osl.forms_by_name.items():
    xsux = [form.unicode_cuneiform.text
            for form in forms
            if form.unicode_cuneiform]
    if not xsux:
        continue
    if len(set(xsux)) > 1:
        raise ValueError(name, xsux)
    xsux = xsux[0]
    if len(xsux) > 1:
        continue
    if 'X' in xsux or 'x' in xsux:
        continue
    if name[0] != "|" or name[-1] != "|":
        continue        
    sequence_parts = xsux_sequence(name)
    if sequence_parts:
        if xsux in atomic_sequences and atomic_sequences[xsux] != ''.join(sequence_parts):
            raise ValueError(f"Multiple decompositions {atomic_sequences[xsux]} != {sequence_parts} for {xsux}")
        if len(sequence_parts) > 1:
            atomic_sequences[xsux] = ''.join(sequence_parts)

for xsux, decomposition in atomic_sequences.items():
    print(f"+++ {xsux} is not {'.'.join(decomposition)}")
print(f"--- {len(atomic_sequences)} atomically encoded sequences")

atom_replacements = sorted(atomic_sequences.items(), key=lambda kv: -len(kv[1]))

sequence_mapping: dict[str, list[tuple[list[str], list[Form]]]] = defaultdict(list)
for name, forms in osl.forms_by_name.items():
    xsux = [form.unicode_cuneiform.text
            for form in forms
            if form.unicode_cuneiform] or [f"(no @ucun for {name})"]
    if len(set(xsux)) > 1:
        raise ValueError(name, xsux)
    xsux = xsux[0]
    if name[0] != "|" or name[-1] != "|":
        continue
    sequence_parts = xsux_sequence(name)
    for atom, sequence in atom_replacements:
        sequence_parts = list(''.join(sequence_parts).replace(sequence, atom))
    if sequence_parts:
        sequence_mapping[xsux].append((sequence_parts, forms))
for xsux, decompositions in sequence_mapping.items():
    for decomposition, forms in decompositions:
        if xsux != ''.join(decomposition) and len(xsux) != 1:
            message = f"{xsux} is not {'.'.join(decomposition)}"
            if all(form.deprecated for form in forms):
              print("---", message, "in deprecated form")
            elif all(''.join(xsux_sequence(form.names[0])) == xsux for form in forms):
              print("---", message, "from alternate name")
            else:
              raise ValueError(message)