"""Evidence-to-entity mapping for the first structured correlation rule suite."""
import copy

VERSION = 'fixture-only'
ANALYSIS_ID = 'synthetic-analysis'


def ref(snapshot, record, pointer):
    return {'snapshotId': snapshot['snapshotId'], 'recordId': record['recordId'],
            'jsonPointer': pointer}


def _ports(filter_record):
    conditions = filter_record['payload']['conditions'] or []
    ports = [v for c in conditions if c['name'] == 'LocalPort' for v in c['values']
             if v.isascii() and v.isdigit() and 0 <= int(v) <= 65535]
    protocols = [v for c in conditions if c['name'] == 'Protocol' for v in c['values']]
    return set(ports) if 'TCP' in protocols else set()


def normalize(snapshot):
    records = snapshot['records']
    # The extended rule suite is applicable only when an explicit TCP port
    # condition exists. The original Any-port fixture retains its exact output.
    structured = any(r['recordType'] == 'firewall_filter' and _ports(r) for r in records)
    entities = []
    relationships = []
    process_entities = {}
    for record in records:
        kind, payload = record['recordType'], record['payload']
        if kind == 'process' and payload['imagePath'] is not None:
            entity_id = f'app-{len(process_entities) + 1}'
            process_entities[record['recordId']] = entity_id
            entities.append({'entityId': entity_id,
                             'entityType': 'Application',
                             'attributes': [{'name': 'originalPath', 'value': payload['imagePath']}],
                             'evidenceRefs': [ref(snapshot, record, '/payload/imagePath')],
                             'fieldStates': {},
                             'actor': {'kind': 'application', 'identityRefs': []}})
        elif structured and kind in ('tcp_connection', 'udp_endpoint'):
            pointers = ['/payload/localAddress', '/payload/localPort', '/payload/owningProcess']
            if kind == 'tcp_connection':
                pointers.append('/payload/state')
            entities.append({'entityId': 'socket-' + record['recordId'],
                             'entityType': 'SocketObservation',
                             'attributes': [{'name': 'protocol', 'value': 'TCP' if kind == 'tcp_connection' else 'UDP'},
                                            {'name': 'localPort', 'value': str(payload['localPort'])}],
                             'evidenceRefs': [ref(snapshot, record, p) for p in pointers],
                             'fieldStates': {}})
        elif structured and kind == 'firewall_rule':
            entities.append({'entityId': 'permission-' + record['recordId'],
                             'entityType': 'FirewallPermission',
                             'attributes': [{'name': 'name', 'value': payload['name']}],
                             'evidenceRefs': [ref(snapshot, record, '/payload/name')],
                             'fieldStates': {}})
    if structured:
        by_type = lambda typ: [r for r in records if r['recordType'] == typ]
        for process in by_type('process'):
            if process['recordId'] not in process_entities:
                continue
            for socket in by_type('tcp_connection') + by_type('udp_endpoint'):
                if process['payload']['pid'] != socket['payload']['owningProcess']:
                    continue
                if process['payload']['creationTime'] is None or socket['payload']['creationTime'] is None:
                    limitation = ['PID matches, but creation time is unavailable; process identity is not confirmed.']
                else:
                    limitation = ['PID matches; process lifetime overlap is not independently established.']
                relationships.append({'relationshipId': 'owns-' + process['recordId'] + '-' + socket['recordId'],
                                      'type': 'owns_endpoint', 'from': process_entities[process['recordId']],
                                      'to': 'socket-' + socket['recordId'],
                                      'epistemicStatus': 'inference', 'strength': 'heuristic',
                                      'evidenceRefs': [ref(snapshot, process, '/payload/pid'),
                                                       ref(snapshot, socket, '/payload/owningProcess')],
                                      'limitations': limitation})
        for rule in by_type('firewall_rule'):
            if rule['payload']['enabled'] is not True or rule['payload']['action'] != 'Allow' or rule['payload']['direction'] != 'Inbound':
                continue
            for filter_record in by_type('firewall_filter'):
                if filter_record['payload']['ruleRecordId'] != rule['recordId']:
                    continue
                for socket in by_type('tcp_connection'):
                    if (socket['payload']['state'] != 'Listen' or
                            str(socket['payload']['localPort']) not in _ports(filter_record)):
                        continue
                    relationships.append({'relationshipId': 'candidate-' + rule['recordId'] + '-' + socket['recordId'],
                                          'type': 'candidate_permission_for',
                                          'from': 'permission-' + rule['recordId'],
                                          'to': 'socket-' + socket['recordId'],
                                          'epistemicStatus': 'inference', 'strength': 'heuristic',
                                          'evidenceRefs': [ref(snapshot, rule, '/payload/enabled'),
                                                           ref(snapshot, rule, '/payload/action'),
                                                           ref(snapshot, rule, '/payload/direction'),
                                                           ref(snapshot, filter_record, '/payload/ruleRecordId'),
                                                           ref(snapshot, filter_record, '/payload/conditions'),
                                                           ref(snapshot, socket, '/payload/localPort'),
                                                           ref(snapshot, socket, '/payload/state')],
                                          'limitations': ['Matching TCP port and rule do not establish program binding, network profile applicability, or actual traffic.']})
    return {'schemaVersion': '1.0.0', 'analysisId': ANALYSIS_ID,
            'inputSnapshotIds': [snapshot['snapshotId']],
            'inputHashes': [snapshot['integrity']['manifestHash']],
            'engineVersion': VERSION, 'rulesetVersion': VERSION,
            'normalizerVersion': VERSION, 'semanticConfiguration': {},
            'entities': entities, 'relationships': relationships,
            'coverage': copy.deepcopy(snapshot['collectorRuns'][0]['coverage'])}
