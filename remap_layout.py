import html
import re

dvorak_lower = """
⫶  1  2  3  4  5  6  7  8  9  0  [  ]
    ʾ  ṣ  ṭ  p  ŋ  f  g  š  r  l  /  +  \
     a  ś  e  u  i  d  ḫ  t  n  s  -
      :  q  j  k  x  b  m  w  v  z
""".split()
dvorak_upper = """
¹  !  ́   ̀   «  »  ̂   ̄   *  (  )  ⸢  ⸣
    ‹  Ṣ  Ṭ  P  Ŋ  F  G  Š  R  L  ?  =  ×
     A  Ś  E  U  I  D  Ḫ  T  N  S  .
      ›  Q  J  K  X  B  M  W  V  Z
""".split()
qwerty_lower = """
⫶  1  2  3  4  5  6  7  8  9  0  -  +
    q  w  e  r  t  ŋ  u  i  ś  p  [  ]  \
     a  s  d  f  g  ḫ  j  k  l  :  ʾ
      z  x  š  v  b  n  m  ṣ  ṭ  /
""".split()
qwerty_upper = """
¹  !  ́   ̀   «  »  ̂   ̄   *  (  )  .  =
    Q  W  E  R  T  Ŋ  U  I  Ś  P  ⸢  ⸣  ×
     A  S  D  F  G  Ḫ  J  K  L  ‹  ›
      Z  X  Š  V  B  N  M  Ṣ  Ṭ  ?
""".split()

with open("mac/ʾṣṭpŋf.keylayout", "r") as f:
  for line in f.readlines():
    match = re.match(r'.*output="([^"]*)".*', line)
    if match:
      if html.unescape(match.group(1)) not in list(dvorak_lower) + dvorak_upper + ["§"]:
        raise Exception(line, match.group(1))