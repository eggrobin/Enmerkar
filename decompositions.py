from collections import defaultdict
import re

import asl

with open("decompositions.txt", "w", encoding="utf-8") as f:
    mapping: dict[str, list[list[str]]] = defaultdict(list)
    sequence_mapping: dict[str, list[list[str]]] = defaultdict(list)
    for forms in asl.osl.forms_by_name.values():
        for form in forms:
            if not form.unicode_cuneiform:
                continue
            xsux = form.unicode_cuneiform.text
            xsux = xsux[0]
            if 'X' in xsux or 'x' in xsux:
                continue
            decompositions_by_name : dict[str, list[str]] = {}
            for name in form.names:
                if "|" not in name and "@" not in name:
                    continue
                parts : list[str] = []
                for part in re.split(r"([|.×()&+%]|@(?:[cfgstv]|180)?)", name):
                    for part_form in (asl.osl.forms_by_name.get(part) or
                                      asl.signs_by_value.get(part.lower()) or
                                      asl.forms_by_list_number.get(part) or
                                      []):
                        if part_form.unicode_cuneiform:
                            parts.append(part_form.unicode_cuneiform.text)
                            break
                    else:
                        parts.append(part)
                decompositions_by_name[name] = parts
            if not decompositions_by_name:
                continue
            base_name_operators = ([part for part in decompositions_by_name[form.names[0]]
                                         if all(ord(c) <= 0x7F for c in part)]
                                   if form.names[0] in decompositions_by_name else [])
            for name, decomposition in decompositions_by_name.items():
                operators = [part for part in decomposition if all(ord(c) <= 0x7F for c in part)]
                if len(operators) > len(base_name_operators):
                    print(f"Alternate name {name} is more decomposed than {form.names[0]}")
                    mapping[xsux].append(decomposition)
    for xsux, decompositions in mapping.items():
        if any(''.join(part
                        for part in parts
                        if part not in "|.+") != xsux
                for parts in decompositions):
            print(xsux, file=f)
            for parts in decompositions:
                print("  →", "".join(parts), file=f)