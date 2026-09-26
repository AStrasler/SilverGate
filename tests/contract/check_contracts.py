"""Development contract oracle, not a runtime importer or collection implementation."""
import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '.test-deps'))
sys.path.insert(0, str(ROOT / 'tools'))
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from build_contract_assets import canonical, digest, seal


class UnsupportedVersion(ValueError):
    pass


def unique_pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('DUPLICATE_PROPERTY')
        value[key] = item
    return value


def load(path):
    data = path.read_bytes()
    if len(data) > 50 * 1024 * 1024:
        raise ValueError('INPUT_LIMIT')
    result = json.loads(data.decode('utf-8'), object_pairs_hook=unique_pairs,
                        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('NON_JSON_NUMBER')))
    bounded(result)
    return result


def bounded(value, depth=0):
    if depth > 32:
        raise ValueError('DEPTH_LIMIT')
    if isinstance(value, str) and len(value.encode('utf-8')) > 1048576:
        raise ValueError('STRING_LIMIT')
    if isinstance(value, float):
        raise ValueError('INTEGER_ONLY_PROFILE')
    if isinstance(value, int) and not isinstance(value, bool) and abs(value) > 9007199254740991:
        raise ValueError('INTEGER_LIMIT')
    if isinstance(value, dict):
        for k, v in value.items():
            bounded(k, depth + 1)
            bounded(v, depth + 1)
    elif isinstance(value, list):
        for item in value:
            bounded(item, depth + 1)


SCHEMAS = {s['$id']: s for s in (load(p) for p in (ROOT / 'schemas').rglob('*.schema.json'))}
REGISTRY = Registry().with_resources((key, Resource.from_contents(s)) for key, s in SCHEMAS.items())


def validate_schema(name, value):
    if value.get('schemaVersion', '1.0.0') != '1.0.0':
        raise UnsupportedVersion('UNSUPPORTED_VERSION: no truth/integrity judgment')
    schema = SCHEMAS['https://silvergate.invalid/schemas/' + name + '/1.0.0.schema.json']
    Draft202012Validator(schema, registry=REGISTRY, format_checker=FormatChecker()).validate(value)


def pointer(value, path):
    if path == '':
        return value
    for segment in path[1:].split('/'):
        key = segment.replace('~1', '/').replace('~0', '~')
        if isinstance(value, list):
            if not key.isdigit() or (len(key) > 1 and key.startswith('0')):
                raise ValueError('INVALID_POINTER')
            value = value[int(key)]
        else:
            value = value[key]
    return value


def null_paths(value, path=''):
    if value is None:
        yield path
    elif isinstance(value, dict):
        for k, item in value.items():
            if k != 'fieldStates':
                yield from null_paths(item, path + '/' + k.replace('~', '~0').replace('/', '~1'))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            yield from null_paths(item, path + '/' + str(i))


def field_states(value):
    states = value['fieldStates']
    for path in null_paths(value):
        if path not in states:
            raise ValueError('UNEXPLAINED_NULL:' + path)
    for path in states:
        if pointer(value, path) is not None:
            raise ValueError('FIELD_STATE_FOR_KNOWN_VALUE')


def index_unique(items, field):
    result = {item[field]: item for item in items}
    if len(result) != len(items):
        raise ValueError('DUPLICATE_ID')
    return result


def ordered_time(start, end):
    if start is not None and end is not None and datetime.fromisoformat(start.replace('Z', '+00:00')) > datetime.fromisoformat(end.replace('Z', '+00:00')):
        raise ValueError('REVERSED_INTERVAL')


