import json
import os
import sys
import urllib.request
import zipfile

def get_oracc_json_from_zip(z: str):
  if z in os.listdir("oracc"):
    z = f"oracc/{z}"
    print(f"Reusing downloaded {z}...")
  else:
    print(f"Downloading {z}...")
    z, _ = urllib.request.urlretrieve(f"http://oracc.org/json/{z}",
                                      f"oracc/{z}")

  with zipfile.ZipFile(z, 'r') as f:
    f.extractall("oracc/")

for project in sys.argv[1:]:
  get_oracc_json_from_zip(f"{project}.zip")

  with open(f"oracc/{project}/corpus.json", encoding="utf-8") as f:
    corpus = json.loads(f.read())
    subprojects : set[str] = set(corpus["proxies"].values())

  for subproject in subprojects:
    if subproject in ("uet6", "pcsl"):
      print(f"Skipping {subproject}")
      continue
    get_oracc_json_from_zip(subproject.replace("/", "-") + ".zip")