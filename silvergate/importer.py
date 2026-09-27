"""Bounded offline JSON importer for the current Python analysis prototype.

This module never imports the development contract oracle. Hashes establish
internal consistency, not authenticity of the producer or source evidence.
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
VERSION = '1.0.0'
BASE = 'https://silvergate.invalid/schemas/'
MAX_BYTES = 50 * 1024 * 1024
MAX_DEPTH = 32
MAX_STRING_BYTES = 1048576
MAX_INTEGER = 9007199254740991


class UnsupportedVersion(ValueError):
    """Compatible evidence may require a newer importer; integrity is unknown."""


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('DUPLICATE_PROPERTY')
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError('NON_JSON_NUMBER')


def _bounded(value, depth=0):
    if depth > MAX_DEPTH:
        raise ValueError('DEPTH_LIMIT')
    if isinstance(value, str) and len(value.encode('utf-8')) > MAX_STRING_BYTES:
        raise ValueError('STRING_LIMIT')
    if isinstance(value, float):
        raise ValueError('INTEGER_ONLY_PROFILE')
    if isinstance(value, int) and not isinstance(value, bool) and abs(value) > MAX_INTEGER:
        raise ValueError('INTEGER_LIMIT')
    if isinstance(value, dict):
        for key, item in value.items():
            _bounded(key, depth + 1)
            _bounded(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            _bounded(item, depth + 1)


def load(path):
    path = Path(path)
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('INPUT_LIMIT')
    with path.open('rb') as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError('INPUT_LIMIT')
    value = json.loads(data.decode('utf-8'), object_pairs_hook=_unique,
                       parse_constant=_reject_constant)
    _bounded(value)
    return value


def _schemas():
    schemas = {}
    for path in (ROOT / 'schemas').rglob('*.schema.json'):
        schema = load(path)
        schemas[schema['$id']] = schema
    registry = Registry().with_resources(
        (uri, Resource.from_contents(schema)) for uri, schema in schemas.items())
    return schemas, registry


SCHEMAS, REGISTRY = _schemas()


def validate_schema(name, document):
    if not isinstance(document, dict) or document.get('schemaVersion') != VERSION:
        raise UnsupportedVersion('UNSUPPORTED_VERSION: no integrity judgment')
    schema = SCHEMAS[BASE + name + '/' + VERSION + '.schema.json']
    Draft202012Validator(schema, registry=REGISTRY,
                         format_checker=FormatChecker()).validate(document)


def _digest(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(',', ':'), allow_nan=False).encode('ascii')
    return hashlib.sha256(encoded).hexdigest()


def _index(items, key):
    indexed = {}
    for item in items:
        if item[key] in indexed:
            raise ValueError('DUPLICATE_ID')
        indexed[item[key]] = item
    return indexed


def _pointer(value, path):
    if path == '':
        return value
    if not path.startswith('/'):
        raise ValueError('INVALID_POINTER')
    for segment in path[1:].split('/'):
        # Reject invalid RFC 6901 escapes rather than accepting ambiguous refs.
        if '~' in segment.replace('~0', '').replace('~1', ''):
            raise ValueError('INVALID_POINTER')
        key = segment.replace('~1', '/').replace('~0', '~')
        if isinstance(value, list):
            if not key.isascii() or not key.isdigit() or (len(key) > 1 and key[0] == '0'):
                raise ValueError('INVALID_POINTER')
            value = value[int(key)]
        else:
            value = value[key]
    return value


def _null_paths(value, path=''):
    if value is None:
        yield path
    elif isinstance(value, dict):
        for key, item in value.items():
            if key != 'fieldStates':
                yield from _null_paths(item, path + '/' + key.replace('~', '~0').replace('/', '~1'))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _null_paths(item, path + '/' + str(index))


def _field_states(value):
    states = value['fieldStates']
    for path in _null_paths(value):
        if path not in states:
            raise ValueError('UNEXPLAINED_NULL:' + path)
    for path in states:
        if _pointer(value, path) is not None:
            raise ValueError('FIELD_STATE_FOR_KNOWN_VALUE')


def _ordered(start, end):
    if start is not None and end is not None:
        if datetime.fromisoformat(start.replace('Z', '+00:00')) > datetime.fromisoformat(end.replace('Z', '+00:00')):
            raise ValueError('REVERSED_INTERVAL')


def validate_snapshot(snapshot):
    _bounded(snapshot)
    if not isinstance(snapshot, dict) or snapshot.get('schemaVersion') != VERSION:
        raise UnsupportedVersion('UNSUPPORTED_VERSION: no integrity judgment')
    if any(r.get('recordSchemaVersion') != VERSION for r in snapshot.get('records', [])) or any(
        run.get('recordSchemaVersion') != VERSION for run in snapshot.get('collectorRuns', [])):
        raise UnsupportedVersion('UNSUPPORTED_RECORD_VERSION: no integrity judgment')
    validate_schema('evidence', snapshot)
    records = _index(snapshot['records'], 'recordId')
    runs = _index(snapshot['collectorRuns'], 'collectorRunId')
    sources = _index(snapshot['sources'], 'sourceId')
    _field_states(snapshot['host'])
    for source in sources.values():
        _field_states(source)
    _ordered(snapshot['captureWindow']['startedAt'], snapshot['captureWindow']['endedAt'])
    for record in records.values():
        if record['sourceId'] not in sources or record['collectorRunId'] not in runs:
            raise ValueError('DANGLING_RECORD_REFERENCE')
        _field_states(record)
        window = record['observedWindow']
        _ordered(window['start'], window['end'])
        kind = record['recordType']
        if snapshot['origin'] == 'historical_transcription' and kind != 'historical_assertion':
            raise ValueError('HISTORICAL_NOT_RAW_QUERY')
        if kind == 'historical_assertion' and sources[record['sourceId']]['kind'] != 'user_handoff':
            raise ValueError('HISTORICAL_SOURCE_MISMATCH')
        if kind == 'firewall_rule':
            for target in record['payload']['filterRecordIds'] or []:
                if (target not in records or records[target]['recordType'] != 'firewall_filter'
                        or records[target]['payload']['ruleRecordId'] != record['recordId']):
                    raise ValueError('FILTER_ASSOCIATION_MISMATCH')
        if kind == 'firewall_filter':
            target = record['payload']['ruleRecordId']
            if (target not in records or records[target]['recordType'] != 'firewall_rule'
                    or record['recordId'] not in (records[target]['payload']['filterRecordIds'] or [])):
                raise ValueError('FILTER_ASSOCIATION_MISMATCH')
    for run_id, run in runs.items():
        _ordered(run['startedAt'], run['endedAt'])
        members = {r['recordId'] for r in records.values() if r['collectorRunId'] == run_id}
        if members != set(run['records']) or len(members) != len(run['records']):
            raise ValueError('RUN_RECORD_MISMATCH')
        if run['metrics']['recordCount'] != len(members):
            raise ValueError('RECORD_COUNT_MISMATCH')
        if run['status'] == 'success' and not members:
            raise ValueError('SUCCESS_WITHOUT_RECORDS')
        if run['status'] == 'empty' and members:
            raise ValueError('EMPTY_WITH_RECORDS')
        if run['status'] in ('inaccessible', 'unsupported', 'failed', 'timed_out',
                             'cancelled', 'not_requested') and members:
            raise ValueError('USE_PARTIAL_FOR_RETAINED_RECORDS')
        if run['status'] == 'partial' and run['coverage']['completeness'] != 'partial':
            raise ValueError('PARTIAL_COVERAGE_MISMATCH')
    if {rid: _digest(record) for rid, record in records.items()} != snapshot['integrity']['recordHashes']:
        raise ValueError('RECORD_INTEGRITY_MISMATCH')
    manifest = dict(snapshot)
    integrity = dict(snapshot['integrity'])
    expected = integrity.pop('manifestHash')
    manifest['integrity'] = integrity
    if _digest(manifest) != expected:
        raise ValueError('MANIFEST_INTEGRITY_MISMATCH')
    return records


def validate_derived_refs(document, snapshot, records=None):
    records = validate_snapshot(snapshot) if records is None else records

    def walk(value):
        if isinstance(value, dict):
            if 'evidenceRefs' in value:
                for reference in value['evidenceRefs']:
                    if reference['snapshotId'] != snapshot['snapshotId'] or reference['recordId'] not in records:
                        raise ValueError('DANGLING_EVIDENCE_REFERENCE')
                    try:
                        _pointer(records[reference['recordId']], reference['jsonPointer'])
                    except (KeyError, IndexError, TypeError, ValueError) as error:
                        raise ValueError('INVALID_EVIDENCE_POINTER') from error
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
    walk(document)
