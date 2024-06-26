from app.generate_documents import generate_documents

songs = [
    {"artist": "Arcade Fire", "title": "Wake Up"},
    {"artist": "Idina Menzel", "title": "Let It Go - From Frozen/Soundtrack Version"},
    # Add more songs here
]

api_key = "your_genius_api_key"
lyrics_output = "Lyrics_Document.docx"
chords_output = "Chords_Document.docx"

generate_documents(songs, api_key, lyrics_output, chords_output)
