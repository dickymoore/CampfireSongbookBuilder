import requests
from bs4 import BeautifulSoup
import logging
from app.cache import cache_data, load_cache
import json
import re
import html
import time
import os

# Configure logging
logger = logging.getLogger(__name__)

# Helper: Remove 'The' from artist
def strip_the(artist):
    return re.sub(r'^the\s+', '', artist, flags=re.IGNORECASE).strip()

# Helper: Remove punctuation from title
def strip_punct(title):
    return re.sub(r'[^\w\s]', '', title)

# Helper: Load manual lyrics from file
MANUAL_LYRICS_PATH = 'data/manual_lyrics.json'
def get_manual_lyrics(song_title, artist_name):
    if not os.path.exists(MANUAL_LYRICS_PATH):
        return None
    try:
        with open(MANUAL_LYRICS_PATH, 'r', encoding='utf-8') as f:
            manual = json.load(f)
        key = f"{artist_name} - {song_title}"
        return manual.get(key)
    except Exception as e:
        logger.error(f"Error loading manual lyrics: {e}")
        return None

# AZLyrics scraper
AZLYRICS_BASE = "https://www.azlyrics.com/lyrics"
def get_lyrics_from_azlyrics(song_title, artist_name):
    logger.debug(f"Trying AZLyrics for {song_title} by {artist_name}...")
    # AZLyrics URLs are like: https://www.azlyrics.com/lyrics/artist/title.html
    artist_url = re.sub(r'[^a-z0-9]', '', artist_name.lower().replace(' ', ''))
    title_url = re.sub(r'[^a-z0-9]', '', song_title.lower().replace(' ', ''))
    url = f"{AZLYRICS_BASE}/{artist_url}/{title_url}.html"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            logger.debug(f"AZLyrics returned status {response.status_code} for {url}")
            return "Lyrics not found."
        soup = BeautifulSoup(response.text, 'html.parser')
        # Lyrics are in the first div after all <div class="ringtone">
        divs = soup.find_all('div')
        for i, div in enumerate(divs):
            if div.get('class') == ['ringtone']:
                # Lyrics are in the next div without a class
                for next_div in divs[i+1:]:
                    if not next_div.get('class'):
                        lyrics = next_div.get_text("\n", strip=True)
                        if lyrics:
                            logger.debug(f"Lyrics found on AZLyrics for {song_title} by {artist_name}.")
                            return lyrics
                        break
                break
        logger.debug(f"Lyrics not found on AZLyrics for {song_title} by {artist_name}.")
        return "Lyrics not found."
    except Exception as e:
        logger.error(f"Error scraping AZLyrics for {song_title} by {artist_name}: {e}")
        return "Lyrics not found."

def get_genius_client(genius_access_token):
    import lyricsgenius
    return lyricsgenius.Genius(genius_access_token)

def get_lyrics_from_genius(song_title, artist_name, genius_client):
    logger.debug(f"Searching for lyrics for {song_title} by {artist_name}...")
    try:
        song = genius_client.search_song(song_title, artist_name)
        if song:
            lyrics = song.lyrics
            logger.debug(f"Lyrics found for {song_title} by {artist_name}.")
            return lyrics
        else:
            logger.debug(f"Lyrics not found for {song_title} by {artist_name}.")
            return get_lyrics_from_lyrics_ovh(song_title, artist_name)
    except Exception as e:
        logger.error(f"Error fetching lyrics for {song_title} by {artist_name} from Genius: {e}")
        return get_lyrics_from_lyrics_ovh(song_title, artist_name)

def get_lyrics_from_lyrics_ovh(song_title, artist_name):
    logger.debug(f"Trying Lyrics.ovh for {song_title} by {artist_name}...")
    url = f"https://api.lyrics.ovh/v1/{artist_name}/{song_title}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        lyrics = data.get("lyrics", "Lyrics not found.")
        if lyrics and lyrics != "Lyrics not found.":
            logger.debug(f"Lyrics found on Lyrics.ovh for {song_title} by {artist_name}.")
            return lyrics
        else:
            logger.debug(f"Lyrics not found on Lyrics.ovh for {song_title} by {artist_name}.")
            return "Lyrics not found."
    except Exception as e:
        logger.error(f"Error fetching lyrics from Lyrics.ovh for {song_title} by {artist_name}: {e}")
        return "Lyrics not found."

