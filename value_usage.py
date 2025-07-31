from collections import defaultdict
import json
import os
import sys
from typing import Any

import asl

language_to_sign_to_value_to_period_to_genre_to_usages : dict[
  str, dict[
  str, dict[
    str, dict[
      str, dict[
        str, int]]]]] = defaultdict(
          lambda: defaultdict(
            lambda: defaultdict(
              lambda: defaultdict(
                lambda: defaultdict(int)))))

def index_values(text_json: Any, period: str, genre: str, lang: str = "und"):
  if "lang" in text_json:
    lang = text_json["lang"].split("-")[0]
  if "cdl" in text_json:
    for node in text_json["cdl"]:
      index_values(node, period, genre, lang)
  if "f" in text_json:
      index_values(text_json["f"], period, genre, lang)
  if "gdl" in text_json:
     for node in text_json["gdl"]:
      index_values(node, period, genre, lang)
  if "group" in text_json:
     for node in text_json["group"]:
      index_values(node, period, genre, lang)
  if "seq" in text_json:
     for node in text_json["seq"]:
      index_values(node, period, genre, lang)
  if "v" in text_json and "utf8" in text_json:
    language_to_sign_to_value_to_period_to_genre_to_usages[
      lang][
        text_json["utf8"]][
          text_json["v"]][period][genre] += 1


def index(directory: str):
  listing = os.listdir(directory)
  if "catalogue.json" in listing:
    with open(directory + "/catalogue.json", encoding="utf-8") as f:
      catalogue = json.loads(f.read())
    files = [
        (directory + "/corpusjson/" + cdli_number + ".json", metadata)
        for cdli_number, metadata in catalogue["members"].items()
        if os.path.isfile(directory + "/corpusjson/" + cdli_number + ".json")]
    print(f"Indexing {len(files)} texts in {directory}...")
    skipped : list[str] = []
    for i, (text_file, metadata) in enumerate(files):
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
        metadata.get("period", "unknown").replace("Neo ", "Neo-"),
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

for project in ("",):
  index(f"oracc/{project}")

sign = asl.osl.signs_by_name[sys.argv[1]]
if isinstance(sign, asl.Sign):
  if not sign.unicode_cuneiform:
    raise ValueError(f"No Xsux for {sign.names[0]}")
  for language, sign_to_value_to_period_to_genre_to_usages in language_to_sign_to_value_to_period_to_genre_to_usages.items():
    print(language, "values of", sign.unicode_cuneiform.text, sign.names[0])
    for value in sign.values:
      usage = sign_to_value_to_period_to_genre_to_usages[sign.unicode_cuneiform.text][value.text]
      total = 0
      total_by_period : dict[str, int] = defaultdict(int)
      genres_by_period : dict[str, set[str]] = defaultdict(set)
      periods : set[str] = set()
      for period, genre_to_usages in usage.items():
        period = period.replace(
          "Old ", "O").replace("Middle ", "M").replace("Neo-", "N").replace(
          "Assyrian", "A").replace("Babylonian", "B")
        periods.add(period)
        for genre, usages in genre_to_usages.items():
          total += usages
          total_by_period[period] += usages
          genres_by_period[period].add(genre)
      if not total:
        continue
      print(value.text, total)
      chronology = {"O": 0, "M": 1, "N": 2}
      for period in sorted(periods, key=lambda period: (chronology[period[0]] if len(period) == 2 else 9, period)):
        print(" " * len(value.text),
              period,
              total_by_period[period],
              "(" + ", ".join(genres_by_period[period]) +")" if len(genres_by_period[period]) < 10 else "")