import json

from app.manual_import import ManualSongEntry, parse_manual_import, write_manual_json


def test_write_manual_json_merges_existing_entries(tmp_path):
    target = tmp_path / "manual_lyrics.json"
    target.write_text(
        json.dumps({"Existing Artist - Existing Song": "existing\n"}, indent=2) + "\n",
        encoding="utf-8",
    )

    entries = [
        ManualSongEntry(
            artist="New Artist",
            title="New Song",
            lyrics="new lyrics\n",
        )
    ]

    write_manual_json(target, entries, "lyrics")

    data = json.loads(target.read_text(encoding="utf-8"))
    assert data == {
        "Existing Artist - Existing Song": "existing\n",
        "New Artist - New Song": "new lyrics\n",
    }


def test_parse_manual_import_extracts_lyrics_from_chord_sheet():
    text = """# The Darkness - Friday Night
No capo

[Intro]
E A B x2

[Verse 1]
E
Hey you!
B
Do you remember me
A
I used to sit next to you at school
"""

    entries = parse_manual_import(text)

    assert len(entries) == 1
    entry = entries[0]
    assert entry.artist == "The Darkness"
    assert entry.title == "Friday Night"
    assert entry.chords is not None
    assert "No capo" in entry.chords
    assert entry.lyrics == "[Verse 1]\nHey you!\nDo you remember me\nI used to sit next to you at school\n"
