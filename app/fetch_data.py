"""Functions to fetch lyrics and chords from various external sources.

This module contains helper functions and flexible pipelines to retrieve
lyrics and chord charts from several online sites.  For lyrics the sources
currently tried (in order) are Genius, Lyrics.ovh, AZLyrics and a manual
lyrics file.  For chords the sources tried include Chordie, Ultimate Guitar,
E‑Chords, Songsterr and Yousician.  Each fetch function checks the cache
first and attempts to write successful results back to the cache via
``jsonl_save_entry``.

These functions may make HTTP requests; in environments without network
access they will return ``"Lyrics not found."`` or ``"Chords not found."``
gracefully.  See ``app/document_generation.py`` for the high level caching
orchestration.
"""

import requests
from bs4 import BeautifulSoup
import logging
from .cache import jsonl_save_entry, jsonl_load_entry, jsonl_load_all
import json
import re
import html
import time
import os

# Configure logging
logger = logging.getLogger(__name__)

# Helper: Remove 'The' from artist
def strip_the(artist: str) -> str:
    return re.sub(r'^the\s+', '', artist, flags=re.IGNORECASE).strip()

# Helper: Remove punctuation from title
def strip_punct(title: str) -> str:
    return re.sub(r'[^\w\s]', '', title)

# Helper: Load manual lyrics from file
MANUAL_LYRICS_PATH = 'data/manual_lyrics.json'
def get_manual_lyrics(song_title: str, artist_name: str) -> str | None:
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
def get_lyrics_from_azlyrics(song_title: str, artist_name: str) -> str:
    logger.debug(f"Trying AZLyrics for {song_title} by {artist_name}...")
    cached = jsonl_load_entry('data/cache/lyrics_cache.jsonl', artist_name, song_title, 'lyrics')
    if cached and cached != "Lyrics not found.":
        logger.debug(f"Lyrics loaded from cache for {song_title} by {artist_name}.")
        return cached
    artist_url = re.sub(r'[^a-z0-9]', '', artist_name.lower().replace(' ', ''))
    title_url = re.sub(r'[^a-z0-9]', '', song_title.lower().replace(' ', ''))
    url = f"https://www.azlyrics.com/lyrics/{artist_url}/{title_url}.html"
    try:
        response = requests.get(url, timeout=10)
        response.encoding = response.apparent_encoding
        if response.status_code != 200:
            logger.debug(f"AZLyrics returned status {response.status_code} for {url}")
            jsonl_save_entry('data/cache/lyrics_cache.jsonl', artist_name, song_title, "Lyrics not found.", 'lyrics')
            return "Lyrics not found."
        soup = BeautifulSoup(response.text, 'html.parser')
        # Lyrics are in the first div after all <div class="ringtone">
        divs = soup.find_all('div')
        for i, div in enumerate(divs):
            if div.get('class') == ['ringtone']:
                for next_div in divs[i+1:]:
                    if not next_div.get('class'):
                        lyrics = next_div.get_text("\n", strip=True)
                        if lyrics:
                            logger.debug(f"Lyrics found on AZLyrics for {song_title} by {artist_name}.")
                            jsonl_save_entry('data/cache/lyrics_cache.jsonl', artist_name, song_title, lyrics, 'lyrics')
                            return lyrics
                        break
                break
        logger.debug(f"Lyrics not found on AZLyrics for {song_title} by {artist_name}.")
        jsonl_save_entry('data/cache/lyrics_cache.jsonl', artist_name, song_title, "Lyrics not found.", 'lyrics')
        return "Lyrics not found."
    except Exception as e:
        logger.error(f"Error scraping AZLyrics for {song_title} by {artist_name}: {e}")
        jsonl_save_entry('data/cache/lyrics_cache.jsonl', artist_name, song_title, "Lyrics not found.", 'lyrics')
        return "Lyrics not found."

def get_genius_client(genius_access_token: str):
    import lyricsgenius
    return lyricsgenius.Genius(genius_access_token)