def validate_snapshot(snapshot):
    bounded(snapshot)
    if any(r.get('recordSchemaVersion') != '1.0.0' for r in snapshot.get('records', [])):
        raise UnsupportedVersion('UNSUPPORTED_RECORD_VERSION')
    validate_schema('evidence', snapshot)
    records = index_unique(snapshot['records'], 'recordId')
    sources = index_unique(snapshot['sources'], 'sourceId')
    runs = index_unique(snapshot['collectorRuns'], 'collectorRunId')
    field_states(snapshot['host'])
    for source in sources.values():
        field_states(source)
    ordered_time(snapshot['captureWindow']['startedAt'], snapshot['captureWindow']['endedAt'])
    for record in records.values():
        if record['sourceId'] not in sources or record['collectorRunId'] not in runs:
            raise ValueError('DANGLING_RECORD_REFERENCE')
        field_states(record)
        ordered_time(record['observedWindow']['start'], record['observedWindow']['end'])
        if snapshot['origin'] == 'historical_transcription' and record['recordType'] != 'historical_assertion':
            raise ValueError('HISTORICAL_NOT_RAW_QUERY')
        if record['recordType'] == 'historical_assertion' and sources[record['sourceId']]['kind'] != 'user_handoff':
            raise ValueError('HISTORICAL_SOURCE_MISMATCH')
        if record['recordType'] == 'firewall_rule':
            for target in record['payload']['filterRecordIds'] or []:
                if target not in records or records[target]['recordType'] != 'firewall_filter' or records[target]['payload']['ruleRecordId'] != record['recordId']:
                    raise ValueError('FILTER_ASSOCIATION_MISMATCH')
        if record['recordType'] == 'firewall_filter':
            target = record['payload']['ruleRecordId']
            if target not in records or records[target]['recordType'] != 'firewall_rule' or record['recordId'] not in (records[target]['payload']['filterRecordIds'] or []):
                raise ValueError('FILTER_ASSOCIATION_MISMATCH')
    for rid, run in runs.items():
        ordered_time(run['startedAt'], run['endedAt'])
        observed = {r['recordId'] for r in records.values() if r['collectorRunId'] == rid}
        if observed != set(run['records']) or len(run['records']) != len(observed):
            raise ValueError('RUN_RECORD_MISMATCH')
        if run['metrics']['recordCount'] != len(observed):
            raise ValueError('RECORD_COUNT_MISMATCH')
        if run['status'] == 'success' and not observed:
            raise ValueError('SUCCESS_WITHOUT_RECORDS')
        if run['status'] == 'empty' and observed:
            raise ValueError('EMPTY_WITH_RECORDS')
        if run['status'] in ('inaccessible', 'unsupported', 'failed', 'timed_out', 'cancelled', 'not_requested') and observed:
            raise ValueError('USE_PARTIAL_FOR_RETAINED_RECORDS')
        if run['status'] == 'partial' and run['coverage']['completeness'] != 'partial':
            raise ValueError('PARTIAL_COVERAGE_MISMATCH')
    expected = {rid: digest(record) for rid, record in records.items()}
    if expected != snapshot['integrity']['recordHashes']:
        raise ValueError('RECORD_INTEGRITY_MISMATCH')
    body = copy.deepcopy(snapshot)
    manifest_hash = body['integrity'].pop('manifestHash')
    if digest(body) != manifest_hash:
        raise ValueError('MANIFEST_INTEGRITY_MISMATCH')
    return records


def validate_derived_refs(document, snapshot):
    records = validate_snapshot(snapshot)
    def walk(value):
        if isinstance(value, dict):
            for reference in value.get('evidenceRefs', []):
                if reference['snapshotId'] != snapshot['snapshotId'] or reference['recordId'] not in records:
                    raise ValueError('DANGLING_EVIDENCE_REFERENCE')
                pointer(records[reference['recordId']], reference['jsonPointer'])
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(document)


