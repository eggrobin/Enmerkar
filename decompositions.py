from collections import defaultdict
import re

import asl

signs_by_value : dict[str, list[asl.Sign]] = defaultdict(list)
for sign in asl.osl.signs:
    if isinstance(sign, asl.Sign):
        if sign.deprecated:
            continue
        for value in sign.values:
            if value.deprecated:
                continue
            if value.language:
                continue
            if value.text in signs_by_value and "ₓ" not in value.text:
                raise ValueError(f"Multiple signs with value {value.text}: {signs_by_value[value.text][0].names}, {sign.names}")
            signs_by_value[value.text].append(sign)

with open("decompositions.txt", "w", encoding="utf-8") as f:
    mapping: dict[str, list[list[str]]] = defaultdict(list)
    for name, forms in asl.osl.forms_by_name.items():
        xsux = [form.unicode_cuneiform.text
                for form in forms
                if form.unicode_cuneiform]
        if not xsux:
            continue
        if len(set(xsux)) > 1:
            raise ValueError(name, xsux)
        xsux = xsux[0]
        if 'X' in xsux or 'x' in xsux:
            continue
        if "|" not in name and "@" not in name:
            continue
        parts : list[str] = []
        for part in re.split(r"([|.×()&+%]|@(?:[cfgstv]|180)?)", name):
            for form in (asl.osl.forms_by_name.get(part) or
                         signs_by_value.get(part.lower()) or []):
                if form.unicode_cuneiform:
                    parts.append(form.unicode_cuneiform.text)
                    break
            else:
                parts.append(part)
        mapping[xsux].append(parts)
    for xsux, decompositions in mapping.items():
        if any(''.join(part
                        for part in parts
                        if part not in "|.+") != xsux
                for parts in decompositions):
            print(xsux, file=f)
            for parts in decompositions:
                print("  →", "".join(parts), file=f)