from collections import defaultdict
import json
import os
import sys
from typing import Any

import atf
import asl

language_to_value_to_period_to_occurrences : dict[
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
    language_to_value_to_period_to_occurrences[
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

ORACC_PROJECTS = ("atae", "tcma", "blms", "saao", "rinap", "riao")

for project in ORACC_PROJECTS:
  index(f"oracc/{project}")

for file in ("OAkk", "Early OB", "OA", "OB akk", "MA", "MB", "Early NB", "NA", "NB"):
  covered_by_oracc : set[str] = set()
  for v, occurrences in atf.get_value_counts(
      f"cdli/{file}.atf",
      "akk",
      set((atf.SpanAttribute.DETERMINATIVE, atf.SpanAttribute.LOGOGRAM))).items():
    oracc_texts = set(language_to_value_to_period_to_occurrences["akk"][v][file.removesuffix(" akk")])
    for occurrence in occurrences:
      if occurrence in oracc_texts:
        covered_by_oracc.add(occurrence)
      else:
        language_to_value_to_period_to_occurrences["akk"][v][file.removesuffix(" akk")].append(occurrence)
  print(f"--- {len(covered_by_oracc)} artefacts already covered by Oracc in {file}")

sign = asl.osl.signs_by_name[sys.argv[1]]
if isinstance(sign, asl.Sign):
  value_to_period_to_occurrences = language_to_value_to_period_to_occurrences["akk"]
  sign_occurrences_by_period : dict[str, list[str]] = defaultdict(list)
  for value in sign.values:
    usage = value_to_period_to_occurrences[value.text]
    for period, occurrences in usage.items():
      sign_occurrences_by_period[period] += occurrences
  value_to_homophone_occurrences_by_period : dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
  for value in sign.values:
    base = value.text.rstrip("₀₁₂₃₄₅₆₇₈₉")
    for other_value, period_to_occurrences in value_to_period_to_occurrences.items():
      if other_value.rstrip("₀₁₂₃₄₅₆₇₈₉") != base:
        continue
      for period, occurrences in period_to_occurrences.items():
        value_to_homophone_occurrences_by_period[value.text][period] += occurrences
  for value in sign.values:
    period_to_occurrences = value_to_period_to_occurrences[value.text]
  with open(sign.names[0] + "_akk_value_usage.html", mode="w", encoding="utf-8") as f:
    print("""
          <html>
          <head>
          <style>
          table {
            border-collapse: collapse;
          }
          th {
            border: 1px solid;
            text-align: center;
          }
          td {
            border: 1px solid;
            text-align: center;
          }
          tr.𒆍𒀭𒊏𒆠 {
            border-bottom: 3px double;
          }
          </style>
          <script>
          function update_from_query() {
            params = (new URL(document.location)).searchParams;
            document.querySelector('input[id="count-artefact"]').checked = params.get("count") === "artefact";
            document.querySelector('input[id="over-homophones"]').checked = params.get("over") === "homophones";
            document.querySelector('input[id="over-sign"]').checked = params.get("over") === "sign";
            update_visibilities(false);
          }

          function update_visibilities(push_history = true) {
            over_homophones = document.querySelector('input[id="over-homophones"]').checked;
            over_sign = document.querySelector('input[id="over-sign"]').checked;
            count = !over_homophones && !over_sign;
            count_artefacts = document.querySelector('input[id="count-artefact"]').checked;
            if (push_history) {
              let query = [`count=${count_artefacts?"artefact":"occurrence"}`];
              if (over_homophones) {
                query.push("over=homophones");
              } else if (over_sign) {
                query.push("over=sign");
              }
              var newurl = window.location.protocol + "//" + window.location.host + window.location.pathname + '?' + query.join("&");
              window.history.pushState({ path: newurl }, '', newurl);
            }
            for (var div of document.getElementsByTagName("div")) {
              if (div.className === "over-homophones") {
                div.style = over_homophones ? "" : "display:none";
              }
              if (div.className === "over-sign") {
                div.style = over_sign ? "" : "display:none";
              }
              if (div.className === "count") {
                div.style = count ? "" : "display:none";
              }
              if (div.className === "count-artefact") {
                div.style = count_artefacts ? "" : "display:none";
              }
              if (div.className === "count-occurrence") {
                div.style = count_artefacts ? "display:none" : "";
              }
            }
          }
          window.onload = function () {
            for (var input of document.getElementsByTagName("input")) {
              input.onclick = update_visibilities;
            }
            update_from_query();
          }
          </script>
          </head>
          <body>
          """,
          file=f)
    print(f"<h1>akk values of {sign.unicode_cuneiform.text if sign.unicode_cuneiform else sign.names[0]}</h1>", file=f)
    print(f"<p>Based on transliterations from CDLI and Oracc projects {', '.join(ORACC_PROJECTS)}.</p>", file=f)
    print(f"""
          <p>
          <input type="radio" name="count" value="occurrence" id="count-occurrence" checked>
          <label for="count-occurrence">Count occurrences</label>
          </p>
          <p>
          <input type="radio" name="count" value="artefact" id="count-artefact">
          <label for="count-artefact">Count artefacts</label>
          </p>""", file=f)
    print(f"""
          <p>
          <input type="radio" name="over" value="1" id="count" checked>
          <label for="count">Show count</label>
          </p>
          <p>
          <input type="radio" name="over" value="homophones" id="over-homophones">
          <label for="over-homophones">Show count as a proportion of homophones in same period (e.g., qi₂ as a percentage of all qi, qi₂, qi₃, etc. in MA)</label>
          </p>
          <p>
          <input type="radio" name="over" value="sign" id="over-sign">
          <label for="over-sign">Show count as a proportion of usages of the sign in same period (e.g., qi₂ as a percentage of Akkadian syllabic 𒆠 in MA)</label>
          </p>""", file=f)
    print("""
          <table>
          <tr>
          <th rowspan="2"></th>
          <th rowspan="2">OAkk</th>
          <th colspan="2">OA</th>
          <th>MA</th>
          <th colspan="2">NA</th>
          </tr>
          <tr class="𒆍𒀭𒊏𒆠">
          <th>Early OB</th>
          <th>OB</th>
          <th>MB</th>
          <th>Early NB</th>
          <th>NB</th>
          </tr>
          """,
          file=f)

    for value in sign.values:
      period_to_occurrences = value_to_period_to_occurrences[value.text]
      total = 0
      periods : set[str] = set()
      for period, occurrences in period_to_occurrences.items():
        periods.add(period)
        total += len(occurrences)
      if not total:
        continue

      def entry(period: str):
        sign_occurrences = sign_occurrences_by_period[period]
        homophone_occurrences = value_to_homophone_occurrences_by_period[value.text][period]
        occurrences = period_to_occurrences[period]
        if len(occurrences) == 0:
          return "&nbsp;"
        else:
          return f"""
              <div class="count-occurrence">
              <div class="count">{len(occurrences)}</div>
              <div class="over-homophones">{len(occurrences) / len(homophone_occurrences):0.1%}</div>
              <div class="over-sign">{len(occurrences) / len(sign_occurrences):0.1%}</div>
              </div>
              <div class="count-artefact">
              <div class="count">{len(set(occurrences))}</div>
              <div class="over-homophones">{len(set(occurrences)) / len(set(homophone_occurrences)):0.1%}</div>
              <div class="over-sign">{len(set(occurrences)) / len(set(sign_occurrences)):0.1%}</div>
              </div>"""
      print(f"""
            <tr>
            <th rowspan="2">{value.text}</th>
            <td rowspan="2">{entry("OAkk")}</td>
            <td colspan="2">{entry("OA")}</td>
            <td>{entry("MA")}</td>
            <td colspan="2">{entry("NA")}</td>
            </tr>
            <tr class="𒆍𒀭𒊏𒆠">
            <td>{entry("Early OB")}</td>
            <td>{entry("OB")}</td>
            <td>{entry("MB")}</td>
            <td>{entry("Early NB")}</td>
            <td>{entry("NB")}</td>
            </tr>
            """,
            file=f)
    print("</table></body></html>", file=f)