def get_lyrics_from_genius(song_title: str, artist_name: str, genius_client) -> str:
    logger.debug(f"Searching for lyrics for {song_title} by {artist_name}...")
    cached = jsonl_load_entry('data/cache/lyrics_cache.jsonl', artist_name, song_title, 'lyrics')
    if cached and cached != "Lyrics not found.":
        logger.debug(f"Lyrics loaded from cache for {song_title} by {artist_name}.")
        return cached
    try:
        song = genius_client.search_song(song_title, artist_name)
        if song:
            lyrics = song.lyrics
            logger.debug(f"Lyrics found for {song_title} by {artist_name}.")
            jsonl_save_entry('data/cache/lyrics_cache.jsonl', artist_name, song_title, lyrics, 'lyrics')
            return lyrics
        else:
            logger.debug(f"Lyrics not found for {song_title} by {artist_name}.")
            jsonl_save_entry('data/cache/lyrics_cache.jsonl', artist_name, song_title, "Lyrics not found.", 'lyrics')
            return get_lyrics_from_lyrics_ovh(song_title, artist_name)
    except Exception as e:
        logger.error(f"Error fetching lyrics for {song_title} by {artist_name} from Genius: {e}")
        jsonl_save_entry('data/cache/lyrics_cache.jsonl', artist_name, song_title, "Lyrics not found.", 'lyrics')
        return get_lyrics_from_lyrics_ovh(song_title, artist_name)

def get_lyrics_from_lyrics_ovh(song_title: str, artist_name: str) -> str:
    logger.debug(f"Trying Lyrics.ovh for {song_title} by {artist_name}...")
    cached = jsonl_load_entry('data/cache/lyrics_cache.jsonl', artist_name, song_title, 'lyrics')
    if cached and cached != "Lyrics not found.":
        logger.debug(f"Lyrics loaded from cache for {song_title} by {artist_name}.")
        return cached
    url = f"https://api.lyrics.ovh/v1/{artist_name}/{song_title}"
    try:
        response = requests.get(url)
        response.encoding = response.apparent_encoding
        response.raise_for_status()
        data = response.json()
        lyrics = data.get("lyrics", "Lyrics not found.")
        if lyrics and lyrics != "Lyrics not found.":
            logger.debug(f"Lyrics found on Lyrics.ovh for {song_title} by {artist_name}.")
            jsonl_save_entry('data/cache/lyrics_cache.jsonl', artist_name, song_title, lyrics, 'lyrics')
            return lyrics
        else:
            logger.debug(f"Lyrics not found on Lyrics.ovh for {song_title} by {artist_name}.")
            jsonl_save_entry('data/cache/lyrics_cache.jsonl', artist_name, song_title, "Lyrics not found.", 'lyrics')
            return "Lyrics not found."
    except Exception as e:
        logger.error(f"Error fetching lyrics from Lyrics.ovh for {song_title} by {artist_name}: {e}")
        jsonl_save_entry('data/cache/lyrics_cache.jsonl', artist_name, song_title, "Lyrics not found.", 'lyrics')
        return "Lyrics not found."

def get_lyrics_from_sources(song_title: str, artist_name: str, genius_client=None):
    """
    Try all sources and flexible queries for lyrics.  Log which sources/queries were tried.

    Returns: (lyrics, source_name, tried_log)
    """
    tried_log: list[str] = []
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
                if lyrics and isinstance(lyrics, str) and lyrics.lower() not in ["lyrics not found.", "", None]:
                    logger.info(f"Lyrics found for {artist} – {title} from {source_name}")
                    return lyrics, source_name, tried_log
            except Exception as e:
                logger.error(f"Error with {source_name} for {artist} – {title}: {e}")
    logger.info(f"Lyrics not found for {artist_name} – {song_title} after trying all sources/queries.")
    return "Lyrics not found.", None, tried_log

# E‑Chords scraper
E_CHORDS_BASE = "https://www.e-chords.com/chords"
def get_chords_from_echords(song_title: str, artist_name: str) -> str:
    logger.debug(f"Trying E‑Chords for {song_title} by {artist_name}...")
    artist_url = re.sub(r'[^a-z0-9]', '-', artist_name.lower())
    title_url = re.sub(r'[^a-z0-9]', '-', song_title.lower())
    url = f"{E_CHORDS_BASE}/{artist_url}/{title_url}"
    try:
        response = requests.get(url, timeout=10)
        response.encoding = response.apparent_encoding
        if response.status_code != 200:
            logger.debug(f"E‑Chords returned status {response.status_code} for {url}")
            return "Chords not found."
        soup = BeautifulSoup(response.text, 'html.parser')
        chords_div = soup.find('pre', class_='core')
        if chords_div:
            chords = chords_div.get_text("\n", strip=True)
            if chords:
                logger.debug(f"Chords found on E‑Chords for {song_title} by {artist_name}.")
                return chords
        logger.debug(f"Chords not found on E‑Chords for {song_title} by {artist_name}.")
        return "Chords not found."
    except Exception as e:
        logger.error(f"Error scraping E‑Chords for {song_title} by {artist_name}: {e}")
        return "Chords not found."

