import lyricsgenius
import logging

# Configure logging
logger = logging.getLogger(__name__)

def get_genius_client(access_token):
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


# # Genius API endpoints
# access_token_url = 'https://api.genius.com/oauth/authorize'

# def get_access_token(website_url,client_id, client_secret):

#     genius = OAuth2Session(
#         client_id=client_id,
#         base_url='https://api.genius.com'
#     )
#     params = {
#     'redirect_uri': website_url,
#     'response_type': 'code',
#     'scope': 'me'
#     }
#     authorize_url = genius.get_authorize_url(**params)
#     print(f'Visit this URL to authorize the app: {authorize_url}')

#     authorization_code = input('Enter the authorization code from the redirect URL: ')
#     exit()
#     data = {
#         'code': authorization_code,
#         'redirect_uri': website_url,
#         'grant_type': 'authorization_code',
#         'client_id': client_id,
#         'client_secret': client_secret
#     }

#     response = requests.post('https://api.genius.com/oauth/token', data=data)
#     response_data = response.json()

#     # Extract the access token from the response
#     access_token = response_data['access_token']
#     print(f'Access Token: {access_token}')
#     headers = {
#         'Authorization': f'Bearer {access_token}'
#     }
#     user_response = requests.get('https://api.genius.com/account', headers=headers)
#     print(user_response.json())

#     # payload={
#     #     'genius_client_id' : client_id,
#     #     'genius_secret_id' : client_secret,
#     #     'redirect_uri': website_url,
#     #     'scope' : "me",
#     #     'state' : "SOME_STATE_VALUE",
#     #     'response_type' : "code"
#     # }
#     # logger.debug(f"Requesting access token: ")
#     # r = requests.get(access_token_url, params=payload)
#     # print(f"status_code: {r.status_code}") #200 is good
#     # print(f"_content_consumed: {r._content_consumed}")
#     # print(f"_next: {r._next}")
#     # print(f"headers: {r.headers}")
#     # print(f"raw: {r.raw}")
#     # print(f"url: {r.url}")
#     # print(f"encoding: {r.encoding}")
#     # print(f"history: {r.history}")
#     # print(f"reason: {r.reason}")
#     # print(f"cookies: {r.cookies}")
#     # print(f"elapsed: {r.elapsed}")
#     # print(f"request: {r.request}")
#     # print(f"connection: {r.connection}")

#     # exit()
    

#     # Create an OAuth2 session
#     oauth = OAuth2Session(client_id, redirect_uri=website_url)

#     # Redirect user to Genius for authorization
#     authorization_url, state = oauth.authorization_url(AUTHORIZATION_BASE_URL)
#     authorization_url, state = oauth.authorization_url(AUTHORIZATION_BASE_URL, state="random_state_string", response_type="code")

#     logger.info(f'Authorization Url: {authorization_url}')
#     logger.info(f'Please go to {authorization_url} and authorize access.')

#     # Get the authorization verifier code from the callback URL
#     redirect_response = input('Paste the full redirect URL here: ')

#     try:
#         # Fetch the access token
#         token = oauth.fetch_token(TOKEN_URL, authorization_response=redirect_response, client_secret=client_secret)
#         logger.debug("Access token received.")
#         return token['access_token']
#     except Exception as e:
#         logger.error(f"Error fetching access token: {e}")
#         raise

# def get_chords_from_ultimate_guitar(song_title, artist_name):
#     logger.debug(f"Searching for chords for {song_title} by {artist_name}...")
#     search_url = f"https://www.ultimate-guitar.com/search.php?search_type=title&value={song_title} {artist_name}"
#     try:
#         response = requests.get(search_url)
#         soup = BeautifulSoup(response.text, 'html.parser')
#         result = soup.find("a", class_="js-tp_link")
#         if result:
#             chords_url = result['href']
#             chords_response = requests.get(chords_url)
#             chords_soup = BeautifulSoup(chords_response.text, 'html.parser')
#             chords_div = chords_soup.find("pre", class_="js-tab-content")
#             chords = chords_div.get_text() if chords_div else "Chords not found."
#             logger.debug("Chords found.")
#             return chords
#         logger.debug("Chords not found.")
#         return "Chords not found."
#     except Exception as e:
#         logger.error(f"Error fetching chords: {e}")
#         return "Chords not found."

# def get_lyrics_from_genius(song_title, artist_name, access_token):
#     logger.debug(f"Searching for lyrics for {song_title} by {artist_name}...")
#     base_url = "https://api.genius.com"
#     headers = {'Authorization': f'Bearer {access_token}'}
#     search_url = f"{base_url}/search"
#     params = {'q': f"{song_title} {artist_name}"}
#     try:
#         response = requests.get(search_url, headers=headers, params=params)
#         response.raise_for_status()
        
#         json_response = response.json()
#         remote_song_info = None
#         for hit in json_response['response']['hits']:
#             if artist_name.lower() in hit['result']['primary_artist']['name'].lower():
#                 remote_song_info = hit
#                 break
        
#         if remote_song_info:
#             song_path = remote_song_info['result']['path']
#             song_url = f"https://genius.com{song_path}"
#             song_page = requests.get(song_url)
#             song_page_soup = BeautifulSoup(song_page.text, 'html.parser')
#             lyrics_div = song_page_soup.find("div", class_="lyrics")
#             if not lyrics_div:
#                 lyrics_div = song_page_soup.find("div", class_="SongPage__Section__Lyrics")
#             lyrics = lyrics_div.get_text() if lyrics_div else "Lyrics not found."
#             logger.debug("Lyrics found.")
#             return lyrics
#         logger.debug("Lyrics not found.")
#         return "Lyrics not found."
#     except Exception as e:
#         logger.error(f"Error fetching lyrics: {e}")
#         return "Lyrics not found."
