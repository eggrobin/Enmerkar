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


def xsux_sequence(name: str):
    sequence_parts : list[str] = []
    depth = 0
    start = 1
    for i, c in enumerate(name):
        if i == 0:
            continue
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
        elif depth == 0 and c == '.' or i == len(name) - 1:
            part_name = name[start:i]
            for form in (asl.osl.forms_by_name.get(part_name) or
                        asl.osl.forms_by_name.get(f"|{part_name}|") or
                            signs_by_value.get(part_name.lower()) or []):
                if form.unicode_cuneiform:
                    sequence_parts.append(form.unicode_cuneiform.text)
                    break
            else:
                sequence_parts = []
                break
            start = i + 1
    return sequence_parts


atomic_sequences: dict[str, str] = {}
for name, forms in asl.osl.forms_by_name.items():
    xsux = [form.unicode_cuneiform.text
            for form in forms
            if form.unicode_cuneiform]
    if not xsux:
        continue
    if len(set(xsux)) > 1:
        raise ValueError(name, xsux)
    xsux = xsux[0]
    if len(xsux) > 1:
        continue
    if 'X' in xsux or 'x' in xsux:
        continue
    if name[0] != "|" or name[-1] != "|":
        continue        
    sequence_parts = xsux_sequence(name)
    if sequence_parts:
        if xsux in atomic_sequences and atomic_sequences[xsux] != ''.join(sequence_parts):
            raise ValueError(f"Multiple decompositions {atomic_sequences[xsux]} != {sequence_parts} for {xsux}")
        atomic_sequences[xsux] = ''.join(sequence_parts)

for xsux, decomposition in atomic_sequences.items():
    if xsux != decomposition:
        print(f"+++ {xsux} is not {'.'.join(decomposition)}")
print(f"--- {len(atomic_sequences)} atomically encoded sequences")

atom_replacements = sorted(atomic_sequences.items(), key=lambda kv: -len(kv[1]))

sequence_mapping: dict[str, list[list[str]]] = defaultdict(list)
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
    if name[0] != "|" or name[-1] != "|":
        continue
    sequence_parts = xsux_sequence(name)
    for atom, sequence in atom_replacements:
        sequence_parts = list(''.join(sequence_parts).replace(sequence, atom))
    if sequence_parts:
        sequence_mapping[xsux].append(sequence_parts)
for xsux, decompositions in sequence_mapping.items():
    for decomposition in decompositions:
        if xsux != ''.join(decomposition) and len(xsux) != 1:
            print(f"*** {xsux} is not {'.'.join(decomposition)}")

with open("decompositions.txt", "w", encoding="utf-8") as f:
    mapping: dict[str, list[list[str]]] = defaultdict(list)
    sequence_mapping: dict[str, list[list[str]]] = defaultdict(list)
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