# Songsterr scraper
SONGSTERR_SEARCH = "https://www.songsterr.com/a/wa/search?pattern="
def get_chords_from_songsterr(song_title: str, artist_name: str) -> str:
    logger.debug(f"Trying Songsterr for {song_title} by {artist_name}...")
    query = f"{song_title} {artist_name}"
    url = f"{SONGSTERR_SEARCH}{requests.utils.quote(query)}"
    try:
        response = requests.get(url, timeout=10)
        response.encoding = response.apparent_encoding
        if response.status_code != 200:
            logger.debug(f"Songsterr returned status {response.status_code} for {url}")
            return "Chords not found."
        soup = BeautifulSoup(response.text, 'html.parser')
        link = soup.find('a', href=True, class_='song')
        if link and 'href' in link.attrs:
            song_url = f"https://www.songsterr.com{link['href']}"
            song_response = requests.get(song_url, timeout=10)
            song_response.encoding = song_response.apparent_encoding
            if song_response.status_code != 200:
                logger.debug(f"Songsterr song page returned status {song_response.status_code} for {song_url}")
                return "Chords not found."
            song_soup = BeautifulSoup(song_response.text, 'html.parser')
            tab_pre = song_soup.find('pre', class_='js-tab-content')
            if tab_pre:
                chords = tab_pre.get_text("\n", strip=True)
                if chords:
                    logger.debug(f"Chords found on Songsterr for {song_title} by {artist_name}.")
                    return chords
        logger.debug(f"Chords not found on Songsterr for {song_title} by {artist_name}.")
        return "Chords not found."
    except Exception as e:
        logger.error(f"Error scraping Songsterr for {song_title} by {artist_name}: {e}")
        return "Chords not found."

def get_chords_from_chordie(song_title: str, artist_name: str) -> str:
    logger.debug(f"Searching for chords for {song_title} by {artist_name} on Chordie...")
    chords_cache = jsonl_load_all('data/cache/chords_cache.jsonl', 'chords')
    cache_key = f"{artist_name} - {song_title}"
    if cache_key in chords_cache and bool(chords_cache[cache_key]) and chords_cache[cache_key] != "Chords not found.":
        logger.debug(f"Chords loaded from cache for {song_title} by {artist_name}. Cache content: {chords_cache[cache_key][:100]}...")
        return chords_cache[cache_key]
    search_url = f"https://www.chordie.com/result.php?q={song_title.replace(' ', '+')}+by+{artist_name.replace(' ', '+')}"
    try:
        response = requests.get(search_url)
        response.encoding = response.apparent_encoding
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
            chords_response.encoding = chords_response.apparent_encoding
            chords_response.raise_for_status()
            chords_soup = BeautifulSoup(chords_response.text, 'html.parser')
            chords_div = chords_soup.find("textarea", {"id": "chordproContent"})
            if chords_div:
                chords = chords_div.get_text()
                logger.debug(f"Chords found for {song_title} by {artist_name}.")
                jsonl_save_entry('data/cache/chords_cache.jsonl', artist_name, song_title, chords, 'chords')
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

