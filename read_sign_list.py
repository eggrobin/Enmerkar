import codecs
import csv
import re
import sys

import numbers

sys.stdout = codecs.getwriter("utf-16")(sys.stdout.detach())

SOURCES = ['MesZL', 'Labat', 'ABZ']

def is_printable_basic_latin(c):
  return c >= "!" and c <= "~"

def is_lowercase_akkadian_letter(c):
  return c in 'bdgptkʾṭqzšsṣḫmnrlwyjaeiu'

def is_capital_akkadian_letter(c):
  return c in 'bdgptkʾṭqzšsṣḫmnrlwyjaeiu'.upper()

def is_digit(c):
  return c >= '0' and c <= '9'

def is_composition_sign(c):
  return c in 'f:⫶/v'

def is_composition_character(c):
  return (is_lowercase_akkadian_letter(c) or
          is_digit(c) or
          is_composition_sign(c))

class Reading:
  def __init__(self, sign, šašková_index):
    self.value = ''
    self.comment = ''
    self.source = ''
    self.disambiguator = ''
    self.sign = sign
    self.šašková_index = šašková_index
    self.keep = True

  def composition(self):
    return self.value.lower() + self.disambiguator

  def normalize(self):
    # Properly write aleph, Y is a synonym for J, and we handle variant more
    # comprehensively than the single KAMᵛ.
    self.value = self.value.strip().replace(
        '’', 'ʾ').replace('Y', 'J').replace('v', '')
    self.comment = self.comment.replace('’', 'ʾ')
    source = re.match('^(\w+)[;:]', self.comment)
    if source:
      source = source[1]
      if source == 'KŠ':
        # Kateřina Šašková marks her own comments like this.
        # Since we are processing her list, everything is by definition therein;
        # the source field tracks provenance from older lists.
        return
      if source in ('MesZ', 'MeZL', 'MeLZ', 'MesLZ'):  # Typos.
        source = 'MesZL'
      if source not in SOURCES:
        raise ValueError('Unexpected source %s' % source)
      self.source = source
      
readings_by_value = {}
readings_by_sign = {}

def insert_parentheses(original, amendment):
  original_segment = amendment.replace('[', '').replace(']', '')
  amended_segment = amendment.replace('[', '(').replace(']', ')')
  return original.replace(original_segment, amended_segment)

def delete_parentheses(original, amendment):
  original_segment = amendment.replace('[', '(').replace(']', ')')
  amended_segment = amendment.replace('[', '').replace(']', '')
  return original.replace(original_segment, amended_segment)

