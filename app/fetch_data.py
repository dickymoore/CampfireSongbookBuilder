import requests
from bs4 import BeautifulSoup
import logging

# Configure logging
logger = logging.getLogger(__name__)

def get_genius_client(access_token):
    import lyricsgenius
    return lyricsgenius.Genius(access_token)

def get_lyrics_from_genius(song_title, artist_name, genius_client):
    logger.debug(f"Searching for lyrics for {song_title} by {artist_name}...")
    try:
        song = genius_client.search_song(song_title, artist_name)
        if song:
            lyrics = song.lyrics
            logger.debug("Lyrics found.")
            return lyrics
        else:
            logger.debug("Lyrics not found.")
            return "Lyrics not found."
    except Exception as e:
        logger.error(f"Error fetching lyrics: {e}")
        return "Lyrics not found."

def get_chords_from_ultimate_guitar(song_title, artist_name):
    logger.debug(f"Searching for chords for {song_title} by {artist_name}...")
    search_url = f"https://www.ultimate-guitar.com/search.php?search_type=title&value={song_title} {artist_name}"
    try:
        response = requests.get(search_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        result = soup.find("a", class_="js-tp_link")
        if result:
            chords_url = result['href']
            logger.debug(f"Found chords link: {chords_url}")
            chords_response = requests.get(chords_url)
            chords_soup = BeautifulSoup(chords_response.text, 'html.parser')
            chords_div = chords_soup.find("pre", class_="js-tab-content")
            if chords_div:
                chords = chords_div.get_text()
                logger.debug("Chords found.")
                return chords
            else:
                logger.debug("Chords content not found in the page.")
                return "Chords not found."
        else:
            logger.debug("Chords link not found in the search results.")
            return "Chords not found."
    except Exception as e:
        logger.error(f"Error fetching chords: {e}")
        return "Chords not found."
