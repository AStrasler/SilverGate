"""Small explicit predicate registry; no fixture prose or answer keys are read."""
import copy

from silvergate.normalizer import VERSION

LIMITATION = 'Synthetic example only; observation time is unknown.'


def _claim(snapshot, ordinal, subjects, predicate, status, strength, dimension,
           comparison, references, limitations):
    return {'claimId': f'claim-{ordinal}', 'subjectIds': subjects,
            'predicate': predicate, 'epistemicStatus': status, 'strength': strength,
            'value': {'dimension': dimension, 'comparison': comparison},
            'evidenceRefs': copy.deepcopy(references), 'premiseClaimIds': [],
            'ruleId': VERSION if predicate == 'synthetic_image_path' else predicate + '-v1',
            'scope': {'snapshotIds': [snapshot['snapshotId']], 'observationWindow': None},
            'limitations': limitations, 'unknownReason': None,
            'templateId': VERSION if predicate == 'synthetic_image_path' else predicate + '-v1'}


def image_path(entity, snapshot, ordinal):
    return _claim(snapshot, ordinal, [entity['entityId']], 'synthetic_image_path',
                  'fact', 'direct', 'imagePath', 'reported', entity['evidenceRefs'],
                  [LIMITATION])


def socket_observation(entity, snapshot, ordinal):
    attributes = {a['name']: a['value'] for a in entity['attributes']}
    protocol = attributes['protocol']
    return _claim(snapshot, ordinal, [entity['entityId']], 'observed_local_endpoint',
                  'fact', 'direct', 'localEndpoint', protocol + ':' + attributes['localPort'],
                  entity['evidenceRefs'], ['Socket observation does not establish a remote peer or traffic.'])


def firewall_rule(entity, snapshot, ordinal):
    return _claim(snapshot, ordinal, [entity['entityId']], 'reported_firewall_rule',
                  'fact', 'direct', 'firewallRule', 'reported', entity['evidenceRefs'],
                  ['Rule name alone does not establish effective permission.'])


def candidate_permission(relationship, snapshot, ordinal):
    return _claim(snapshot, ordinal, [relationship['from'], relationship['to']],
                  'candidate_permission_for_listener', 'inference', 'heuristic',
                  'tcpPortMatch', 'candidate', relationship['evidenceRefs'],
                  copy.deepcopy(relationship['limitations']))


PREDICATES = {'synthetic_image_path': image_path,
              'observed_local_endpoint': socket_observation,
              'reported_firewall_rule': firewall_rule,
              'candidate_permission_for_listener': candidate_permission}


def claim_set(normalized, snapshot):
    claims = []
    for entity in normalized['entities']:
        kind = entity['entityType']
        if kind == 'Application':
            claims.append(image_path(entity, snapshot, len(claims) + 1))
        elif kind == 'SocketObservation':
            claims.append(socket_observation(entity, snapshot, len(claims) + 1))
        elif kind == 'FirewallPermission':
            claims.append(firewall_rule(entity, snapshot, len(claims) + 1))
    for relationship in normalized['relationships']:
        if relationship['type'] == 'candidate_permission_for':
            candidate = candidate_permission(relationship, snapshot, len(claims) + 1)
            candidate['premiseClaimIds'] = [claim['claimId'] for claim in claims
                                            if claim['subjectIds'] == [relationship['from']]
                                            or claim['subjectIds'] == [relationship['to']]]
            claims.append(candidate)
    return {'schemaVersion': '1.0.0', 'analysisId': normalized['analysisId'],
            'claims': claims}