with open(r".\sign_list.csv", encoding="utf-8") as file:
  reader = csv.reader(file)
  ok_entries = 0
  erroneous_entries = 0
  meszl_seen = {}

  row_index = 0

  for row in reader:
    meszl = row[3]
    if any(is_printable_basic_latin(c) for c in row[0] + row[1]) or row[0] != row[1]:
      if meszl == '003+003\n(839+756+003+003)':
        # A spelling of Idiqlat in the MesZL glossary.  No sign name, just type
        # it as ḪAL.ḪAL.
        continue
      elif row[2].startswith('UŠUMX\n'):
        pass  # UŠUMₓ is missing in the Sinacherib font.
      elif row[2].startswith('ARAD x ŠE\n'):
        continue  # Labat has ìr×še but Borger does not; it is not encoded.
      elif (row[0] and
            all(not is_printable_basic_latin(c) for c in row[0]) and
            all(c in ' x' for c in row[1] if is_printable_basic_latin(c))):
        pass  # Signs missing in the Sinacherib font.
      elif meszl == '58':
        continue  # 𒅗×𒌍 is an unencoded variant of 𒅗×𒊓 = 𒅾.
      elif meszl in (
          '27',
          '36',  # HZL 137: unbekannte Bedeutung (Gegenstand aus Holz).
          '40',  # HZL 138: Gerät?, Behälter? aus Kupfer.
          '41',  # HZL 139: ein Behälter aus Holz.
          '55',
          '67',  # HZL 150: Körperteilbezeichnung?
          '70',  # HZL 142: u.B.
        ):
        # Signs from https://www.unicode.org/wg2/docs/n4277.pdf.
        pass
      elif 'BAD squared' in row[2]:
        # We unify BAD squared with IDIM over IDIM squared, since IDIM is part
        # of BAD in both Labat and Borger, and both sign lists mention only a
        # squared BAD, not a squared IDIM over IDIM; indeed the latter has no
        # reading in Šašková.
        pass
      elif row[2].startswith('NUN crossing NUN.LAGAR over LAGAR'):
        continue  # Unified with TUR3 over TUR3.
      elif row[2].startswith('ŠIR over ŠIR.BUR over BUR'):
        pass  # Sign missing in the Sinacherib font.
      else:
        raise ValueError(row)


      row_index += 1
      if not row[0]:
        continue
      if meszl in meszl_seen:
        meszl_seen[meszl] += 1
        meszl += '/%d' % meszl_seen[meszl]
      else:
        meszl_seen[meszl] = 1
      readings = ' '.join(row[2].split('\n')[1:-1])
      uncommented_readings = ''
      if not readings:
        readings = '()'
      # Mismatched parentheses; by MesZL number; entries with identical MesZL number
      # are indexed after the slash.
      if meszl in ('69', '598/5'):
        readings = '(' + readings
      elif meszl in (
              '848', '45', '84', '129', '187', '193', '202', '223+889+552',
              '266 (sign LUGAL)', '302+596', '353/2', '469+809+598+590/2',
              '491+380', '491+748', '491+839', '541+184', '545', '724+136',
              '737+755', '839+010+387', '839+756+202',
          ):
        readings += ')'
      elif meszl in ('001+183', '280 (sign EZEN x MIR)', '575+183', '748+183'):
        readings = '(' + readings + ')'
      elif meszl in ('242+753', '380+827', '546\nalso 485', '703/2', '883+149', '883+827'):
        if readings[-1] != ')':
          raise ValueError('No trailing parenthesis to strip from readings in %r' % row)
        readings = readings[:-1]
      elif meszl in ('13', '184+464+755'):
        readings = readings.replace('))),', ')),')
      elif meszl in ('701+232+553', '701+232+553/2', '788', '836'):
        readings = readings.replace(')),', '),')
      elif meszl == '84':
        readings = insert_parentheses(readings, '([MesZL: variant of KA x GU (no. 69)];')
      elif meszl == '142':
        readings = insert_parentheses(readings, '(ŠAR5 = IM (no. 641)]')
      elif meszl == '150':
        readings = insert_parentheses(readings, '(Labat; MesZL: ŠURU6 = KID2 (no. 106)]')
      elif meszl == '010+296':
        readings = delete_parentheses(readings, '(= MesZL 296)];')
      elif meszl == '296':
        readings = delete_parentheses(readings, '(= MesZL 296)];')
      elif meszl == '348':
        readings = insert_parentheses(readings, '(MesZL: AL x ŠE (no. 479) = IL (no. 348)];')
      elif meszl == '362+010+120':
        readings = insert_parentheses(readings, ' (nos. 362+010+887+809+807)]')
      elif meszl == '479, 348':
        readings = insert_parentheses(readings, '(no. 348)];')
      elif meszl == '490':
        readings = delete_parentheses(readings, 'PU11, PU8 missing)]')
      elif meszl == '560+132':
        readings = insert_parentheses(readings, '(no. 560)],')
      elif meszl in ('809+816+580', '809+816+584'):
        readings = delete_parentheses(readings, '[MUPARRU')
      elif meszl == '839':
        readings = insert_parentheses(readings, '(no. 856)],')
      elif meszl == '883+381':
        readings = insert_parentheses(readings, '(nos. 382+889)],')
      elif meszl == '092, also 585':
        readings = insert_parentheses(readings, '([MesZL: see MUŠ (no. 585) and PAB (no. 92)];')

      if meszl == '572':
        readings = readings.replace(
            '((MesZL: instead of KAŠŠEBA, KAŠŠEBI)',
            '((MesZL: instead of KAŠŠEBA, KAŠŠEBI);')
      if meszl == '577/2' or meszl == '576/2':
        # We have these glyphs and their readings for proper letter signs;
        # imparting these readings to the punctuation signs (they have separate
        # transcriptions for those roles given in MesZL).
        continue
      if meszl == '863':
        # We have two variants of a numeric sign for IMIN already, the use of a
        # disunified non-numeric sign is unclear, especially since which variant
        # is picked ends up being font-dependent...
        continue

      if readings[0] != '(' or readings[-1] != ')':
        raise ValueError(row)

      processed_readings = ''
      depth = 0
      sign = row[0]
      # Unify BAD squared and IDIM over IDIM squared, see above.
      sign = sign.replace('.𒁁squared', '𒅄')
      sign = sign.replace('𒁁squared', '𒅄')
      sign = sign.replace('𒍗squared', '𒅄')

      # For some reason Šašková does not always use 𒌍, which was there in the
      # initial Unicode 5.0 character set.
      sign = sign.replace('𒌋𒌋𒌋', '𒌍')

      # Use the signs from https://www.unicode.org/wg2/docs/n4277.pdf.
      # Global substitutions: U.U and ME.EŠ are always MAN and MEŠ.
      sign = sign.replace('𒌋𒌋', '𒎙').replace('𒈨𒌍', '𒎌')
      # Disunification of ŠAR₂ 𒊹 and TI₂ 𒎗.
      if meszl == '633':
        sign = '𒎗'
      sign = sign.replace('𒅗 x 𒌅', '𒎆')
      sign = sign.replace('𒅗 x 𒌫', '𒎇')
      sign = sign.replace('𒅗 x 𒉺', '𒎄')
      sign = sign.replace('𒅗 x 𒄑', '𒎀')
      sign = sign.replace('𒅗 x 𒄯', '𒎂')
      sign = sign.replace('𒅗 x 𒐋', '𒍿')
      sign = sign.replace('𒅗 x 𒈝', '𒎃')

      if any(is_printable_basic_latin(c) for c in sign):
        raise ValueError(sign)

      first_reading = Reading(sign, row_index)
      first_reading.value = row[2].split('\n')[0]

      if sign == '𒇽𒇽' and first_reading.value == 'LU2 over LU2':
        # Not encoded, same reading as LU2.LU2 which is in the list.
        continue

      sign_readings = [first_reading]
      current_reading = first_reading
      for c in readings:
        processed_readings += c
        if depth == 1 and c in ',;':
          current_reading = Reading(sign, row_index)
          sign_readings.append(current_reading)
          continue  # Consume delimiters between comments.
        if c == '(':
          depth += 1
          if depth in (1, 2):
            continue  # Consume the initial & start-of-comment parentheses.
        elif c == ')':
          depth -= 1
          if depth in (0, 1):
            continue  # Consume the final & end-of-comment parentheses.

        if depth == 1:
          if current_reading is first_reading:
            current_reading = Reading(sign, row_index)
            sign_readings.append(current_reading)
          current_reading.value += c
          if current_reading.comment:
            raise ValueError(
                'Reading %s restarts after comment %s [MesZL %s]' % (
                    current_reading.value, current_reading.comment, meszl))
        elif depth > 1:
          current_reading.comment += c
        else:
          raise ValueError('surfaced before end of readings: %s[!] %r' % (processed_readings, row))
      if depth != 0:
        raise ValueError('depth=%d at end of readings %r' % (depth, row))
      for reading in sign_readings:
        reading.normalize()
      # We handle numbers ourselves, and thus discard any numerical readings
      # found in Šašková.
      sign_readings = [
          reading for reading in sign_readings
          if any (c.isalpha() for c in reading.value)]

      # Deal with the disunification of 60 and 1 in Unicode.
      for reading in sign_readings:
        # Readings given for 60 in MesZL 748.
        if reading.sign == '𒁹' and reading.value in ('GEŠ2', 'GIŠ2', 'GEŠTA'):
          reading.sign = '𒐕'
        # Labat-only readings for 60n.
        if reading.sign == '𒐊' and reading.value == 'GEŠIA':
          reading.sign = '𒐙'
        if reading.sign == '𒐋' and reading.value == 'GEŠAŠ':
          reading.sign = '𒐚'
        if reading.sign in '𒐌𒑂' and reading.value == 'GEŠUMUN':
          reading.sign = '𒐛'
        if reading.sign in '𒐍𒑄' and reading.value == 'GEŠUSSU':
          reading.sign = '𒐜'
        if reading.sign == '𒑆' and reading.value == 'GEŠILIMMU':
          reading.sign = '𒐝'

      for reading in sign_readings:
        readings_by_value.setdefault(reading.value, []).append(reading)
        readings_by_sign.setdefault(reading.sign, []).append(reading)
      ok_entries += 1

