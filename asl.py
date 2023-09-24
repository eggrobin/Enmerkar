# Based on https://build-oracc.museum.upenn.edu/ogsl/aslogslfileformat/index.html as built from
# https://github.com/oracc/ogsl/blob/53952bfcbe2a575f92522562fdff3b8fcfd757ab/00web/asl.xml.

from typing import Optional, Sequence, Tuple

class TextTag:
  tag: str
  text: str

  def __init__(self, text: str):
    self.text = text

  def __str__(self):
    return "@%s\t%s" % (self.tag, "\t\n".join(self.text.splitlines()))
  
  @classmethod
  def parse(cls, lines: list[str], i: int, context: str) -> Tuple["TextTag", int]:
    tag, first_line = lines[i].split(maxsplit=1)
    if tag != f"@{cls.tag}":
      raise SyntaxError()
    text = first_line
    consumed = 0
    for line in lines[i+1:]:
      if line.startswith("\t"):
        text += line.lstrip()
        consumed += 1
      else:
        break
    return (cls(text), consumed)

class Note(TextTag):
  tag = "note"

class InternalNote(Note):
  tag = "inote"

class Literature(Note):
  tag = "lit"

# Not actually arbitrary text.
class Reference(Note):
  tag = "ref"

# Not actually arbitrary text.
class UnicodeName(TextTag):
  tag = "uname"

class UnicodeNote(TextTag):
  tag = "unote"

class UnicodeSequence(TextTag):
  tag = "useq"

class SourceNumber:
  pass

class Source:
  """A classical sign list, e.g., RÉC, MZL, etc.

  We use the Unicode term source so as to avoid conflicts and confusion with
  both the SignList type, representing the OGSL, and with Python lists.
  """
  abbreviation: str
  numbers: set[SourceNumber]
  tag = "listdef"
  
  def __init__(self, abbreviation: str, numbers: set[SourceNumber]):
    self.abbreviation = abbreviation
    self.numbers = numbers

class Value:
  deprecated: bool
  language: str
  text: str
  notes: list[Note]
  pass

class SourceReference:
  source: Source
  number: SourceNumber

class System:
  tag = "sysdef"

class SystemBinding:
  pass

class SignLike:
  pass

class SourceOnly(SignLike):
  tag = "lref"
  source: Source
  number: SourceNumber
  notes: list[Note]

class CompoundOnly(SignLike):
  tag = "compoundonly"
  source: Source
  number: SourceNumber
  notes: list[Note]

# Omitting @sref which is not actually used.

class Form:
  deprecated: bool
  names: list[str]
  sources: list[SourceReference]
  notes: list[Note]
  # TODO(egg): Unicode.
  values: list[Value]
  # system* is missing from formblock in the documentation, but really is used.
  systems: list[SystemBinding]

  def __init__(self, name: str):
    self.names = [name]

class Sign(Form, SignLike):
  tag = "sign"
  forms: list[Form]

class SignList:
  name: str
  # Not documented, nor really used, except that one of the listdefs is
  # @inoted out. 
  notes: list[Note]
  sources: list[Source]
  systems: list[System]
  signs: list[SignLike]

  def __init__(self, name: str):
    self.name = name
    self.notes = []
    self.sources = []
    self.systems = []
    self.signs = []

  def add_source(self, source: Source):
    self.signs.append(source)

  def add_sign(self, sign: Sign):
    self.signs.append(sign)

  # TODO(egg): In Python 3.11, this should return Self.
  @classmethod  
  def parse(cls, lines: list[str], context: str) -> "SignList":
    result: Optional[SignList] = None
    i = -1
    while i + 1 < len(lines):
      i += 1
      line = lines[i].strip()
      if not line:
        continue
      print(repr(line))
      (tag, name) = line.split(maxsplit=1)
      if not tag.startswith("@"):
        raise SyntaxError(f"{context}:{i} Tag {tag} does not start with @: {line}")
      tag = tag[1:]
      if not result:
        if tag != "signlist":
          raise SyntaxError(f"{context}:{i} Expected @signlist: {line}")
        result = cls(name)
      else:
        if tag == InternalNote.tag:
          (note, consumed) = InternalNote.parse(lines, i, context)
          result.notes.append(note)
          i += consumed
        elif tag == Source.tag:
          (source, consumed) = Source.parse(lines, i, context)
          result.sources.append(source)
          i += consumed
        elif tag == System.tag:
          (system, consumed) = System.parse(lines, i, context)
          result.system.append(system)
          i += consumed
        else:
          for entry in SignLike.__subclasses__():
            if tag == entry.tag:
              tag.parse(lines, i, context)
              break
          else:
            raise SyntaxError(f"{context}:{i} Expected one of {SignLike.__subclasses__()} {line}")

with open(r"..\ogsl\00lib\ogsl.asl", encoding="utf-8") as f:
  SignList.parse(f.readlines(), "ogsl.asl")
