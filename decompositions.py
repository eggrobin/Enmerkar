import asl
import re

with open("decompositions.txt", "w", encoding="utf-8") as f:
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
        if ''.join(part for part in parts if part not in "|.×()&") != xsux:
            print(xsux, file=f)
            print("  →", "".join(parts), file=f)