from collections import defaultdict
import json
import os
from typing import Any
import unicodedata

import asl

def list_signs(text_json: Any, signs: list[str]):
  if "cdl" in text_json:
    for node in text_json["cdl"]:
      list_signs(node, signs)
  if "f" in text_json:
      list_signs(text_json["f"], signs)
  if "gdl" in text_json:
     for node in text_json["gdl"]:
      list_signs(node, signs)
  if "group" in text_json:
     for node in text_json["group"]:
      list_signs(node, signs)
  if "seq" in text_json:
     for node in text_json["seq"]:
      list_signs(node, signs)
  # We do not go down into "qualified" for now (the index is on default values).
  if "utf8" in text_json:
    for c in text_json["utf8"]:
      if ord(c) >= 0x12000 and ord(c) <= 0x1268F:
        signs.append(c)


class FontCorpusCoverage:
  def __init__(self, code_points_covered : set[str]) -> None:
    self.code_points_covered = code_points_covered
    self.texts : set[str] = set()
    self.texts_covered : set[str] = set()
    self.sign_occurrences : list[str] = []
    self.covered_sign_occurrences : list[str] = []

  def add_text(self, name: str, text: list[str]):
    if name in self.texts:
      raise ValueError(name)
    self.texts.add(name)
    covered_signs = [c for c in text if c in self.code_points_covered]
    if len(covered_signs) == len(text):
      self.texts_covered.add(name)
    self.sign_occurrences += text
    self.covered_sign_occurrences += covered_signs

  def print_most_common_uncovered(self):
    occurrences_by_sign : dict[str, int] = defaultdict(int)
    for s in self.sign_occurrences:
      if s not in self.code_points_covered:
        occurrences_by_sign[s] += 1
    max = 100
    for i, (sign, occurrences) in enumerate(
      sorted(occurrences_by_sign.items(),
             key=lambda kv: -kv[1])):
      if i > max:
        print(f"({len(occurrences_by_sign) - max} more...)")
        break
      print(f"{i:3} {occurrences:5} U+{ord(sign):5X} {unicodedata.name(sign):50} {sign}")

  def __str__(self):
    return f"""
        {len(self.texts_covered)}/{len(self.texts)} texts ({
          len(self.texts_covered)/len(self.texts):0.2%}),
        {len(self.covered_sign_occurrences)}/{
          len(self.sign_occurrences)} sign occurrences ({
            len(self.covered_sign_occurrences)/
            len(self.sign_occurrences)
          :0.2%}),
        {len(set(self.covered_sign_occurrences))}/{
          len(set(self.sign_occurrences))} unique signs ({
            len(set(self.covered_sign_occurrences))/
            len(set(self.sign_occurrences))
          :0.2%})"""

def compute_coverage(directory: str,
                     coverage_by_font: dict[str, FontCorpusCoverage]):
  listing = os.listdir(directory)
  if "catalogue.json" in listing:
    with open(directory + "/catalogue.json", encoding="utf-8") as f:
      catalogue = json.loads(f.read())
    files = [
        (cdli_number,
         directory + "/corpusjson/" + cdli_number + ".json",
         metadata)
        for cdli_number, metadata in catalogue["members"].items()
        if os.path.isfile(directory + "/corpusjson/" + cdli_number + ".json")]
    print(f"Indexing {len(files)} texts in {directory}...")
    skipped : list[str] = []
    for i, (cdli_number, text_file, metadata) in enumerate(files):
      if i > 0 and i % 1000 == 0:
        print(f"    {i}/{len(files)}...")
      with open(text_file, encoding="utf-8") as f:
        source = f.read()
        if not source:
          skipped.append(text_file)
          continue
        text = json.loads(source)
      text_signs : list[str] = []
      list_signs(text, text_signs)
      for coverage in coverage_by_font.values():
        coverage.add_text(cdli_number, text_signs)
    if skipped:
      if len(skipped) < 10:
        for file in skipped:
          print(f"*** {file} was empty, skipped.")
      else:
        print(f"*** Skipped {len(skipped)} empty files.")
  for f in listing:
    if os.path.isdir(directory + "/" + f) and f != "corpusjson":
      compute_coverage(directory + "/" + f, coverage_by_font)

