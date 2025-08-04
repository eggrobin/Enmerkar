from collections import defaultdict
import json
import os
import urllib.parse
from typing import Any

import atf
import asl

language_to_value_to_period_to_occurrences : dict[
  str, dict[
    str, dict[
      str, list[str]]]] = defaultdict(
        lambda: defaultdict(
          lambda: defaultdict(list)))

def get_base(value: str):
  return value.rstrip("₀₁₂₃₄₅₆₇₈₉")
def is_consonant(letter: str):
  return letter in set("ʾbdghklmnpqrsṣštṭvwyz")
def is_vowel(letter: str):
  return letter in set("aeui")
def is_cv(value: str):
  base = get_base(value)
  return len(base) == 2 and is_consonant(base[0]) and is_vowel(base[1])
def is_vc(value: str):
  base = get_base(value)
  return len(base) == 2 and is_vowel(base[0]) and is_consonant(base[1])
def is_cvc(value: str):
  base = get_base(value)
  return len(base) == 3 and is_consonant(base[0]) and is_vowel(base[1]) and is_consonant(base[2])
def vowel(syllable_value: str):
  base = get_base(syllable_value)
  vowel, = (v for v in base if is_vowel(v))
  return vowel

def index_values(text_json: Any,
                 artefact: str,
                 period: str,
                 genre: str,
                 lang: str = "und",
                 consecutive_values:list[str]|None=None):
  if "det" in text_json:
    if consecutive_values:
      consecutive_values.clear()
    return
  if "lang" in text_json:
    lang = text_json["lang"].split("-")[0]
  if "cdl" in text_json:
    for node in text_json["cdl"]:
      index_values(node, artefact, period, genre, lang)
  if "f" in text_json:
      index_values(text_json["f"], artefact, period, genre, lang)
  if "gdl" in text_json:
     gdl_values : list[str] = []
     for node in text_json["gdl"]:
      index_values(node, artefact, period, genre, lang, gdl_values)
  if "group" in text_json:
     for node in text_json["group"]:
      index_values(node, artefact, period, genre, lang)
  if "seq" in text_json:
     for node in text_json["seq"]:
      index_values(node, artefact, period, genre, lang)
  # We do not go down into "qualified" for now (the index is on default values).
  if "v" in text_json:
    if consecutive_values is not None:
      if consecutive_values:
        preceding = consecutive_values[-1]
        if is_cv(preceding) and is_vc(text_json["v"]) and vowel(preceding) == vowel(text_json["v"]):
          language_to_value_to_period_to_occurrences[
            lang][preceding + "-" + text_json["v"]][period].append(artefact)
      if text_json.get("delim") == "-":
        consecutive_values.append(text_json["v"])
      else:
        consecutive_values.clear()
    language_to_value_to_period_to_occurrences[
      lang][text_json["v"]][period].append(artefact)
  elif consecutive_values:
    consecutive_values.clear()

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

ORACC_PROJECTS = ("akklove", "atae", "babcity", "balt", "blms", "dcclt", "riao", "ribo", "rinap", "saao", "tcma")

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

syllabary_index : list[asl.Sign] = []
base_to_values : dict[str, list[str]] = defaultdict(list)

HEAD = """
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
"""

SOURCE = f"""
<p>Based on transliterations from CDLI and Oracc projects {", ".join(ORACC_PROJECTS)}.</p>
"""

COUNT_SELECTOR = """
<p>
<input type="radio" name="count" value="occurrence" id="count-occurrence" checked>
<label for="count-occurrence">Count occurrences</label>
</p>
<p>
<input type="radio" name="count" value="artefact" id="count-artefact">
<label for="count-artefact">Count artefacts</label>
</p>
"""

RATIO_SELECTOR = """
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
</p>
"""

TABLE_PERIODS = """
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
"""

