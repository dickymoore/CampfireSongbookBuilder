import requests
from bs4 import BeautifulSoup
import logging
from app.cache import cache_data, load_cache
import json
import re
import html
import time

# Configure logging
logger = logging.getLogger(__name__)

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
            return "Lyrics not found."
    except Exception as e:
        logger.error(f"Error fetching lyrics for {song_title} by {artist_name}: {e}")
        return "Lyrics not found."

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
        if script_tag:
            data_content = json.loads(script_tag["data-content"])
            search_results = data_content.get("store", {}).get("page", {}).get("data", {}).get("results", [])
            for result in search_results:
                if result["type"] == "Chords" and song_title.lower() in result["song_name"].lower() and artist_name.lower() in result["artist_name"].lower():
                    chords_page_url = result["tab_url"]
                    logger.debug(f"Chords page URL matched: {chords_page_url}")
                    break
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
                    data_content = chords_div['data-content']
                    decoded_data_content = html.unescape(data_content)
                    json_content = json.loads(decoded_data_content)
                    content_value = json_content['store']['page']['data']['tab_view']['wiki_tab']['content']

                    # Use content_value as the chords
                    chords = content_value
                    logger.debug(f"Chords found for {song_title} by {artist_name}.")
                    # Cache the chords
                    chords_cache[cache_key] = chords
                    cache_data('data/cache/chords_cache.json', chords_cache)  # Save with prettified JSON
                    return chords
                else:
                    logger.debug(f"Chords content not found in the page for {song_title} by {artist_name}.")
                    chords_cache[cache_key] = "Chords not found."
                    cache_data('data/cache/chords_cache.json', chords_cache)  # Save with prettified JSON
                    return "Chords not found."
            except Exception as e:
                logger.error(f"Error fetching chords for {song_title} by {artist_name}: {e}")
                chords_cache[cache_key] = "Chords not found."
                cache_data('data/cache/chords_cache.json', chords_cache)  # Save with prettified JSON
                return "Chords not found."
        else:
            logger.debug(f"Chords link not found in the search results for {song_title} by {artist_name}.")
            chords_cache[cache_key] = "Chords not found."
            cache_data('data/cache/chords_cache.json', chords_cache)  # Save with prettified JSON
            return "Chords not found."
    except Exception as e:
        logger.error(f"Error fetching chords for {song_title} by {artist_name}: {e}")
        chords_cache[cache_key] = "Chords not found."
        cache_data('data/cache/chords_cache.json', chords_cache)  # Save with prettified JSON
        return "Chords not found."