coverage_by_font: dict[str, FontCorpusCoverage] = {}

for font in ("Nabuninuaihsus", "CuneiformNAOutline"):
  with open(f"../Nabuninuaihsus/{font}_coverage.txt",
            encoding="utf8") as f:
    covered_code_points : set[str] = set()
    for line in f.readlines():
      covered_code_points.add(chr(int(line, base=16)))
    coverage_by_font[font] = FontCorpusCoverage(covered_code_points)

compute_coverage("oracc/saao", coverage_by_font)

for font, coverage in coverage_by_font.items():
  print(f"Most common missing signs in {font}:")
  coverage.print_most_common_uncovered()
for font, coverage in coverage_by_font.items():
  print(font, coverage)

signlist : list[str] = []

def get_list_number(xsux: str, list_name: str):
  numbers : set[asl.SourceRange] = set()
  for form in asl.osl.forms_by_source[asl.osl.sources["U+"]][asl.SourceRange("0x%X" % ord(xsux))]:
    for source_reference in form.sources:
      if source_reference.source.abbreviation == list_name:
        numbers.add(source_reference.number)
  if not numbers:
    return None
  return sorted(numbers, key=str)[0]

def get_pretty_list_number(xsux: str, list_name: str):
  number = get_list_number(xsux, list_name)
  if not number:
    return None
  return {"MZL" : "MZL", "SYA": "SyA", "ASY" : "ASy", "SLLHA": "ŠL/MÉA"}[list_name] + ' ' + str(number)

def sort_key(c : str, list_name : str):
  number = get_list_number(c, list_name)
  return str(number)

signs = [c for c in coverage_by_font["Nabuninuaihsus"].code_points_covered if ord(c) >= 0x12000]

sorted_signs : list[str] = []

for sign_list in "MZL", "SYA", "ASY", "SLLHA":
  for c in sorted((c for c in signs if get_list_number(c, sign_list) and c not in sorted_signs),
                  key=lambda c: str(get_list_number(c, sign_list))):
    inserted_number = str(get_list_number(c, sign_list))
    next_down = None
    i_next_down = len(sorted_signs) - 1
    for i in range(len(sorted_signs)):
      number_at_i = get_list_number(sorted_signs[i], sign_list)
      if not number_at_i:
        continue
      number_at_i = str(number_at_i)
      if number_at_i > inserted_number:
        continue
      if not next_down or number_at_i > next_down:
        next_down = number_at_i
        i_next_down = i
    sorted_signs.insert(i_next_down + 1, c)

sorted_signs += sorted(c for c in signs if c not in sorted_signs)

with open("../Nabuninuaihsus/index.html", encoding="utf8") as f:
  index_lines = f.readlines()


with open("../Nabuninuaihsus/index.html", mode="w", encoding="utf8") as f:
  in_sign_list = False
  for line in index_lines:
    line = line.rstrip("\n")
    if line.strip() == "<!--end GENERATED SIGN LIST;-->":
      in_sign_list = False
    if not in_sign_list:
      print(line, file=f)
    if line.strip() == "<!--GENERATED SIGN LIST: begin-->":
      in_sign_list = True
      print("\n".join(f"""<tr><td>U+{ord(c):04X}</td><td class="nabuninuaihsus">{c}</td><td class="nabuninuaihsus-sans">{c}</td><td>{
          asl.osl.forms_by_source[asl.osl.sources["U+"]][asl.SourceRange("0x%X" % ord(c))][0].names[0]}</td><td>{
            get_pretty_list_number(c, "SYA") or ""
          }</td><td>{
            get_pretty_list_number(c, "ASY") or ""
          }</td><td>{
            get_pretty_list_number(c, "SLLHA") or ""
          }</td><td>{
            get_pretty_list_number(c, "MZL") or ""
          }</td></tr>""" for c in sorted_signs),
          file=f)