value_to_period_to_occurrences = language_to_value_to_period_to_occurrences["akk"]
sign_to_period_to_occurrences : dict[asl.Sign, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
base_to_period_to_occurrences : dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
base_to_signs_and_values : dict[str, list[tuple[asl.Sign, asl.Value]]] = defaultdict(list)
values_to_signs : dict[asl.Value, asl.Sign] = {}

for sign in asl.osl.signs:
  if not isinstance(sign, asl.Sign) or sign.deprecated:
    continue
  for value in sign.values:
    if value.deprecated:
      continue
    if value.text == "xₓ":
      # A garbage value which somehow sneaks in unqualified in a few places in
      # Oracc.
      continue
    if "-" in value.text:
      # - in OSL values is an oddity which we ignore (otherwise it is
      # ambiguous whether a sequence of values is one or two signs).
      continue
    values_to_signs[value] = sign
    usage = value_to_period_to_occurrences[value.text]
    for period, occurrences in usage.items():
      if "ₓ" in value.text:
        raise ValueError(value.text, occurrences)
      sign_to_period_to_occurrences[sign][period] += occurrences
    base = get_base(value.text)
    base_to_signs_and_values[base].append((sign, value))

for value, period_to_occurrences in value_to_period_to_occurrences.items():
  base = get_base(value)
  for period, occurrences in period_to_occurrences.items():
    base_to_period_to_occurrences[base][period] += occurrences

def entry(period: str, value: asl.Value, sign: asl.Sign):
  sign_occurrences = sign_to_period_to_occurrences[sign][period]
  homophone_occurrences = base_to_period_to_occurrences[get_base(value.text)][period]
  occurrences = value_to_period_to_occurrences[value.text][period]
  if len(occurrences) == 0:
    return "&nbsp;"
  else:
    return f"""
        <div class="count-occurrence">
        <div class="count">{len(occurrences)}</div>
        <div class="over-homophones">{len(occurrences) / len(homophone_occurrences):0.0%}</div>
        <div class="over-sign">{len(occurrences) / len(sign_occurrences):0.0%}</div>
        </div>
        <div class="count-artefact">
        <div class="count">{len(set(occurrences))}</div>
        <div class="over-homophones">{len(set(occurrences)) / len(set(homophone_occurrences)):0.0%}</div>
        <div class="over-sign">{len(set(occurrences)) / len(set(sign_occurrences)):0.0%}</div>
        </div>"""

def table_row(value: asl.Value, sign: asl.Sign, sign_specific_table: bool):
  base = get_base(value.text)
  return f"""
      <tr>
      <th rowspan="2"><a href="{
        f"homophones/{base}.html" if sign_specific_table else
        f'../{sign.names[0].replace("|", "").replace("/", "-")}.html'
      }">{
        value.text
      }{
        "" if sign_specific_table else
        f"({sign.unicode_cuneiform.text if sign.unicode_cuneiform else sign.names[0]})"
      }</a></th>
      <td rowspan="2">{entry("OAkk", value, sign)}</td>
      <td colspan="2">{entry("OA", value, sign)}</td>
      <td>{entry("MA", value, sign)}</td>
      <td colspan="2">{entry("NA", value, sign)}</td>
      </tr>
      <tr class="𒆍𒀭𒊏𒆠">
      <td>{entry("Early OB", value, sign)}</td>
      <td>{entry("OB", value, sign)}</td>
      <td>{entry("MB", value, sign)}</td>
      <td>{entry("Early NB", value, sign)}</td>
      <td>{entry("NB", value, sign)}</td>
      </tr>
      """

for sign in asl.osl.signs:
  if isinstance(sign, asl.Sign):
    if sign not in sign_to_period_to_occurrences:
      continue
    with open("syllabary/akk/" + sign.names[0].replace("|", "").replace("/", "-") + ".html", mode="w", encoding="utf-8") as f:
      print(HEAD,
            file=f)
      print(f"<h1>Akkadian syllabic values of {sign.unicode_cuneiform.text if sign.unicode_cuneiform else sign.names[0]}</h1>", file=f)
      print(SOURCE, file=f)
      print(COUNT_SELECTOR, file=f)
      print(RATIO_SELECTOR, file=f)
      print(TABLE_PERIODS, file=f)

      for value in sign.values:
        if value.deprecated:
          continue
        if value.text == "xₓ":
          continue
        if not value_to_period_to_occurrences[value.text]:
          continue
        print(table_row(value, sign, sign_specific_table=True), file=f)

      print("</table></body></html>", file=f)

for base, signs_and_values in base_to_signs_and_values.items():
  if not any(value_to_period_to_occurrences[value.text] for _, value in signs_and_values):
    continue
  with open("syllabary/akk/homophones/" + base + ".html", mode="w", encoding="utf-8") as f:
    print(HEAD,
          file=f)
    print(f"<h1>Akkadian syllabic homophones of {base}</h1>", file=f)
    print(SOURCE, file=f)
    print(COUNT_SELECTOR, file=f)
    print(RATIO_SELECTOR, file=f)
    print(TABLE_PERIODS, file=f)

    for sign, value in sorted(signs_and_values, key=lambda sv: sv[1].text):
      if not value_to_period_to_occurrences[value.text]:
        continue
      print(table_row(value, sign, sign_specific_table=False), file=f)

    print("</table></body></html>", file=f)

with open("syllabary/akk/index.html", mode="w", encoding="utf-8") as f:
  print("<ul>", file=f)
  for sign in asl.osl.signs:
    if isinstance(sign, asl.Sign):
      if sign not in sign_to_period_to_occurrences:
        continue
      print(f"<li><a href='{urllib.parse.quote(sign.names[0].replace('|', '').replace('/', '-'))}.html'>{sign.unicode_cuneiform.text if sign.unicode_cuneiform else ''} {sign.names[0]}</a></li>",
            file=f)
  print("</ul>", file=f)