def get_chords_from_ultimate_guitar(song_title: str, artist_name: str) -> str:
    logger.debug(f"Searching for chords for {song_title} by {artist_name} on Ultimate Guitar...")
    chords_cache = jsonl_load_all('data/cache/chords_cache.jsonl', 'chords')
    cache_key = f"{artist_name} - {song_title}"
    if cache_key in chords_cache and bool(chords_cache[cache_key]) and chords_cache[cache_key] != "Chords not found.":
        logger.debug(f"Chords loaded from cache for {song_title} by {artist_name}. Cache content: {chords_cache[cache_key][:100]}...")
        return chords_cache[cache_key]
    search_url = f"https://www.ultimate-guitar.com/search.php?search_type=title&value={song_title.replace(' ', '%20')}+{artist_name.replace(' ', '%20')}"
    try:
        response = requests.get(search_url)
        response.encoding = response.apparent_encoding
        time.sleep(1)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find("div", class_="js-store")
        chords_page_url = None
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
                logger.error(f"Error parsing Ultimate Guitar search results: {e}")
        else:
            logger.debug(f"No matching URL found in the search results for {song_title} by {artist_name}.")
            chords_cache[cache_key] = "Chords not found."
            jsonl_save_entry('data/cache/chords_cache.jsonl', artist_name, song_title, "Chords not found.", 'chords')
            return "Chords not found."
        if chords_page_url:
            logger.debug(f"Fetching chords from URL: {chords_page_url}")
            try:
                chords_response = requests.get(chords_page_url)
                chords_response.encoding = chords_response.apparent_encoding
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
                            jsonl_save_entry('data/cache/chords_cache.jsonl', artist_name, song_title, chords, 'chords')
                            return chords
                        else:
                            logger.debug(f"Chords content not found in the page for {song_title} by {artist_name}.")
                    except Exception as e:
                        logger.error(f"Error parsing chords content for {song_title} by {artist_name}: {e}")
                chords_cache[cache_key] = "Chords not found."
                jsonl_save_entry('data/cache/chords_cache.jsonl', artist_name, song_title, "Chords not found.", 'chords')
                return "Chords not found."
            except Exception as e:
                logger.error(f"Error fetching chords for {song_title} by {artist_name}: {e}")
                chords_cache[cache_key] = "Chords not found."
                jsonl_save_entry('data/cache/chords_cache.jsonl', artist_name, song_title, "Chords not found.", 'chords')
                return "Chords not found."
        else:
            logger.debug(f"Chords link not found in the search results for {song_title} by {artist_name}.")
            chords_cache[cache_key] = "Chords not found."
            jsonl_save_entry('data/cache/chords_cache.jsonl', artist_name, song_title, "Chords not found.", 'chords')
            return "Chords not found."
    except Exception as e:
        logger.error(f"Error fetching chords for {song_title} by {artist_name}: {e}")
        chords_cache[cache_key] = "Chords not found."
        jsonl_save_entry('data/cache/chords_cache.jsonl', artist_name, song_title, "Chords not found.", 'chords')
        return "Chords not found."

# Yousician scraper
def get_chords_from_yousician(song_title: str, artist_name: str) -> str:
    logger.debug(f"Trying Yousician for {song_title} by {artist_name}...")
    def format_for_url(s: str) -> str:
        return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
    artist_url = format_for_url(artist_name)
    title_url = format_for_url(song_title)
    url = f"https://yousician.com/chords/{artist_url}/{title_url}"
    try:
        response = requests.get(url, timeout=10)
        response.encoding = response.apparent_encoding
        if response.status_code != 200:
            logger.debug(f"Yousician returned status {response.status_code} for {url}")
            return "Chords not found."
        soup = BeautifulSoup(response.text, 'html.parser')
        chords_pre = soup.find('pre')
        if chords_pre:
            chords = chords_pre.get_text("\n", strip=True)
            if chords:
                logger.debug(f"Chords found on Yousician for {song_title} by {artist_name}.")
                return chords
        chords_div = soup.find('div', class_='chords')
        if chords_div:
            chords = chords_div.get_text("\n", strip=True)
            if chords:
                logger.debug(f"Chords found on Yousician for {song_title} by {artist_name} (div.chords).")
                return chords
        logger.debug(f"Chords not found on Yousician for {song_title} by {artist_name}.")
        return "Chords not found."
    except Exception as e:
        logger.error(f"Error scraping Yousician for {song_title} by {artist_name}: {e}")
        return "Chords not found."

def get_chords_from_sources(song_title: str, artist_name: str):
    """
    Try all sources and flexible queries for chords.  Log which sources/queries were tried.

    Returns: (chords, source_name, tried_log)
    """
    tried_log: list[str] = []
    queries = [
        (artist_name, song_title),
        (strip_the(artist_name), song_title),
        (artist_name, strip_punct(song_title)),
        (strip_the(artist_name), strip_punct(song_title)),
        (artist_name.split(',')[0], song_title),  # Try just the main artist
    ]
    sources = [
        ("Chordie", get_chords_from_chordie),
        ("Ultimate Guitar", get_chords_from_ultimate_guitar),
        ("E‑Chords", get_chords_from_echords),
        ("Songsterr", get_chords_from_songsterr),
        ("Yousician", get_chords_from_yousician),
    ]
    for artist, title in queries:
        for source_name, fetch_func in sources:
            try:
                chords = fetch_func(title, artist)
                tried_log.append(f"{source_name} ({artist} – {title})")
                if chords and isinstance(chords, str) and chords.lower() not in ["chords not found.", "", None]:
                    logger.info(f"Chords found for {artist} – {title} from {source_name}")
                    return chords, source_name, tried_log
            except Exception as e:
                logger.error(f"Error with {source_name} for {artist} – {title}: {e}")
    logger.info(f"Chords not found for {artist_name} – {song_title} after trying all sources/queries.")
    return "Chords not found.", None, tried_log