def get_lyrics_from_sources(song_title, artist_name, genius_client=None):
    """
    Try all sources and flexible queries for lyrics. Log which sources/queries were tried.
    Returns: (lyrics, source_name, tried_log)
    """
    tried_log = []
    queries = [
        (artist_name, song_title),
        (strip_the(artist_name), song_title),
        (artist_name, strip_punct(song_title)),
        (strip_the(artist_name), strip_punct(song_title)),
    ]
    sources = [
        ("Genius", lambda t, a: get_lyrics_from_genius(t, a, genius_client)),
        ("Lyrics.ovh", get_lyrics_from_lyrics_ovh),
        ("AZLyrics", get_lyrics_from_azlyrics),
        ("Manual", get_manual_lyrics),
    ]
    for artist, title in queries:
        for source_name, fetch_func in sources:
            try:
                lyrics = fetch_func(title, artist)
                tried_log.append(f"{source_name} ({artist} – {title})")
                if lyrics and lyrics.lower() not in ["lyrics not found.", "", None]:
                    logger.info(f"Lyrics found for {artist} – {title} from {source_name}")
                    return lyrics, source_name, tried_log
            except Exception as e:
                logger.error(f"Error with {source_name} for {artist} – {title}: {e}")
    logger.info(f"Lyrics not found for {artist_name} – {song_title} after trying all sources/queries.")
    return "Lyrics not found.", None, tried_log

def get_chords_from_chordie(song_title, artist_name):
    logger.debug(f"Searching for chords for {song_title} by {artist_name} on Chordie...")
    
    # Load chords cache
    chords_cache = load_cache('data/cache/chords_cache.json')
    cache_key = f"{artist_name} - {song_title}"

    # Check if chords are already in cache
    if cache_key in chords_cache and bool(chords_cache[cache_key]) and chords_cache[cache_key] != "Chords not found.":
        logger.debug(f"Chords loaded from cache for {song_title} by {artist_name}. Cache content: {chords_cache[cache_key][:100]}...")  # Log first 100 chars
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
            link_text = link.text.strip().lower()
            logger.debug(f"Found link text: {link_text}")
            if link and song_title.lower() in link_text and artist_name.lower() in link_text:
                song_link = link['href']
                chords_page_url = "https://www.chordie.com" + song_link
                logger.debug(f"Chords page URL matched: {chords_page_url}")
                break

        if chords_page_url:
            if not chords_page_url.startswith('https://'):
                chords_page_url = "https://www.chordie.com" + chords_page_url
            logger.debug(f"Fetching chords from URL: {chords_page_url}")
            chords_response = requests.get(chords_page_url)
            chords_response.raise_for_status()
            chords_soup = BeautifulSoup(chords_response.text, 'html.parser')
            chords_div = chords_soup.find("textarea", {"id": "chordproContent"})
            if chords_div:
                chords = chords_div.get_text()
                logger.debug(f"Chords found for {song_title} by {artist_name}.")
                # Cache the chords
                chords_cache[cache_key] = chords
                cache_data('data/cache/chords_cache.json', chords_cache)  # Save with prettified JSON
                return chords
            else:
                logger.debug(f"Chords content not found in the page for {song_title} by {artist_name}.")
                return get_chords_from_ultimate_guitar(song_title, artist_name)
        else:
            logger.debug(f"Chords link not found in the search results for {song_title} by {artist_name}.")
            return get_chords_from_ultimate_guitar(song_title, artist_name)
    except Exception as e:
        logger.error(f"Error fetching chords for {song_title} by {artist_name}: {e}")
        return get_chords_from_ultimate_guitar(song_title, artist_name)

