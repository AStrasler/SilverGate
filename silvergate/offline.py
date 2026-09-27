"""Deterministic, offline Step 2a slice for the synthetic image-path predicate.

The Python runtime importer validates input independently of the test oracle.
No collectors or machine queries are invoked.
"""
import copy
import json
from pathlib import Path

from silvergate.importer import load, validate_snapshot, validate_schema, validate_derived_refs

ROOT = Path(__file__).resolve().parents[1]

VERSION = 'fixture-only'
ANALYSIS_ID = 'synthetic-analysis'
LIMITATION = 'Synthetic example only; observation time is unknown.'


def evidence_ref(snapshot, record):
    return {'snapshotId': snapshot['snapshotId'], 'recordId': record['recordId'],
            'jsonPointer': '/payload/imagePath'}


def normalize(snapshot):
    """Map observed process image paths to application entities, in record order."""
    entities = []
    for record in snapshot['records']:
        if record['recordType'] != 'process':
            continue
        path = record['payload']['imagePath']
        if path is None:
            continue
        entities.append({
            'entityId': f'app-{len(entities) + 1}', 'entityType': 'Application',
            'attributes': [{'name': 'originalPath', 'value': path}],
            'evidenceRefs': [evidence_ref(snapshot, record)],
            'fieldStates': {}, 'actor': {'kind': 'application', 'identityRefs': []},
        })
    return {
        'schemaVersion': '1.0.0', 'analysisId': ANALYSIS_ID,
        'inputSnapshotIds': [snapshot['snapshotId']],
        'inputHashes': [snapshot['integrity']['manifestHash']],
        'engineVersion': VERSION, 'rulesetVersion': VERSION,
        'normalizerVersion': VERSION, 'semanticConfiguration': {},
        'entities': entities, 'relationships': [],
        'coverage': copy.deepcopy(snapshot['collectorRuns'][0]['coverage']),
    }


def image_path_claim(entity, snapshot, ordinal):
    """Registry entry: a reported process image path supports a direct fact."""
    return {
        'claimId': f'claim-{ordinal}', 'subjectIds': [entity['entityId']],
        'predicate': 'synthetic_image_path', 'epistemicStatus': 'fact',
        'strength': 'direct', 'value': {'dimension': 'imagePath', 'comparison': 'reported'},
        'evidenceRefs': copy.deepcopy(entity['evidenceRefs']), 'premiseClaimIds': [],
        'ruleId': VERSION,
        'scope': {'snapshotIds': [snapshot['snapshotId']], 'observationWindow': None},
        'limitations': [LIMITATION], 'unknownReason': None, 'templateId': VERSION,
    }


PREDICATES = {'synthetic_image_path': image_path_claim}


def claim_set(normalized, snapshot):
    claims = [PREDICATES['synthetic_image_path'](entity, snapshot, i)
              for i, entity in enumerate(normalized['entities'], 1)
              if entity['entityType'] == 'Application'
              and any(a['name'] == 'originalPath' and a['value'] is not None
                      for a in entity['attributes'])]
    return {'schemaVersion': '1.0.0', 'analysisId': normalized['analysisId'],
            'claims': claims}


def explain(claims, normalized, snapshot):
    findings = []
    for i, claim in enumerate(claims['claims'], 1):
        if claim['predicate'] not in PREDICATES:
            raise ValueError('UNSUPPORTED_PREDICATE')
        findings.append({
            'subjectIds': copy.deepcopy(claim['subjectIds']),
            'predicate': claim['predicate'], 'epistemicStatus': claim['epistemicStatus'],
            'value': copy.deepcopy(claim['value']),
            'evidenceRefs': copy.deepcopy(claim['evidenceRefs']),
            'limitations': copy.deepcopy(claim['limitations']),
            'findingId': f'finding-{i}',
            'observationWindow': copy.deepcopy(claim['scope']['observationWindow']),
            'explanation': 'Synthetic fixture reports an image path; no live observation.',
        })
    return {
        'schemaVersion': '1.0.0', 'exportId': 'export-1', 'producer': VERSION,
        'inputSnapshots': [{'snapshotId': snapshot['snapshotId'],
                            'hash': snapshot['integrity']['manifestHash'],
                            'origin': snapshot['origin']}],
        'analysisVersion': VERSION, 'hostScopeId': snapshot['host']['scopeId'],
        'findings': findings, 'coverage': copy.deepcopy(normalized['coverage']),
        'privacy': copy.deepcopy(snapshot['privacy']),
    }


def analyze(path):
    snapshot = load(Path(path))
    validate_snapshot(snapshot)
    if snapshot['origin'] != 'synthetic' or len(snapshot['collectorRuns']) != 1:
        raise ValueError('UNSUPPORTED_ANALYSIS_SCOPE')
    normalized = normalize(snapshot)
    claims = claim_set(normalized, snapshot)
    findings = explain(claims, normalized, snapshot)
    for name, document in (('normalized', normalized), ('claims', claims),
                           ('findings', findings)):
        validate_schema(name, document)
        validate_derived_refs(document, snapshot)
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
