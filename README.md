# 𒂗𒈨𒅕𒃸
𒂗𒈨𒅕𒃸 (en-me-er-kár, Enmerkar) is a Sumero-Akkadian cuneiform input method for Windows.

It is based on the [sample IME from *Windows classic samples* by
Microsoft Corporation](https://github.com/microsoft/Windows-classic-samples/tree/22b652b35ea19c544b4ee541f91a59e5e8d8c070/Samples/IME),
available under the MIT license.
Its sign list is based on the [Oracc Global Sign List](http://oracc.museum.upenn.edu/ogsl/)
by the OGSL Project ([available in machine readable form on GitHub](https://github.com/oracc/ogsl)),
available under the CC BY-SA 3.0 license.
Adjustments were made to the sign list, in particular to take into account
[signs](https://www.unicode.org/wg2/docs/n4277.pdf) newly encoded in Unicode 7.0 (2014).
We are in the process of [upstreaming](https://github.com/oracc/ogsl/pulls?q=is%3Apr+author%3Aeggrobin) these adjustments.

## Installation

Download the installer (`Enmerkar.msi`) for the latest release from https://github.com/eggrobin/Enmerkar/releases, and run the installer; select an appropriate keyboard layout (be that one in which you touch type, or the one matching your physical keyboard) in the installer.

## Usage

Once 𒂗𒈨𒅕𒃸 is installed, the list of keyboard layouts in the [Language bar](https://support.microsoft.com/en-us/topic/switch-between-languages-using-the-language-bar-1c2242c0-fe15-4bc3-99bc-535de6f4f258) should have a new entry.
> 𒀝 Syriac  
> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Akkadian IME

> ###### Notes.
> The language of the input method is Syriac, rather than Akkadian, because Windows does not support arbitrary language codes in
[the relevant API](https://docs.microsoft.com/en-us/windows/win32/api/msctf/nf-msctf-itfinputprocessorprofilemgr-registerprofile),
and instead uses [the deprecated `LANGID`](https://docs.microsoft.com/en-us/windows/win32/intl/language-identifier-constants-and-strings),
which only supports a relatively small set of languages, and in particular has no equivalent to `akk`. We apologize for the inconvenience.  
> The icon, which, for keyboard layouts, is normally an abbreviation of the language names (**ΕΛ**, **ENG**, **FRA**, **РУС**, etc.),
> is here 𒀝, consistent with 𒀝𒅗𒁺𒌑; note that the IME can also be used to type Elamite, Hittite, or Sumerian (its default
> layouts all have the letter ŋ).

Select this IME to type Sumero-Akkadian cuneiform signs.

When using the IME, typing a transliteration will bring up a menu with possible completions; pressing the spacebar `␣` or the enter key `⏎` will cause the selected sign to be entered, as shown in the table below.
| Keys | Output |
|---|---|
|`a` `␣` | 𒀀 |
|`n` `a` `␣` | 𒈾 |
|`a` `␣` `n` `a` `␣` | 𒀀𒈾 |
|`e` `␣`             | 𒂊 |
|`e` `2` `␣`         | 𒂍 |
|`d` `␣` `3` `0` `␣` | 𒀭𒌍 |
|`d` `␣` `s` `i` `n` `␣` | 𒀭𒌍 |

### Spelling

We use j rather than i̯ or y, w rather than u̯, ŋ rather than g̃ or ĝ, ḫ rather than h.
Keys are assigned to the letters ŋ, ḫ, ṣ, š, ś, and ṭ (see below for their placement); they should not be
entered as digraphs.

### Word separation

For the sake of editability, linebreaking, and searchability, we recommend that you separate words; this can
be done without introducing unsightly spaces using the zero-width space, which may be entered using the
transliteration `/`.

The Old Assyrian word divider 𒑰 can serve the same function (while it looks similar to DIŠ 𒁹, it is a
different character, recognized by Unicode as punctuation, and thus it breaks words for the purposes of text
processing). It may be entered as `/v`.

Examples below. Note that thanks to the word separation, if you double-click on the cuneiform text below, a single word will* be selected, instead of the whole text; in the case of the Sumerian text, a search engine will then readily find the uninflected words in ePSD2.

| Key sequences | Output |
|---|---|
| [`e␣` `nu␣` `ma␣` `/␣` `e␣` `liš␣` `/␣` `la␣` `/␣` `na␣` `bu␣` `u2␣` `/␣` `ša2␣` `ma␣` `mu␣` `/␣` `šap␣` `liš␣` `/␣` `am␣` `ma␣` `tum␣` `/␣` `šu␣` `ma␣` `/␣` `la␣` `/␣` `zak␣` `rat␣`](https://cdli.ucla.edu/search/search_results.php?SearchMode=Text&ObjectID=P480701) | 𒂊𒉡𒈠​𒂊𒇺​𒆷​𒈾𒁍𒌑​𒃻𒈠𒈬​𒉺𒅁𒇺​𒄠𒈠𒌈​𒋗𒈠​𒆷​𒍠𒋥 |
| [`a␣` `na␣` `/␣` `d␣` `en␣` `lil2␣` `ba␣` `ni␣` `/␣` `qi2␣` `bi2␣` `ma␣` `/v␣` `um␣` `ma␣` `/␣` `ta␣` `ri␣` `iš␣` `ma␣` `tum␣` `ma␣`](https://cdli.ucla.edu/search/search_results.php?SearchMode=Text&ObjectID=P360975) | 𒀀𒈾​𒀭𒂗𒆤𒁀𒉌​𒆠𒉈𒈠𒑰𒌝𒈠​𒋫𒊑𒅖𒈠𒌈𒈠 |
| [`ud␣` `bi␣` `ta␣` `/␣` `inim␣` `/␣` `im␣` `ma␣` `/␣` `gub␣` `bu␣` `/␣` `nu␣` `ub␣` `ta␣` `ŋal2␣` `la␣` `/␣` `i3␣` `ne␣` `eš2␣` `/␣` `d␣` `utu␣` `/␣` `ud␣` `ne␣` `a␣` `/␣` `ur5␣` `/␣` `ḫe2␣` `en␣` `na␣` `nam␣` `ma␣` `am3␣`](https://etcsl.orinst.ox.ac.uk/cgi-bin/etcsl.cgi?text=c.1.8.2.3&display=Crit&charenc=gtilde&lineid=c1823.504#c1823.504) | 𒌓𒁉𒋫​𒅗​𒅎𒈠​𒁺𒁍​𒉡𒌒𒋫𒅅𒆷​𒉌𒉈𒂠​𒀭𒌓​𒌓​𒉈𒀀​𒄯​𒃶𒂗𒈾𒉆𒈠𒀀𒀭 |


---
\* We are told this does not work on Firefox, though it works fine on Chrome, Edge, and even Internet Explorer.

### Typing transliterated Sumerian and Akkadian

Typing while the shift key is pressed types the letters directly without attempting to compose cuneiform signs.

| Keys | Output |
|---|---|
| `⇧a` | a |
| `⇧n` `⇧a` | na |
| `⇧s` `⇧a` `⇧n` `⇧t` `⇧a` `⇧k` `⇧4` | santak₄ |

While caps lock is on, all keys are typed directly, making it easier to type longer stretches of transliteration;
further pressing the shift key types capital letters (or other symbols; in particular the acute and grave accents and the
full stop are mapped to the shifted versions of `2`, `3`, and `-`; see below).

| Keys (caps lock on) | Output |
|---|---|
| `a` `-` `n` `a` `␣`  `⇧k` `⇧a` `⇧2` `⇧-` `⇧d` `⇧i` `⇧n` `⇧g` `⇧i` `⇧r` `⇧-` `⇧r` `⇧a` `⇧k` `⇧i`  | a-na KÁ.DINGIR.RA.KI |

The key `¹` (a shifted key in the default layouts; see below for its placement) has the special effect of making a following
`+`, `-`, `d`, `f`, or `m` superscript, and a following digit non-subscript; typing it twice yields an actual superscript 1:
| Keys (caps lock on) | Output |
|---|---|
| `d` `u` `n` `3` `¹` `+` | dun₃⁺ |
| `¹` `d` `¹` `3` `¹` `0` | ᵈ30 |
| `¹` `¹` `⇧a` `⇧n` `⇧-` `⇧š` `⇧a` `⇧2` `⇧r` `⇧-` `⇧d` `⇧u` `⇧3` `⇧-` `⇧a` | ¹AN.ŠÁR.DÙ.A |

### Layout

The letters that are not part of the basic latin alphabet may have been assigned various keys;
the otherwise unused letters `C`, `H`, `O`, `Y` have consistently been repurposed as `Š`, `Ḫ`, `Ś`, `Ŋ` respectively;
the placement of `Ṣ` and `Ṭ` is more haphazard. The table below shows the layouts offered by the installer.
<table>
<thead><tr><th>AZERTŊ</th><th>QWERTŊ</th><th>QWERTZ</th><th>ʾṢṬPŊF (Dvorak)</th></tr></thead>
<tbody><tr><td>
<pre>
⫶  1  2  3  4  5  6  7  8  9  0  ×  +
    a  z  e  r  t  ŋ  u  i  ś  p  ʾ  ṣ
     q  s  d  f  g  ḫ  j  k  l  m  ṭ  *
      w  x  š  v  b  n  /  -  :  !
</pre>
</td><td>
<pre>
⫶  1  2  3  4  5  6  7  8  9  0  -  +
    q  w  e  r  t  ŋ  u  i  ś  p  [  ]  \
     a  s  d  f  g  ḫ  j  k  l  :  ʾ
      z  x  š  v  b  n  m  ṣ  ṭ  /
</pre>
</td><td>
<pre>
̂   1  2  3  4  5  6  7  8  9  0  ʾ  ̄
    q  w  e  r  t  z  u  i  ś  p  ṭ  +
     a  s  d  f  g  ḫ  j  k  l  ṣ  ⫶  \
      ŋ  x  š  v  b  n  m  /  :  -
</pre>
</td><td>
<pre>
⫶  1  2  3  4  5  6  7  8  9  0  [  ]
    ʾ  ṣ  ṭ  p  ŋ  f  g  š  r  l  /  +  \
     a  ś  e  u  i  d  ḫ  t  n  s  -
      :  q  j  k  x  b  m  w  v  z
</pre>
</td></tr></tbody></table>
<table>
<thead><tr><th>AZERTŊ</th><th>QWERTŊ</th><th>QWERTZ</th><th>ʾṢṬPŊF (Dvorak)</th></tr></thead>
<tbody><tr><td>
<pre>
¹  ‹  ́   ̀   ›  (  «  ⸢  \  ⸣  »  )  =
    A  Z  E  R  T  Ŋ  U  I  Ś  P  ̂   Ṣ
     Q  S  D  F  G  Ḫ  J  K  L  M  Ṭ  ̄ 
      W  X  Š  V  B  N  ?  .  [  ]
</pre>
</td><td>
<pre>
¹  !  ́   ̀   «  »  ̂   ̄   *  (  )  .  =
    Q  W  E  R  T  Ŋ  U  I  Ś  P  ⸢  ⸣  ×
     A  S  D  F  G  Ḫ  J  K  L  ‹  ›
      Z  X  Š  V  B  N  M  Ṣ  Ṭ  ?
</pre>
</td><td>
<pre>
×  !  ́   ̀   «  »  [  ]  (  )  =  ?  ¹
    Q  W  E  R  T  Z  U  I  Ś  P  Ṭ  *
     A  S  D  F  G  Ḫ  J  K  L  Ṣ  ⸢  ⸣
      Ŋ  X  Š  V  B  N  M  ‹  ›  .
</pre>
</td><td>
<pre>
¹  !  ́   ̀   «  »  ̂   ̄   *  (  )  ⸢  ⸣
    ‹  Ṣ  Ṭ  P  Ŋ  F  G  Š  R  L  ?  =  ×
     A  Ś  E  U  I  D  Ḫ  T  N  S  .
      ›  Q  J  K  X  B  M  W  V  Z
</pre>
</td></tr></tbody></table>

The layout may be customized by editing the file `%APPDATA%\mockingbirdnest\Enmerkar\layout.txt` according to the instructions in that file.

### Entry by sign list number

Since version [𒀭𒌉𒍣](https://github.com/eggrobin/Enmerkar/releases/tag/%F0%92%80%AD%F0%92%8C%89%F0%92%8D%A3),
signs can also be entered by their sign list number, prefixed by the key `x` and the abbreviation for the sign list,
as illustrated in the following table for 𒂗.
| Keys | Sign list |
|---|---|
|`x` `l` `a` `k` `5` `3` `2` `␣` | René Labat, _Manuel d'épigraphie akkadienne_ |
|`x` `r` `s` `p` `2` `7` `1` `␣` | Yvonne Rosengarten, _Répertoire commenté des signes présargoniques sumériens de Lagash_ |
|`x` `b` `a` `u` `2` `9` `6` `␣` | Eric Burrows, _Archaic Texts_ |
|`x` `ḫ` `z` `l` `0` `4` `0` `␣` | Christel Rüster & Erich Neu, _Hethitisches Zeichenlexikon_ |
|`x` `m` `z` `l` `1` `6` `4` `␣` | Rykle Borger, _Mesopotamisches Zeichenlexikon_ |
|`x` `a` `b` `z` `l` `6` `2` `␣` | Catherine Mittermayer, _Altbabylonische Zeichenliste der sumerisch-literarische Texte_ |
|`x` `k` `w` `u` `7` `5` `␣` | Nikolaus Schneider, _Die Keilschriftzeichen der Wirtschaftsurkunden von Ur III_ |

This makes it possible to enter signs that have no known values, such as `x` `m` `z` `l` `4` `0` `␣` for 𒎄.