class SchemaTests(unittest.TestCase):
    def test_all_schemas_are_valid_draft_2020_12(self):
        self.assertGreaterEqual(len(SCHEMAS), 22)
        for schema in SCHEMAS.values():
            Draft202012Validator.check_schema(schema)

    def test_all_references_resolve_locally(self):
        def walk(value):
            if isinstance(value, dict):
                if '$ref' in value:
                    uri, _, fragment = value['$ref'].partition('#')
                    self.assertIn(uri, SCHEMAS)
                    if fragment:
                        pointer(SCHEMAS[uri], fragment)
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)
        for schema in SCHEMAS.values():
            walk(schema)

    def test_six_historical_fixtures_and_expectations(self):
        paths = list((ROOT / 'tests/fixtures/aaronaura-historical').glob('*.snapshot.json'))
        self.assertEqual(6, len(paths))
        for path in paths:
            snapshot = load(path)
            records = validate_snapshot(snapshot)
            expected = load(path.with_name(path.name.replace('.snapshot', '.expected')))
            validate_schema('fixture-expectations', expected)
            self.assertEqual(snapshot['snapshotId'], expected['snapshotId'])
            self.assertEqual('historical_transcription', snapshot['origin'])
            for claim in expected['requiredClaims']:
                self.assertTrue(claim['supportRecordIds'])
                self.assertTrue(set(claim['supportRecordIds']) <= records.keys())
            self.assertTrue(expected['negativeVariants'])


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = load(ROOT / 'tests/fixtures/synthetic/basic.snapshot.json')

    def test_synthetic_snapshot_is_valid(self):
        validate_snapshot(self.snapshot)

    def test_unknown_version_is_compatibility_not_corruption(self):
        self.snapshot['schemaVersion'] = '99.0.0'
        with self.assertRaises(UnsupportedVersion):
            validate_snapshot(self.snapshot)

    def test_tampered_record_is_rejected(self):
        self.snapshot['records'][0]['payload']['pid'] = 101
        with self.assertRaisesRegex(ValueError, 'INTEGRITY'):
            validate_snapshot(self.snapshot)

    def test_tampered_manifest_is_rejected(self):
        self.snapshot['producer']['version'] = '0.9.0'
        with self.assertRaisesRegex(ValueError, 'MANIFEST_INTEGRITY'):
            validate_snapshot(self.snapshot)

    def test_resigned_content_is_not_authentication(self):
        self.snapshot['producer']['name'] = 'Unverified third party'
        validate_snapshot(seal(self.snapshot))  # Only consistency, never publisher authenticity.

    def test_duplicate_ids_are_rejected(self):
        self.snapshot['records'][1]['recordId'] = 'record-1'
        with self.assertRaisesRegex(ValueError, 'DUPLICATE_ID'):
            validate_snapshot(seal(self.snapshot))

    def test_dangling_source_is_rejected(self):
        self.snapshot['records'][0]['sourceId'] = 'missing'
        with self.assertRaisesRegex(ValueError, 'DANGLING'):
            validate_snapshot(seal(self.snapshot))

    def test_null_without_state_is_rejected(self):
        self.snapshot['records'][0]['fieldStates'].pop('/payload/creationTime')
        with self.assertRaisesRegex(ValueError, 'UNEXPLAINED_NULL'):
            validate_snapshot(seal(self.snapshot))

    def test_false_unknown_state_is_rejected(self):
        self.snapshot['records'][0]['fieldStates']['/payload/pid'] = {'state': 'unknown', 'reasonCode': 'TEST'}
        with self.assertRaisesRegex(ValueError, 'FIELD_STATE_FOR_KNOWN_VALUE'):
            validate_snapshot(seal(self.snapshot))

    def test_partial_is_not_empty(self):
        self.snapshot['collectorRuns'][0]['status'] = 'empty'
        with self.assertRaisesRegex(ValueError, 'EMPTY_WITH_RECORDS'):
            validate_snapshot(seal(self.snapshot))

    def test_unknown_properties_are_rejected(self):
        self.snapshot['executeThis'] = 'Set-NetFirewallRule'
        with self.assertRaises(Exception):
            validate_snapshot(seal(self.snapshot))

    def test_hostile_strings_remain_data(self):
        records = validate_snapshot(self.snapshot)
        self.assertIn('<script>', records['record-1']['payload']['imagePath'])

    def test_invalid_port_is_rejected(self):
        self.snapshot['records'][1]['payload']['localPort'] = 65536
        with self.assertRaises(Exception):
            validate_snapshot(seal(self.snapshot))

    def test_udp_cannot_manufacture_remote_peer(self):
        self.snapshot['records'][2]['payload']['remoteAddress'] = '192.0.2.8'
        with self.assertRaises(Exception):
            validate_snapshot(seal(self.snapshot))

    def test_unsupported_platform_does_not_invalidate_evidence(self):
        self.snapshot['host']['platform']['osFamily'] = 'Unsupported test platform'
        self.snapshot['host']['fieldStates'].pop('/platform/osFamily')
        validate_snapshot(seal(self.snapshot))

    def test_broken_filter_association_is_rejected(self):
        self.snapshot['records'][4]['payload']['ruleRecordId'] = 'record-1'
        with self.assertRaisesRegex(ValueError, 'FILTER_ASSOCIATION'):
            validate_snapshot(seal(self.snapshot))

    def test_reversed_capture_interval_is_rejected(self):
        self.snapshot['captureWindow']['endedAt'] = '2020-01-01T00:00:00Z'
        with self.assertRaisesRegex(ValueError, 'REVERSED_INTERVAL'):
            validate_snapshot(seal(self.snapshot))

    def test_reference_resolves_and_missing_pointer_fails(self):
        doc = {'evidenceRefs': [{'snapshotId': self.snapshot['snapshotId'], 'recordId': 'record-1', 'jsonPointer': '/payload/pid'}]}
        validate_derived_refs(doc, self.snapshot)
        doc['evidenceRefs'][0]['jsonPointer'] = '/payload/missing'
        with self.assertRaises(KeyError):
            validate_derived_refs(doc, self.snapshot)


