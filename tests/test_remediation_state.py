import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.remediation_state import (
    append_remediation_audit_record,
    build_remediated_content_record,
    create_backup_record,
    load_remediated_content,
    load_remediation_audit_records,
    record_remediation_audit,
    save_remediated_content,
)


class TestRemediationState(unittest.TestCase):
    def test_create_backup_record_writes_exact_identity_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            backups_dir = Path(tmp_dir) / "data" / "review" / "backups"

            record = create_backup_record(
                "The Campfire Trio",
                "Trail Song",
                "lyrics",
                "First line\nSecond line",
                backups_dir=backups_dir,
                captured_at="2026-05-23T19:20:00+01:00",
            )

            backup_path = Path(record["backup_path"])
            self.assertTrue(backup_path.exists())
            saved = json.loads(backup_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["song_key"], "The Campfire Trio - Trail Song")
            self.assertEqual(saved["content_type"], "lyrics")
            self.assertEqual(saved["content"], "First line\nSecond line")
            self.assertEqual(saved["content_hash"], record["content_hash"])

    def test_create_backup_record_avoids_overwriting_when_called_twice(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            backups_dir = Path(tmp_dir) / "data" / "review" / "backups"

            record1 = create_backup_record(
                "The Campfire Trio",
                "Trail Song",
                "lyrics",
                "First line\nSecond line",
                backups_dir=backups_dir,
                captured_at="2026-05-23T19:20:00+01:00",
            )
            record2 = create_backup_record(
                "The Campfire Trio",
                "Trail Song",
                "lyrics",
                "First line\nSecond line",
                backups_dir=backups_dir,
                captured_at="2026-05-23T19:20:00+01:00",
            )

            self.assertNotEqual(record1["backup_path"], record2["backup_path"])
            backup1 = Path(record1["backup_path"])
            backup2 = Path(record2["backup_path"])
            self.assertTrue(backup1.exists())
            self.assertTrue(backup2.exists())
            self.assertEqual(json.loads(backup1.read_text(encoding="utf-8"))["content"], "First line\nSecond line")
            self.assertEqual(json.loads(backup2.read_text(encoding="utf-8"))["content"], "First line\nSecond line")

    def test_save_and_load_remediated_content_round_trip(self):
        remediated_record = build_remediated_content_record(
            "The Campfire Trio",
            "Trail Song",
            "lyrics",
            "Cleaned verse\nCleaned chorus",
            "data/review/backups/the-campfire-trio-trail-song-lyrics.json",
            updated_at="2026-05-23T19:21:00+01:00",
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "remediated_content.json"

            save_remediated_content(target_path, [remediated_record])
            state, errors = load_remediated_content(target_path)

            self.assertEqual(errors, [])
            self.assertEqual(state["version"], 1)
            self.assertEqual(
                state["entries"]["The Campfire Trio - Trail Song"]["lyrics"],
                remediated_record,
            )

    def test_load_missing_remediated_content_returns_empty_state(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "remediated_content.json"

            state, errors = load_remediated_content(target_path)

            self.assertEqual(errors, [])
            self.assertEqual(state["entries"], {})
            self.assertIsNone(state["updated_at"])

    def test_record_remediation_audit_appends_success_and_failure_entries(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "audit" / "remediation_attempts.jsonl"

            self.assertTrue(
                record_remediation_audit(
                    "The Campfire Trio",
                    "Trail Song",
                    "lyrics",
                    "data/review/backups/pre.json",
                    "normalize_whitespace",
                    "success",
                    post_change_reference="data/review/remediated_content.json#trail-song-lyrics",
                    timestamp="2026-05-23T19:22:00+01:00",
                    file_path=target_path,
                )
            )
            self.assertTrue(
                record_remediation_audit(
                    "The Campfire Trio",
                    "Trail Song",
                    "lyrics",
                    "data/review/backups/pre.json",
                    "remove_scraper_residue",
                    "failed",
                    timestamp="2026-05-23T19:23:00+01:00",
                    file_path=target_path,
                )
            )

            records, errors = load_remediation_audit_records(target_path)

            self.assertEqual(errors, [])
            self.assertEqual([record["outcome"] for record in records], ["success", "failed"])
            self.assertEqual(records[0]["post_change_reference"], "data/review/remediated_content.json#trail-song-lyrics")
            self.assertIsNone(records[1]["post_change_reference"])

    def test_load_remediation_audit_reports_malformed_lines_without_losing_valid_records(self):
        valid_record = {
            "artist": "The Campfire Trio",
            "title": "Trail Song",
            "song_key": "The Campfire Trio - Trail Song",
            "content_type": "lyrics",
            "pre_change_reference": "data/review/backups/pre.json",
            "post_change_reference": None,
            "remediation_reason": "normalize_whitespace",
            "outcome": "failed",
            "timestamp": "2026-05-23T19:23:00+01:00",
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            target_path = Path(tmp_dir) / "data" / "review" / "audit" / "remediation_attempts.jsonl"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text("not json\n[]\n{}\n".format(json.dumps(valid_record)), encoding="utf-8")

            records, errors = load_remediation_audit_records(target_path)

            self.assertEqual(records, [valid_record])
            self.assertEqual(len(errors), 2)
            self.assertEqual(errors[0]["field"], "[line 1]")
            self.assertEqual(errors[1]["field"], "[line 2]")

    def test_append_remediation_audit_failure_is_recoverable(self):
        with patch.object(Path, "open", side_effect=OSError("disk full")):
            self.assertFalse(
                append_remediation_audit_record(
                    "/tmp/unwritable/remediation_attempts.jsonl",
                    {"song_key": "The Campfire Trio - Trail Song"},
                )
            )


if __name__ == "__main__":
    unittest.main()
