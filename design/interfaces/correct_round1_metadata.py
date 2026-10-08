#!/usr/bin/env python3
"""Finalize/check only the nine newly authored Phase-1 instance records and R2.

Run after replaying charging.ops.json or rear_interface.ops.json. Default is
read-only verification; --apply performs scoped, idempotent metadata changes.
No placement, pin, wire, UUID, reference or inherited instance edits are allowed.
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN_PATH = '/063f9d99-6c07-44cf-ba32-e33897e06972/13f98b5d-2735-4ce5-b6a9-56134247b933'
REAR_PATH = '/e9412e56-0f4f-4ec5-ad89-3d7d6481d433'
QUALIFICATION = (
    'Recommended normal VBUS 4.0-5.5V; absolute stress limits -0.3..22V. '
    'Positive transient overshoot shall remain below 22V and negative transient/reverse '
    'protection shall keep PMIC VBUS at or above -0.3V with design margin. '
    'Sustained reverse voltage requires series blocking; final clamps and series '
    'protection remain TBD against qualified dock/fault envelope; TVS standoff above dock maximum.'
)
TARGETS = {
    '12_CHARGING.kicad_sch': ('sportwatch_revA', MAIN_PATH,
                             {'J202', 'U1201', 'D1201', '#FLG1201'}),
    'rear_sensor/rear_sensor_revA.kicad_sch': ('rear_sensor_revA', REAR_PATH,
                                            {'J1502', 'C1501', '#FLG1501', '#FLG1502', '#FLG1503'}),
}
TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+')


def child_spans(text):
    """Direct children of one expression, ignoring parentheses inside strings."""
    depth, start = 0, None
    for token in TOKEN.finditer(text):
        if token.group() == '(':
            if depth == 1:
                start = token.start()
            depth += 1
        elif token.group() == ')':
            depth -= 1
            if depth == 1 and start is not None:
                yield start, token.end(), text[start:token.end()]
                start = None
    assert depth == 0, 'Unbalanced schematic expression'


def normalized(text):
    return [t.group() for t in TOKEN.finditer(text)]


def prepare(file, project, path, refs):
    original = (ROOT / file).read_text()
    replacements, proofs, seen = [], [], set()
    for start, end, block in child_spans(original):
        if not re.match(r'\(symbol\s+\(lib_id\b', block):
            continue
        matches = re.findall(r'\(property\s+"Reference"\s+"([^"]+)"', block)
        assert len(matches) == 1, 'Ambiguous Reference field'
        ref = matches[0]
        if ref not in refs:
            continue
        assert ref not in seen, f'Duplicate targeted reference: {ref}'
        seen.add(ref)
        instances = [(a, b, v) for a, b, v in child_spans(block) if v.startswith('(instances')]
        assert len(instances) == 1, f'Expected one instance block: {ref}'
        a, b, inst = instances[0]
        assert len(re.findall(r'\(project\b', inst)) == len(re.findall(r'\(path\b', inst)) == 1
        assert re.findall(r'\(reference\s+"([^"]+)"', inst) == [ref]
        assert re.findall(r'\(unit\s+(\d+)\)', inst) == ['1']
        old_project = re.search(r'\(project\s+"([^"]+)"', inst).group(1)
        old_path = re.search(r'\(path\s+"([^"]+)"', inst).group(1)
        allowed_path = '/ae197026-a6bd-44b2-96e3-f21bc4bb9255' if file.startswith('12_') else path
        assert old_project in {'noname', project} and old_path in {allowed_path, path}, (ref, old_project, old_path)
        desired = f'(instances (project "{project}" (path "{path}" (reference "{ref}") (unit 1))))'
        revised = block[:a] + desired + block[b:]
        if ref == 'D1201':
            pattern = r'(\(property\s+"Qualification"\s+)"(?:\\.|[^"\\])*"'
            revised, count = re.subn(pattern, lambda m: m.group(1) + json.dumps(QUALIFICATION), revised)
            assert count == 1
        replacements.append((start, end, revised))
        proofs.append({'reference': ref, 'project': project, 'path': path,
                       'placed_uuid': re.search(r'\(uuid\s+"([^"]+)"', block).group(1),
                       'single_saved_instance': True, 'correct_before': normalized(block) == normalized(revised)})
    assert seen == refs, (file, 'Missing targeted references', refs - seen)
    revised = original
    for start, end, block in reversed(replacements):
        revised = revised[:start] + block + revised[end:]
    return original, revised, proofs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    # Stage and validate both files before changing either; never reannotate.
    prepared = {f: prepare(f, *settings) for f, settings in TARGETS.items()}
    changes = [f for f, (old, new, proof) in prepared.items() if old != new]
    if args.apply:
        for f in changes:
            (ROOT / f).write_text(prepared[f][1])
    else:
        assert not changes, f'Uncorrected metadata: {changes}; run --apply after authoring replay'
    print(json.dumps({'status': 'PASS', 'mode': 'apply' if args.apply else 'check',
                      'files_changed': changes,
                      'instances': [p for old, new, ps in prepared.values() for p in ps],
                      'qualification': QUALIFICATION}, indent=2))


if __name__ == '__main__':
    main()
