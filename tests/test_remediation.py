import subprocess
import tempfile
import unittest
from pathlib import Path

from app.remediation import run_bounded_remediation
from app.remediation_state import load_remediated_content, load_remediation_audit_records


class TestRemediation(unittest.TestCase):
    def _score(self, quality_score, *signal_codes):
        return {
            "artist": "The Campfire Trio",
            "title": "Trail Song",
            "song_key": "The Campfire Trio - Trail Song",
            "content_type": "lyrics",
            "content_hash": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            "quality_score": quality_score,
            "quality_band": "poor" if quality_score < 40 else "questionable",
            "score_version": "v1",
            "score_reasons": ["signal:{}".format(code) for code in signal_codes],
            "scored_at": "2026-05-23T19:30:00+01:00",
        }

    def test_run_bounded_remediation_routes_allowed_candidate_through_codex_exec(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace_root = Path(tmp_dir)
            remediated_content_path = workspace_root / "data" / "review" / "remediated_content.json"
            backups_dir = workspace_root / "data" / "review" / "backups"
            audit_path = workspace_root / "data" / "review" / "audit" / "remediation_attempts.jsonl"
            captured = {}

            def runner(command, input=None, check=None, capture_output=None, text=None):
                captured["command"] = command
                captured["prompt"] = input
                output_path = Path(command[command.index("-o") + 1])
                output_path.write_text("Verse 1\nChorus", encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, "", "")

            result = run_bounded_remediation(
                "The Campfire Trio",
                "Trail Song",
                "lyrics",
                "Verse 1\n\n\n<div>junk</div>\nVerse 1",
                self._score(25, "html_residue", "duplicate_block"),
                workspace_root=workspace_root,
                remediated_content_path=remediated_content_path,
                backups_dir=backups_dir,
                audit_path=audit_path,
                runner=runner,
            )

            self.assertEqual(result["status"], "success")
            self.assertFalse(result["manual_review_required"])
            self.assertEqual(
                result["approved_operations"],
                [
                    "removal of obvious scraper residue",
                    "normalization or removal of repeated junk blocks",
                ],
            )
            self.assertIn("codex", captured["command"][0])
            self.assertEqual(captured["command"][1], "exec")
            self.assertIn("removal of obvious scraper residue", captured["prompt"])
            self.assertIn("Hard constraints:", captured["prompt"])
            self.assertIn("semantic rewriting", captured["prompt"])

            remediated_state, errors = load_remediated_content(remediated_content_path)
            self.assertEqual(errors, [])
            self.assertEqual(
                remediated_state["entries"]["The Campfire Trio - Trail Song"]["lyrics"]["content"],
                "Verse 1\nChorus",
            )

            audit_records, audit_errors = load_remediation_audit_records(audit_path)
            self.assertEqual(audit_errors, [])
            self.assertEqual(
                [record["outcome"] for record in audit_records],
                ["allowed", "attempted", "success"],
            )

    def test_run_bounded_remediation_refuses_out_of_scope_candidate(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace_root = Path(tmp_dir)
            audit_path = workspace_root / "data" / "review" / "audit" / "remediation_attempts.jsonl"
            runner_calls = []

            def runner(*args, **kwargs):
                runner_calls.append((args, kwargs))
                raise AssertionError("runner should not be called for refused candidates")

            result = run_bounded_remediation(
                "The Campfire Trio",
                "Trail Song",
                "lyrics",
                "Unknown words",
                self._score(10, "missing_lyrics"),
                workspace_root=workspace_root,
                audit_path=audit_path,
                runner=runner,
            )

            self.assertEqual(result["status"], "refused")
            self.assertTrue(result["manual_review_required"])
            self.assertEqual(result["reason_code"], "out_of_scope_signal")
            self.assertEqual(runner_calls, [])

            audit_records, audit_errors = load_remediation_audit_records(audit_path)
            self.assertEqual(audit_errors, [])
            self.assertEqual([record["outcome"] for record in audit_records], ["refused"])

    def test_run_bounded_remediation_records_failed_attempts(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace_root = Path(tmp_dir)
            remediated_content_path = workspace_root / "data" / "review" / "remediated_content.json"
            audit_path = workspace_root / "data" / "review" / "audit" / "remediation_attempts.jsonl"

            def runner(command, input=None, check=None, capture_output=None, text=None):
                raise subprocess.CalledProcessError(1, command, stderr="failure")

            result = run_bounded_remediation(
                "The Campfire Trio",
                "Trail Song",
                "lyrics",
                "Verse 1\n[JUNK]\n[JUNK]",
                self._score(20, "duplicate_block"),
                workspace_root=workspace_root,
                remediated_content_path=remediated_content_path,
                audit_path=audit_path,
                runner=runner,
            )

            self.assertEqual(result["status"], "failed")
            self.assertTrue(result["manual_review_required"])
            self.assertEqual(result["reason_code"], "codex_exec_failed")

            remediated_state, errors = load_remediated_content(remediated_content_path)
            self.assertEqual(errors, [])
            self.assertEqual(remediated_state["entries"], {})

            audit_records, audit_errors = load_remediation_audit_records(audit_path)
            self.assertEqual(audit_errors, [])
            self.assertEqual(
                [record["outcome"] for record in audit_records],
                ["allowed", "attempted", "failed"],
            )


if __name__ == "__main__":
    unittest.main()
