"""Step 2a semantic regression and integrity rejection."""
import copy
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from silvergate.offline import ROOT, analyze


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


if __name__ == '__main__':
    unittest.main()
