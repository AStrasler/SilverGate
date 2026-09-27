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

    def test_structured_correlation_matches_golden_outputs(self):
        path = ROOT / 'tests/fixtures/synthetic/correlation.snapshot.json'
        snapshot = importer.load(path)
        importer.validate_snapshot(snapshot)
        normalized, claims, findings = analyze(path)
        for name, actual in zip(('normalized', 'claims', 'findings'),
                                (normalized, claims, findings)):
            expected = json.loads(path.with_name(f'correlation.{name}.json').read_text())
            self.assertEqual(expected, actual)
            importer.validate_schema(name, actual)
            importer.validate_derived_refs(actual, snapshot)
        direct = [claim for claim in claims['claims'] if claim['epistemicStatus'] == 'fact']
        candidates = [claim for claim in claims['claims']
                      if claim['predicate'] == 'candidate_permission_for_listener']
        self.assertEqual(4, len(direct))
        self.assertEqual(1, len(candidates))
        candidate = candidates[0]
        self.assertEqual('inference', candidate['epistemicStatus'])
        self.assertEqual('heuristic', candidate['strength'])
        self.assertEqual(7, len(candidate['evidenceRefs']))
        self.assertEqual(2, len(candidate['premiseClaimIds']))
        self.assertTrue(set(candidate['premiseClaimIds']) <=
                        {claim['claimId'] for claim in direct})
        for claim, finding in zip(claims['claims'], findings['findings']):
            self.assertEqual((claim['epistemicStatus'], claim['value'], claim['evidenceRefs']),
                             (finding['epistemicStatus'], finding['value'], finding['evidenceRefs']))

    def test_required_support_withdraws_inference(self):
        path = ROOT / 'tests/fixtures/synthetic/correlation.snapshot.json'
        variants = {
            'port_mismatch': lambda s: s['records'][4]['payload']['conditions'][0].update(values=['7769']),
            'not_listening': lambda s: s['records'][1]['payload'].update(state='Established'),
            'rule_disabled': lambda s: s['records'][3]['payload'].update(enabled=False),
        }
        for name, change in variants.items():
            with self.subTest(name=name), TemporaryDirectory() as directory:
                snapshot = importer.load(path)
                change(snapshot)
                seal(snapshot)
                variant = Path(directory) / 'variant.json'
                variant.write_text(json.dumps(snapshot))
                oracle_validate(snapshot)
                importer.validate_snapshot(snapshot)
                _, claims, findings = analyze(variant)
                self.assertNotIn('candidate_permission_for_listener',
                                 [c['predicate'] for c in claims['claims']])
                self.assertNotIn('candidate_permission_for_listener',
                                 [f['predicate'] for f in findings['findings']])
                self.assertEqual(4, len([c for c in claims['claims']
                                         if c['epistemicStatus'] == 'fact']))


if __name__ == '__main__':
    unittest.main()
