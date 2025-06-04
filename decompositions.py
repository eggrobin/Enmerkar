from collections import defaultdict
import re

import asl

with open("decompositions.txt", "w", encoding="utf-8") as f:
    mapping = defaultdict(list)
    for name, forms in asl.osl.forms_by_name.items():
        xsux = [form.unicode_cuneiform.text
                for form in forms
                if form.unicode_cuneiform]
        if not xsux:
            continue
        if len(set(xsux)) > 1:
            raise ValueError(name, xsux)
        xsux = xsux[0]
        if "|" not in name:
            continue
        parts : list[str] = []
        for part in re.split(r"([|.×()&])", name):
            for form in asl.osl.forms_by_name.get(part) or []:
                if form.unicode_cuneiform:
                    parts.append(form.unicode_cuneiform.text)
                    break
            else:
                parts.append(part)
        mapping[xsux].append(parts)
    for xsux, decompositions in mapping.items():

        if any(''.join(part
                        for part in parts
                        if part not in "|.×()&") != xsux
                for parts in decompositions):
            print(xsux, file=f)
            for parts in decompositions:
                print("  →", "".join(parts), file=f)