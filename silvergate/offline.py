"""Deterministic offline analysis pipeline. No collectors or network access."""
import json
from pathlib import Path

from silvergate.importer import load, validate_snapshot, validate_schema, validate_derived_refs
from silvergate.normalizer import normalize
from silvergate.predicates import claim_set
from silvergate.explanation import explain

ROOT = Path(__file__).resolve().parents[1]


def analyze(path):
    snapshot = load(Path(path))
    records = validate_snapshot(snapshot)
    if snapshot['origin'] != 'synthetic' or len(snapshot['collectorRuns']) != 1:
        raise ValueError('UNSUPPORTED_ANALYSIS_SCOPE')
    normalized = normalize(snapshot)
    claims = claim_set(normalized, snapshot)
    findings = explain(claims, normalized, snapshot)
    for name, document in (('normalized', normalized), ('claims', claims),
                           ('findings', findings)):
        validate_schema(name, document)
        validate_derived_refs(document, snapshot, records)
    return normalized, claims, findings


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        raise SystemExit('usage: python -m silvergate.offline SNAPSHOT OUTPUT_DIRECTORY')
    output = Path(sys.argv[2])
    output.mkdir(parents=True, exist_ok=True)
    for name, document in zip(('normalized', 'claims', 'findings'), analyze(sys.argv[1])):
        (output / f'{name}.json').write_text(json.dumps(document, indent=2) + '\n',
                                              encoding='utf-8')
