import requests
from bs4 import BeautifulSoup

def get_chords_from_ultimate_guitar(song_title, artist_name):
    search_url = f"https://www.ultimate-guitar.com/search.php?search_type=title&value={song_title} {artist_name}"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    result = soup.find("a", class_="js-tp_link")
    if result:
        chords_url = result['href']
        chords_response = requests.get(chords_url)
        chords_soup = BeautifulSoup(chords_response.text, 'html.parser')
        chords_div = chords_soup.find("pre", class_="js-tab-content")
        chords = chords_div.get_text() if chords_div else "Chords not found."
        return chords
    return "Chords not found."

def get_lyrics_from_genius(song_title, artist_name, api_key):
    base_url = "https://api.genius.com"
    headers = {'Authorization': f'Bearer {api_key}'}
    search_url = f"{base_url}/search"
    params = {'q': f"{song_title} {artist_name}"}
    response = requests.get(search_url, headers=headers, params=params)
    json_response = response.json()
    remote_song_info = None
    for hit in json_response['response']['hits']:
        if artist_name.lower() in hit['result']['primary_artist']['name'].lower():
            remote_song_info = hit
            break
    if remote_song_info:
        song_path = remote_song_info['result']['path']
        song_url = f"https://genius.com{song_path}"
        song_page = requests.get(song_url)
        song_page_soup = BeautifulSoup(song_page.text, 'html.parser')
        lyrics_div = song_page_soup.find("div", class_="lyrics")
        lyrics = lyrics_div.get_text() if lyrics_div else "Lyrics not found."
        return lyrics
    return "Lyrics not found."