# Insert the numbers which we listed ourselves.
for sign, compositions in numbers.compositions_by_sign.items():
  for composition in compositions:
    reading = Reading(sign, šašková_index=None)
    reading.value = composition
    readings_by_value.setdefault(reading.composition, []).append(reading)
    readings_by_sign.setdefault(reading.sign, []).append(reading)

# Punctuation and common determinatives.
for sign, compositions in {
    # MesZL 592.
    '𒑱' : [':'],
    # MesZL 576: Trennungszeichen (wie n592; Umschrift :).  Disunified from GAM
    # in Unicode.
    '𒑲' : [':v1'],
    # MesZL 577: Trennungs- und Wiederholungszeichen (Umschrift mit Parpola,
    # LASEA pXX ⫶).  Disunified from ILIMMU4 in Unicode.
    '𒑳' : ['⫶'],
    # Word divider.  See MesZL 748, p. 418: In Kültepe wird ein senkrechter Keil
    # als Worttrenner gebraucht.  Disunified from DIŠ in Unicode.
    # See AAA 1/3, 01 for an example usage:
    # https://cdli.ucla.edu/search/archival_view.php?ObjectID=P360975.
    # We use the transcription convention from CDLI, a forward slash.
    '𒑰' : ['/'],
    # Determinatives for personal names and gods.
    '𒁹' : ['m'],
    '𒊩' : ['f'],
    '𒀭' : ['d'],
  }.items():
  for composition in compositions:
    reading = Reading(sign, šašková_index=None)
    reading.value = composition
    readings_by_value.setdefault(reading.composition, []).append(reading)
    readings_by_sign.setdefault(reading.sign, []).append(reading)

