from collections import defaultdict
import json
import os
import sys
from typing import Any

import atf
import asl

language_to_value_to_period_to_usages : dict[
  str, dict[
    str, dict[
      str, list[str]]]] = defaultdict(
        lambda: defaultdict(
          lambda: defaultdict(list)))

def index_values(text_json: Any, artefact: str, period: str, genre: str, lang: str = "und"):
  if "lang" in text_json:
    lang = text_json["lang"].split("-")[0]
  if "cdl" in text_json:
    for node in text_json["cdl"]:
      index_values(node, artefact, period, genre, lang)
  if "f" in text_json:
      index_values(text_json["f"], artefact, period, genre, lang)
  if "gdl" in text_json:
     for node in text_json["gdl"]:
      index_values(node, artefact, period, genre, lang)
  if "group" in text_json:
     for node in text_json["group"]:
      index_values(node, artefact, period, genre, lang)
  if "seq" in text_json:
     for node in text_json["seq"]:
      index_values(node, artefact, period, genre, lang)
  # We do not go down into "qualified" for now (the index is on default values).
  if "v" in text_json:
    language_to_value_to_period_to_usages[
      lang][text_json["v"]][period].append(artefact)

def index(directory: str):
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
      index_values(
        text,
        cdli_number,
        metadata.get("period", "unknown").replace("Neo ", "Neo-").replace(
          "Old ", "O").replace("Middle ", "M").replace("Neo-", "N").replace(
          "Assyrian", "A").replace("Babylonian", "B"),
        metadata.get("genre", metadata.get("subgenre", "unclassified")).lower())
    if skipped:
      if len(skipped) < 10:
        for file in skipped:
          print(f"*** {file} was empty, skipped.")
      else:
        print(f"*** Skipped {len(skipped)} empty files.")
  for f in listing:
    if os.path.isdir(directory + "/" + f) and f != "corpusjson":
      index(directory + "/" + f)

for project in ("atae", "tcma", "blms", "saao", "rinap", "riao"):
  index(f"oracc/{project}")

for file in ("OAkk", "Early OB", "OA", "OB akk", "MA", "MB", "Early NB", "NA", "NB"):
  covered_by_oracc : set[str] = set()
  for value, occurrences in atf.get_value_counts(
      f"cdli/{file}.atf",
      "akk",
      set((atf.SpanAttribute.DETERMINATIVE, atf.SpanAttribute.LOGOGRAM))).items():
    oracc_texts = set(language_to_value_to_period_to_usages["akk"][value][file.removesuffix(" akk")])
    for occurrence in occurrences:
      if occurrence in oracc_texts:
        covered_by_oracc.add(occurrence)
      else:
        language_to_value_to_period_to_usages["akk"][value][file.removesuffix(" akk")].append(occurrence)
  print(f"--- {len(covered_by_oracc)} artefacts already covered by Oracc in {file}")

sign = asl.osl.signs_by_name[sys.argv[1]]
if isinstance(sign, asl.Sign):
  if not sign.unicode_cuneiform:
    raise ValueError(f"No Xsux for {sign.names[0]}")
  for language, value_to_period_to_usages in language_to_value_to_period_to_usages.items():
    print(language, "values of", sign.unicode_cuneiform.text, sign.names[0])
    for value in sign.values:
      usage = value_to_period_to_usages[value.text]
      total = 0
      periods : set[str] = set()
      for period, usages in usage.items():
        periods.add(period)
        total += len(usages)
      if not total:
        continue
      print(value.text, total)
      chronology = {"O": 0, "M": 1, "N": 2}
      for period in sorted(periods, key=lambda period: (chronology[period[0]] if len(period) == 2 else -1 if period == "OAkk" else 9, period)):
        print(" " * len(value.text),
              period,
              len(usage[period]))