class CanonicalTests(unittest.TestCase):
    def test_invalid_unicode_is_rejected(self):
        with self.assertRaises(UnicodeEncodeError):
            bounded('\ud800')

    def test_canonical_fixed_vector(self):
        self.assertEqual(b'{"a":"\\u00e9","z":[true,null,3]}', canonical({'z': [True, None, 3], 'a': '\u00e9'}))

    def test_key_order_does_not_change_digest(self):
        self.assertEqual(digest({'b': 2, 'a': 1}), digest({'a': 1, 'b': 2}))

    def test_duplicate_json_properties_fail(self):
        with self.assertRaisesRegex(ValueError, 'DUPLICATE_PROPERTY'):
            json.loads('{"a":1,"a":2}', object_pairs_hook=unique_pairs)

    def test_depth_limit(self):
        item = None
        for _ in range(34):
            item = [item]
        with self.assertRaisesRegex(ValueError, 'DEPTH_LIMIT'):
            bounded(item)

    def test_string_and_number_limits(self):
        for value in ('x' * 1048577, 9007199254740992, 1.2):
            with self.assertRaises(ValueError):
                bounded(value)


class DerivedTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = load(ROOT / 'tests/fixtures/synthetic/basic.snapshot.json')
        self.claims = load(ROOT / 'tests/fixtures/synthetic/basic.claims.json')

    def test_all_derived_envelopes_and_refs(self):
        for name in ('normalized', 'claims', 'findings'):
            doc = load(ROOT / ('tests/fixtures/synthetic/basic.' + name + '.json'))
            validate_schema(name, doc)
            validate_derived_refs(doc, self.snapshot)

    def test_unknown_requires_reason_and_no_strength(self):
        claim = self.claims['claims'][0]
        claim['epistemicStatus'] = 'unknown'
        with self.assertRaises(Exception):
            validate_schema('claims', self.claims)
        claim['strength'] = None
        claim['unknownReason'] = 'Missing corroborating source'
        validate_schema('claims', self.claims)

    def test_foreign_snapshot_reference_is_rejected(self):
        self.claims['claims'][0]['evidenceRefs'][0]['snapshotId'] = '00000000-0000-4000-8000-999999999999'
        with self.assertRaisesRegex(ValueError, 'DANGLING_EVIDENCE'):
            validate_derived_refs(self.claims, self.snapshot)

    def test_spotify_scope_comparison_has_both_evidence_sides(self):
        expected = load(ROOT / 'tests/fixtures/aaronaura-historical/spotify.expected.json')
        claim = next(c for c in expected['requiredClaims'] if c['predicate'] == 'permission_scope_exceeds_observed_endpoints')
        self.assertEqual(['record-1', 'record-2'], claim['supportRecordIds'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
