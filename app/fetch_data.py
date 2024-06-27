import requests
from bs4 import BeautifulSoup
import logging
from app.cache import cache_data, load_cache

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

def get_chords_from_chordie(song_title, artist_name):
    logger.debug(f"Searching for chords for {song_title} by {artist_name} on Chordie...")
    
    # Load chords cache
    chords_cache = load_cache('data/cache/chords_cache.json')
    cache_key = f"{artist_name} - {song_title}"

    # Check if chords are already in cache
    if cache_key in chords_cache and bool(chords_cache[cache_key]):
        logger.debug("Chords loaded from cache.")
        return chords_cache[cache_key]

    search_url = f"https://www.chordie.com/result.php?q={song_title.replace(' ', '+')}+by+{artist_name.replace(' ', '+')}"
    try:
        response = requests.get(search_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        song_links = soup.find_all('div', class_='clearfix songList')
        
        chords_page_url = None
        for song in song_links:
            link = song.find('a', href=True)
            if link and song_title in link.text:
                song_link = link['href']
                chords_page_url = "https://www.chordie.com" + song_link
                break

        if chords_page_url:
            if not chords_page_url.startswith('https://'):
                chords_page_url = "https://www.chordie.com" + chords_page_url
            logger.debug(f"Chords page URL found: {chords_page_url}")
            chords_response = requests.get(chords_page_url)
            chords_response.raise_for_status()
            chords_soup = BeautifulSoup(chords_response.text, 'html.parser')
            chords_div = chords_soup.find("textarea", {"id": "chordproContent"})
            if chords_div:
                chords = chords_div.get_text()
                logger.debug("Chords found.")
                # Cache the chords
                chords_cache[cache_key] = chords
                cache_data('data/cache/chords_cache.json', chords_cache)
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
