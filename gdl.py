
from abc import abstractmethod

class Expression:
  def factor(self):
    return str(self)

  def atf(self):
    return str(self)

class Compound(Expression):
  @abstractmethod
  def __init__(self, *terms: Expression):
    pass

  def factor(self):
      return f"({self})"

  def atf(self):
    return f"|{self}|"

class Name(Expression):
  def __init__(self, name: str):
    self.text = name

  def __str__(self):
    return self.text

class Beside(Compound):
  def __init__(self, *terms: Expression):
    self.terms : list[Expression] = []
    for term in terms:
      if isinstance(term, Beside):
        self.terms += term.terms
      else:
        self.terms.append(term)

  def __str__(self):
    return ".".join(str(term) for term in self.terms)

class Joining(Compound):
  def __init__(self, *terms: Expression):
    self.terms = terms
    if any(isinstance(term, Beside) for term in terms):
      raise ValueError(f"Redundant parentheses in horizontal sequence {self}")

  def __str__(self):
    return "+".join(str(term) for term in self.terms)

class Containing(Compound):
  def __init__(self, outer: Expression, *inner: Expression):
    self.inner = inner[-1]
    if len(inner) == 1:
      self.outer = outer
    else:
      self.outer = Containing(outer, *inner[:-1])

  def __str__(self):
    return f"{str(self.outer) if isinstance(self.outer, Containing) else self.outer.factor()}×{self.inner.factor()}"

class Above(Compound):
  def __init__(self, *terms: Expression):
    self.terms : list[Expression] = []
    for term in terms:
      if isinstance(term, Above):
        self.terms += term.terms
      else:
        self.terms.append(term)

  def __str__(self):
    return "&".join(term.factor() for term in self.terms)

class Crossing(Compound):
  def __init__(self, first: Expression, second: Expression):
    self.first = first
    self.second = second

  def __str__(self):
    return f"{self.first.factor()}%{self.second.factor()}"

class Opposing(Compound):
  def __init__(self, first: Expression, second: Expression):
    self.first = first
    self.second = second

  def __str__(self):
    return f"{self.first.factor()}@{self.second.factor()}"

def parse(gdl: str) -> Expression:
  if gdl.startswith("|"):
    if not gdl.endswith("|"):
      raise SyntaxError(f"Unterminated || in {gdl}")
    return parse_compound(gdl[1:-1])
  else:
    return Name(gdl)

# Ordered by increasing precedence.
OPERATORS : list[dict[str, type[Compound]]] = [
  {".": Beside},
  {"+": Joining},
  {"×": Containing,
   "&": Above,
   "%": Crossing,
   "@": Opposing},
]

def parse_compound(gdl: str) -> Expression:
  stack : list[int] = []
  for operators in OPERATORS:
    operator_positions : list[int] = []
    for i, c in enumerate(gdl):
      if c == "(":
        stack.append(i)
      elif c == ")":
        start = stack.pop()
        if i == len(gdl) and start == 0:
          return parse_compound(gdl[1:-1])
      if not stack:
        if c == "@" and i + 1 < len(gdl) and gdl[i + 1] in "cfgstnzkrh19v":
          continue
        if c in operators:
          if operator_positions and c != gdl[operator_positions[0]]:
            raise SyntaxError(f"Expression relies on precedence between {c} and {gdl[operator_positions[0]]}: {gdl}")
          operator_positions.append(i)
    if operator_positions:
      parts : list[Expression] = []
      for i, j in zip([-1] + operator_positions, operator_positions + [len(gdl)]):
        parts.append(parse_compound(gdl[i+1:j]))
      return operators[gdl[operator_positions[0]]](*parts)
  if stack:
    raise SyntaxError(f"Unterminated () at in {gdl[:stack[0]]}☞{gdl[stack[0]:]}")
  return Name(gdl)

import asl
for forms in asl.osl.forms_by_name.values():
  for form in forms:
    if form.names[0] != parse(form.names[0]).atf():
      print(f"*** {form.names[0]} != {parse(form.names[0]).atf()}")
    for name in form.names[1:]:
      if name in ("|AŠ&AŠ&AŠ%AŠ&AŠ&AŠ|",  # & > %
                  "|BU%BU×AB|",  # % > ×
                  "|MUŠ%MUŠ×AB|",  # % > ×
                  "|GA₂×NUN&NUN|",  # & > ×
                  "|MUŠ&MUŠ×(A.NA)|",  # & > ×
                  "|MUŠ&MUŠ×AB|",  # & > ×
                  "|MUŠ%MUŠ×(A.NA)|",  # % > ×
                  "|MUŠ%MUŠ×MAŠ|",  # % > ×
                  "|SAR×ZU&ZU|",  # & > ×
                  "|(ŠE.NUN)&(ŠE.NUN)×U₂|",  # & > ×
                  "|URU×TU&TU|",  # & > ×
                  "|KA×GIŠ%GIŠ|",  # % > ×
                  "|KU&HI×AŠ₂|",  # × > &
                  "|KU&HI×AŠ₂.KU&HI×AŠ₂|",  # × > &
                  ):
        continue
      if name != parse(name).atf():
        print(f"*** {name} != {parse(name).atf()}")