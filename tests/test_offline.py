"""Step 2a semantic regression and integrity rejection."""
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from silvergate.offline import ROOT, analyze
from silvergate import importer

sys.path.insert(0, str(ROOT / 'tests/contract'))
from check_contracts import (load as oracle_load, validate_snapshot as oracle_validate,
                             validate_derived_refs as oracle_refs, seal)


class OfflineTests(unittest.TestCase):
    def test_synthetic_outputs_match_expected_semantics(self):
        fixture = ROOT / 'tests/fixtures/synthetic/basic.snapshot.json'
        for name, actual in zip(('normalized', 'claims', 'findings'), analyze(fixture)):
            expected = json.loads(fixture.with_name(f'basic.{name}.json').read_text())
            self.assertEqual(expected, actual, name)

    def test_modified_evidence_is_rejected_before_analysis(self):
        fixture = ROOT / 'tests/fixtures/synthetic/basic.snapshot.json'
        snapshot = json.loads(fixture.read_text())
        snapshot['records'][0]['payload']['imagePath'] = 'modified.exe'
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'snapshot.json'
            path.write_text(json.dumps(snapshot))
            with self.assertRaisesRegex(ValueError, 'INTEGRITY'):
                analyze(path)

    def test_rejects_unsupported_scope(self):
        fixture = ROOT / 'tests/fixtures/aaronaura-historical/spotify.snapshot.json'
        with self.assertRaisesRegex(ValueError, 'UNSUPPORTED_ANALYSIS_SCOPE'):
            analyze(fixture)

    def test_runtime_and_oracle_agree_on_fixture(self):
        path = ROOT / 'tests/fixtures/synthetic/basic.snapshot.json'
        self.assertEqual(oracle_load(path), importer.load(path))
        self.assertEqual(oracle_validate(oracle_load(path)),
                         importer.validate_snapshot(importer.load(path)))
        for name, document in zip(('normalized', 'claims', 'findings'), analyze(path)):
            oracle_refs(document, oracle_load(path))
            importer.validate_schema(name, document)
            importer.validate_derived_refs(document, importer.load(path))

    def test_mutations_rejected_by_both_validators(self):
        path = ROOT / 'tests/fixtures/synthetic/basic.snapshot.json'
        base = oracle_load(path)
        cases = []
        tampered = json.loads(json.dumps(base))
        tampered['records'][0]['payload']['pid'] = 101
        cases.append((tampered, 'RECORD_INTEGRITY_MISMATCH'))
        tampered = json.loads(json.dumps(base))
        tampered['producer']['version'] = 'changed'
        cases.append((tampered, 'MANIFEST_INTEGRITY_MISMATCH'))
        dangling = json.loads(json.dumps(base))
        dangling['records'][0]['sourceId'] = 'missing'
        cases.append((seal(dangling), 'DANGLING_RECORD_REFERENCE'))
        bad_run = json.loads(json.dumps(base))
        bad_run['collectorRuns'][0]['records'].pop()
        cases.append((seal(bad_run), 'RUN_RECORD_MISMATCH'))
        bad_filter = json.loads(json.dumps(base))
        bad_filter['records'][4]['payload']['ruleRecordId'] = 'record-1'
        cases.append((seal(bad_filter), 'FILTER_ASSOCIATION_MISMATCH'))
        for snapshot, error in cases:
            with self.subTest(error=error):
                for validator in (oracle_validate, importer.validate_snapshot):
                    with self.assertRaisesRegex(ValueError, error):
                        validator(snapshot)

    def test_unsupported_versions_are_compatibility_errors(self):
        path = ROOT / 'tests/fixtures/synthetic/basic.snapshot.json'
        for location in ('schema', 'record', 'run'):
            snapshot = oracle_load(path)
            if location == 'schema':
                snapshot['schemaVersion'] = '2.0.0'
            elif location == 'record':
                snapshot['records'][0]['recordSchemaVersion'] = '2.0.0'
            else:
                snapshot['collectorRuns'][0]['recordSchemaVersion'] = '2.0.0'
            with self.subTest(location=location):
                with self.assertRaises(importer.UnsupportedVersion):
                    importer.validate_snapshot(snapshot)
                with TemporaryDirectory() as directory:
                    target = Path(directory) / 'unsupported.json'
                    target.write_text(json.dumps(snapshot))
                    with self.assertRaises(importer.UnsupportedVersion):
                        analyze(target)

    def test_derived_reference_failures(self):
        snapshot = oracle_load(ROOT / 'tests/fixtures/synthetic/basic.snapshot.json')
        document = analyze(ROOT / 'tests/fixtures/synthetic/basic.snapshot.json')[1]
        document['claims'][0]['evidenceRefs'][0]['recordId'] = 'missing'
        with self.assertRaisesRegex(ValueError, 'DANGLING_EVIDENCE_REFERENCE'):
            importer.validate_derived_refs(document, snapshot)
        document['claims'][0]['evidenceRefs'][0]['recordId'] = 'record-1'
        document['claims'][0]['evidenceRefs'][0]['jsonPointer'] = '/payload/noSuchField'
        with self.assertRaisesRegex(ValueError, 'INVALID_EVIDENCE_POINTER'):
            importer.validate_derived_refs(document, snapshot)


if __name__ == '__main__':
    unittest.main()
