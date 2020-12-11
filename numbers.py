
import codecs
import re
import sys
import unicodedata

sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

BASIC_FRACTIONS = {
  "1/2": ['𒈦'],
  "1/3": ['𒑚'],
  "2/3": ['𒑛'],
  "5/6": ['𒑜'],
}

# For these we provide both the 3-row and the 2-row variants, the first one
# being the 3-row one, described as the normal Babylonian form in Friberg
# (2007), 0.4 f.  See also Friberg p. 50-52.
# Note that this is reversed from
# http://oracc.museum.upenn.edu/doc/help/editinginatf/metrology/metrologicaltables/index.html.
DIŠ_NUMERALS = [
  [],
  ['𒁹'],
  ['𒈫'],
  ['𒐈'],
  ['𒐼', '𒐉'],
  ['𒐊'],
  ['𒐋'],
  ['𒑂', '𒐌'],
  ['𒑄', '𒐍'],
  ['𒑆', '𒐎'],
]

# Only the first five are used as part of the counting number systems, the rest
# appear as BÙR.  We still put them in this list so that the signs may be
# referred to by name as a ligature of multiple U signs.
# Again we follow Friberg to choose the normal form, backwards from Oracc (see
# Friberg p. 53).
U_NUMERALS = [
  [],
  ['𒌋'],
  ['𒎙'],
  ['𒌍'],
  ['𒑩', '𒐏'],
  ['𒑪', '𒐐'],
  ['𒑫', '𒐑'],
  ['𒑬', '𒐒'],
  ['𒑭', '𒐓'],
  ['𒑮', '𒐔'],
]

GÉŠ_NUMERALS = [
  [],
  ['𒐕'],
  ['𒐖'],
  ['𒐗'],
  ['𒐘'],
  ['𒐙'],
  ['𒐚'],
  ['𒐛'],
  ['𒐜'],
  ['𒐝'],
]

GEŠʾU_NUMERALS = [
  [],
  ['𒐞'],
  ['𒐟'],
  ['𒐠'],
  ['𒐡'],
  ['𒐢'],
]

ŠÁR_NUMERALS = [
  [],
  ['𒊹'],
  ['𒐣'],
  ['𒐤', '𒐥'],
  ['𒐦'],
  ['𒐧'],
  ['𒐨'],
  ['𒐩'],
  ['𒐪'],
  ['𒐫'],
]

ŠARʾU_NUMERALS = [
  [],
  ['𒐬'],
  ['𒐭'],
  ['𒐮', '𒐯'],
  ['𒐰'],
  ['𒐱'],
]

ŠARGAL_NUMERALS = [
  [sign + '𒃲' for sign in signs] for signs in ŠÁR_NUMERALS
]
ŠARGAL_NUMERALS[1] += '𒐲'
ŠARGAL_NUMERALS[2] += '𒐳'

ŠARʾUGAL_NUMERALS = [
  [sign + '𒃲' for sign in signs] for signs in ŠARʾU_NUMERALS
]

ŠARKID_NUMERALS = [
  [sign + '𒆤' for sign in signs] for signs in ŠÁR_NUMERALS
]

AŠ_NUMERALS = [
  [],
  ['𒀸'],
  ['𒐀'],
  ['𒐁', '𒐻'],
  ['𒐂'],
  ['𒐃'],
  ['𒐄'],
  ['𒐅'],
  ['𒐆'],
  ['𒐇'],
]

# Measures of area.

IKU_FRACTIONS = {
  "1/2": ['𒀹'],
  "1/4": ['𒑠'],
  "1/8": ['𒑟'],
}

IKU_NUMERALS = AŠ_NUMERALS[:6]

ÈŠE_NUMERALS = [
  [],
  ['𒑘'],
  ['𒑙'],
]

BÙR_NUMERALS = U_NUMERALS

BURʾU_NUMERALS = [
  [],
  ['𒐴'],
  ['𒐵'],
  ['𒐶', '𒐷'],
  ['𒐸'],
  ['𒐹'],
]

# Measures of capacity.

BARIG_NUMERALS = [
  [],
  ['𒁹'],
  ['𒑖'],
  ['𒑗'],
  ['𒐉'],
]

BÁN_NUMERALS = [
  [],
  ['𒑏'],
  ['𒑐'],
  ['𒑑'],
  ['𒑒', '𒑓'],
  ['𒑔', '𒑕'],
]

def numeric_value(c):
  if len(c) > 1:
    return None
  try:
    return unicodedata.numeric(c)
  except ValueError:
    return None