readings_by_composition = {}

def recompute_readings_by_composition():
  readings_by_composition.clear()
  for readings in readings_by_sign.values():
    for reading in readings:
      readings_by_composition.setdefault(reading.composition(), []).append(reading)

def sign_name(sign):
  return readings_by_sign[sign][0].value

def print_readings(value, readings, by_source=False):
  print(value, file=sys.stderr)
  for reading in readings:
    print('    ', reading.source.ljust(6) if by_source else ('...' + reading.disambiguator.ljust(8)),
          reading.sign, sign_name(reading.sign), 8 * ' ', reading.comment, file=sys.stderr)

for value, readings in readings_by_value.items():
  if len(readings) > 1:
    # Duplicates, with inconsistent duplicates explicitly listed.
    for reading in readings:
      if not reading.keep:
        continue
      for other in readings:
        if other.keep and other.sign == reading.sign and other is not reading:
          if (other.keep and
              ((other.comment and reading.comment and other.comment != reading.comment) or
               (other.source and reading.source and other.source != reading.source)) and
              (value, sign_name(reading.sign)) not in (
                  # One entry is a superset of the other.
                  ('IL', 'AL x ŠE'),
                  # The comments on these Labat readings are inconsistent
                  # (MesZL: AŠLAG missing vs. MesZL: AŠLAG = TUG2.UD), the
                  # latter being right.
                  ('AŠLAG', 'GIŠ.TUG2.PI.KAR'),
                  # MesZL and Labat readings in agreement, with a ? from MesZL.
                  ('GAMBI', 'MUNUS.UŠ.DI'),
                  # MesZL 905 and 906 unified in Unicode (as in Labat).
                  ('MUR7', 'SIG4')
              )):
            print_readings(value, readings, by_source=True)
            raise ValueError('Inconsistent duplicate readings')
          other.keep = False
    # Ambiguous readings coming from inconsistency between sign lists.
    if any(reading.source and reading.source != 'MesZL' for reading in readings):
      for reading in readings:
        if not reading.source:
          implicit_meszl = any(
              re.match(
                  other.comment,
                  'MesZL: (\w+, *)*%s(, *\w+)* = %s' % (value, readings_by_sign[reading.sign][0].value))
              for other in readings)
          if implicit_meszl:
            reading.source = 'MesZL'
          else:
            print_readings(value, readings, by_source=True)
            raise ValueError("Divergent readings with undetermined source")
      if not all(reading.source == readings[0].source for reading in readings):
        for reading in readings:
          reading.disambiguator += reading.source[0]

for reading_dict in (readings_by_sign,
                     readings_by_value):
  filtered_dict = {
      key: [reading for reading in readings if reading.keep]
      for key, readings in reading_dict.items()
  }
  reading_dict.clear()
  reading_dict.update(filtered_dict)

recompute_readings_by_composition()

for readings in readings_by_composition.values():
  if len(readings) > 1:
    readings.sort(key=lambda r: r.šašková_index)
    i = 0
    for reading in readings:
      if i:
        reading.disambiguator += 'v%d' % i
      i += 1

recompute_readings_by_composition()

for composition, readings in readings_by_composition.items():
  if len(readings) > 1:
    print_readings(composition, readings)
    raise ValueError('Ambiguous composition')

# Sanity check of numbers: 1meow and meow must map to the same sign.
for composition, readings in readings_by_composition.items():
  if re.match('^1\D', composition):
    if composition[1:] in readings_by_composition:
      if readings[0].sign != readings_by_composition[composition[1:]][0].sign:
        if composition in ('1iku', '1buru'):
          # Borger gives iku as a reading for 𒃷 in 𒀸𒃷.  Friberg sees that as
          # a determinative, and transcribes it 1iku GAN2.  Shrug.
          # Buru seems wtf.
          continue
        print_readings(composition, readings)
        print_readings(composition[1:], readings_by_composition[composition[1:]])
        raise ValueError('Inconsistent numeric readings')

for composition, readings in readings_by_composition.items():
  if not all(is_composition_character(c.lower()) for c in composition):
    continue
  print('"%s"="%s"' % (composition, readings[0].sign))
