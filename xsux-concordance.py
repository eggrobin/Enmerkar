from collections import defaultdict
import json
import os
import re
from typing import Any
import unicodedata

import asl

occurrences : dict[str, int] = defaultdict(int)

class Line:
  def __init__(self, source: str, ref: str, label: str, xsux: str):
    self.source = source
    self.ref = ref
    self.label = label
    self.xsux = xsux

  def __repr__(self):
     return f"Line({repr(self.ref)}, {repr(self.label)}, {repr(self.xsux)})"

  def __str__(self):
     return f"{self.source}/{self.ref}\t{self.label}\t{self.xsux}"

  def html_ref(self) -> str:
     return f"<a href='{self.source}/{self.ref}'>{self.source}/{self.ref.split('.')[0]} {self.label}</a>"

  def html(self) -> str:
     return f"<tr><td>{self.html_ref()}</td><td class=xsux>{self.xsux}</td></tr>"

def get_xsux(oracc_json: Any, source : str|None = None, result: list[Line]|None = None) -> list[Line]:
  if result is None:
     result = []
  if not source:
     if "source" not in oracc_json:
        raise ValueError("Missing source", oracc_json)
     source : str = oracc_json["source"]
  if "type" in oracc_json and oracc_json["type"] == "line-start":
    if "label" in oracc_json:
      result.append(Line(source, oracc_json["ref"], oracc_json["label"], ""))
    else:
       print(f"*** Line with no label: {oracc_json.get('ref', 'no ref')}")
  if "cdl" in oracc_json:
     for node in oracc_json["cdl"]:
        get_xsux(node, source, result)
  if "f" in oracc_json:
      get_xsux(oracc_json["f"], source, result)
  if "gdl" in oracc_json:
     for node in oracc_json["gdl"]:
        get_xsux(node, source, result)
  if "group" in oracc_json:
     for node in oracc_json["group"]:
        get_xsux(node, source, result)
  if "seq" in oracc_json:
     for node in oracc_json["seq"]:
        get_xsux(node, source, result)
  if "utf8" in oracc_json:
     for c in oracc_json["utf8"]:
        occurrences[c] += 1
     result[-1].xsux += oracc_json["utf8"]
  return result


all_lines : list[Line] = []

def get_corpus_lines(directory: str):
  global all_lines
  for filename in os.listdir(directory):
    if os.path.isdir(directory + "/" + filename):
      if filename == "corpusjson":
        files = os.listdir(directory + "/corpusjson")
        print(f"{len(files)} texts in {directory}...")
        for filename in files:
          with open(directory + "/corpusjson/" + filename, encoding="utf-8") as f:
            source = f.read()
            if not source:
               print(f"*** {filename} in {directory} is empty, skipping.")
               continue
            text = json.loads(source)
            try:
              all_lines += get_xsux(text)
            except Exception:
              print(f"*** Exception while reading {filename} in {directory}:")
              raise
      else:
        get_corpus_lines(directory + "/" + filename)

for top_level in ("atae", "riao", "rinap", "saao",
                  "tcma", "blms"
                  ):
  get_corpus_lines("oracc/" + top_level)

query = "𒈬𒅗"
tail_regex = re.compile("")#"𒋗|𒈽")

concordance : list[tuple[Line, str, str, str]] = []

for line in all_lines:
  if query in line.xsux:
      start = 0
      while query in line.xsux[start:]:
        i = line.xsux.index(query, start)
        if not tail_regex.search(line.xsux[i+len(query):]):
           break
        concordance.append((line, line.xsux[:i], line.xsux[i:i+len(query)], line.xsux[i+len(query):]))
        start = i + 1

xsux_to_mzl_number : dict[str, int] = {}

for mzl_number, forms in asl.osl.forms_by_source[asl.osl.sources["MZL"]].items():
  for form in forms:
     if form.unicode_cuneiform:
        xsux_to_mzl_number[form.unicode_cuneiform.text] = mzl_number.first

concordance = sorted(concordance, key=lambda x: [xsux_to_mzl_number.get(sign, -1) for sign in x[-1]])

with open("out.html", "w", encoding="utf-8") as f:
  print("<head><style>.xsux {font-family: Assurbanipal} .pre {text-align: right} .query {color: red}</style></head>", file=f)
  print("<body><table>", file=f)
  for line, pre, query, post in concordance:
    print(f"<tr><td>{line.html_ref()}</td>", file=f)
    print(f"<td class='xsux pre'>{pre}</td>", file=f)
    print(f"<td class='xsux query'>{query}</td>", file=f)
    print(f"<td class='xsux post'>{post}</td>", file=f)
  print("</table></body>", file=f)

with open("sign_usage.txt", mode="w", encoding="utf-8") as f:
   for i, (s, count) in enumerate(sorted(occurrences.items(), key=lambda kv: -kv[1])):
      if ord(s) < 0x12000 or ord(s) > 0x12EFF:
         continue
      print(f"{i+1}\tU+{ord(s):04X}\t{s}\t{unicodedata.name(s)}\t{count}", file=f)