"""Finding export: preserve claim status, meaning and exact evidence refs."""
import copy

from silvergate.normalizer import VERSION
from silvergate.predicates import PREDICATES

EXPLANATIONS = {
    'synthetic_image_path': 'Synthetic fixture reports an image path; no live observation.',
    'observed_local_endpoint': 'Structured snapshot reports a local endpoint.',
    'reported_firewall_rule': 'Structured snapshot reports a firewall rule.',
    'candidate_permission_for_listener': 'Rule and TCP listener share an explicit port; applicability remains unconfirmed.',
}


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
            'explanation': EXPLANATIONS[claim['predicate']],
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