def get_chords_from_ultimate_guitar(song_title, artist_name):
    logger.debug(f"Searching for chords for {song_title} by {artist_name} on Ultimate Guitar...")
    
    # Load chords cache
    chords_cache = load_cache('data/cache/chords_cache.json')
    cache_key = f"{artist_name} - {song_title}"

    # Check if chords are already in cache
    if cache_key in chords_cache and bool(chords_cache[cache_key]) and chords_cache[cache_key] != "Chords not found.":
        logger.debug(f"Chords loaded from cache for {song_title} by {artist_name}. Cache content: {chords_cache[cache_key][:100]}...")  # Log first 100 chars
        return chords_cache[cache_key]

    search_url = f"https://www.ultimate-guitar.com/search.php?search_type=title&value={song_title.replace(' ', '%20')}+{artist_name.replace(' ', '%20')}"
    try:
        response = requests.get(search_url)
        time.sleep(1)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find("div", class_="js-store")
        chords_page_url = None  # Always initialize
        if script_tag:
            try:
                data_content = json.loads(script_tag["data-content"])
                search_results = data_content.get("store", {}).get("page", {}).get("data", {}).get("results", [])
                for result in search_results:
                    if (
                        isinstance(result, dict)
                        and result.get("type") == "Chords"
                        and song_title.lower() in result.get("song_name", "").lower()
                        and artist_name.lower() in result.get("artist_name", "").lower()
                        and "tab_url" in result
                    ):
                        chords_page_url = result["tab_url"]
                        logger.debug(f"Chords page URL matched: {chords_page_url}")
                        break
            except Exception as e:
                logger.error(f"Error parsing Ultimate Guitar search results: {e}")
        else:
            logger.debug(f"No matching URL found in the search results for {song_title} by {artist_name}.")
            chords_cache[cache_key] = "Chords not found."
            cache_data('data/cache/chords_cache.json', chords_cache)  # Save with prettified JSON
            return "Chords not found."

        if chords_page_url:
            logger.debug(f"Fetching chords from URL: {chords_page_url}")
            try:
                chords_response = requests.get(chords_page_url)
                time.sleep(1)
                chords_response.raise_for_status()
                chords_soup = BeautifulSoup(chords_response.text, 'html.parser')
                chords_div = chords_soup.find('div', class_='js-store')
                if chords_div:
                    try:
                        data_content = chords_div['data-content']
                        decoded_data_content = html.unescape(data_content)
                        json_content = json.loads(decoded_data_content)
                        content_value = (
                            json_content.get('store', {})
                            .get('page', {})
                            .get('data', {})
                            .get('tab_view', {})
                            .get('wiki_tab', {})
                            .get('content')
                        )
                        if content_value:
                            chords = content_value
                            logger.debug(f"Chords found for {song_title} by {artist_name}.")
                            chords_cache[cache_key] = chords
                            cache_data('data/cache/chords_cache.json', chords_cache)
                            return chords
                        else:
                            logger.debug(f"Chords content not found in the page for {song_title} by {artist_name}.")
                    except Exception as e:
                        logger.error(f"Error parsing chords content for {song_title} by {artist_name}: {e}")
                chords_cache[cache_key] = "Chords not found."
                cache_data('data/cache/chords_cache.json', chords_cache)
                return "Chords not found."
            except Exception as e:
                logger.error(f"Error fetching chords for {song_title} by {artist_name}: {e}")
                chords_cache[cache_key] = "Chords not found."
                cache_data('data/cache/chords_cache.json', chords_cache)
                return "Chords not found."
        else:
            logger.debug(f"Chords link not found in the search results for {song_title} by {artist_name}.")
            chords_cache[cache_key] = "Chords not found."
            cache_data('data/cache/chords_cache.json', chords_cache)
            return "Chords not found."
    except Exception as e:
        logger.error(f"Error fetching chords for {song_title} by {artist_name}: {e}")
        chords_cache[cache_key] = "Chords not found."
        cache_data('data/cache/chords_cache.json', chords_cache)
        return "Chords not found."