# Sanity check.
for name, sequence in dict(globals()).items():
  if name.startswith('__'):
    continue
  if isinstance(sequence, list):
    for i in range(len(sequence)):
      for variant in sequence[i]:
        value = numeric_value(variant)
        expected_value = 60 ** 3 * i if name == 'ŠARGAL_NUMERALS' else i
        if value is not None and value != expected_value:
          raise ValueError(
              '%s has numeric value %s but is at position %s in %s' % (
                  variant, value, i, name))
  elif isinstance(sequence, dict):
    for sequence_value, variants in sequence.items():
      for variant in variants:
        value = numeric_value(variant)
        if value is not None and value != eval(sequence_value):
          raise ValueError(
              '%s has numeric value %s but is at %s in %s' % (
                  variant, value, sequence_value, name))

compositions = {}

def add_simple_compositions(unit_name, unit_sequence):
  for n, variants in (
      unit_sequence.items() if isinstance(unit_sequence, dict) else
      enumerate(unit_sequence)):
    variant = 0
    for sign in variants:
      composition = str(n) + unit_name
      if variant:
        composition += 'v%s' % variant
      if composition in compositions and compositions[composition] != sign:
        raise ValueError('Inconsistent signs for %s: %s, %s' % (
            composition, sign, compositions[composition]))
      compositions[composition] = sign
      variant += 1

def add_sexagesimal_compositions(unit, units_sequence, tens_sequence):
  for n in range(1, 60):
    tens = n // 10
    units = n % 10
    variant = 0
    for tens_sign in tens_sequence[tens] or ['']:
      for units_sign in units_sequence[units] or ['']:
        if isinstance(unit, str):
          composition = str(n) + unit
        else:
          if not unit in (60 ** n for n in range(4)):
            raise ValueError('Unexpected unit value %r' % unit)
          composition = str(n * unit)
        if variant:
          composition += 'v%s' % variant
        sign = tens_sign + units_sign
        if composition in compositions and compositions[composition] != sign:
          raise ValueError('Inconsistent signs for %s: %s, %s' % (
              composition, sign, compositions[composition]))
        compositions[composition] = sign
        variant += 1

add_simple_compositions('', BASIC_FRACTIONS),

# These form beginning of the Sumerian counting number system, as well as the
# digits of the sexagesimal positional number system.
add_sexagesimal_compositions(1, DIŠ_NUMERALS, U_NUMERALS),
# Neo-Sumerian / Old Babylonian counting number system.
add_sexagesimal_compositions(60, GÉŠ_NUMERALS, GEŠʾU_NUMERALS)
add_sexagesimal_compositions(60 ** 2, ŠÁR_NUMERALS, ŠARʾU_NUMERALS)
add_sexagesimal_compositions(60 ** 3, ŠARGAL_NUMERALS, ŠARʾUGAL_NUMERALS)

# Neo-Sumerian / Old Babylonian capacity system.
add_simple_compositions('ban2', BÁN_NUMERALS)
add_simple_compositions('barig', BARIG_NUMERALS)

# Area system.
add_simple_compositions('iku', IKU_FRACTIONS)
add_simple_compositions('iku', IKU_NUMERALS)
add_simple_compositions('eše3', ÈŠE_NUMERALS)
add_sexagesimal_compositions('bur3', BÙR_NUMERALS, BURʾU_NUMERALS)
add_sexagesimal_compositions('šar2', ŠÁR_NUMERALS, ŠARʾU_NUMERALS)
add_sexagesimal_compositions('šargal', ŠARGAL_NUMERALS, ŠARʾUGAL_NUMERALS)
add_simple_compositions('šarkid', ŠARKID_NUMERALS)

# Referring to Neo-Sumerian / Old Babylonian sexagesimal positions by name.
add_sexagesimal_compositions('geš2', GÉŠ_NUMERALS, GEŠʾU_NUMERALS)
add_sexagesimal_compositions('šar2', ŠÁR_NUMERALS, ŠARʾU_NUMERALS)
add_sexagesimal_compositions('šargal', ŠARGAL_NUMERALS, ŠARʾUGAL_NUMERALS)

# Referring to signs by by name (except DIŠ since it is our default).
add_simple_compositions('aš', AŠ_NUMERALS)
add_simple_compositions('u', U_NUMERALS)
# Not putting the alephs there as MesZL does not an aleph on šaru.
add_simple_compositions('buru', BURʾU_NUMERALS)
add_simple_compositions('gešu', GEŠʾU_NUMERALS)
add_simple_compositions('šaru', ŠARʾU_NUMERALS)
add_simple_compositions('šarugal', ŠARʾUGAL_NUMERALS)

compositions_by_sign = {}
for composition, sign in compositions.items():
  compositions_by_sign.setdefault(sign, []).append(composition)
