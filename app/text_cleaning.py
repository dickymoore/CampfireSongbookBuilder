import re

def remove_contributors_and_embeds(lyrics):
    """Remove the Contributors, Embed sections, and unwanted advertisements from the lyrics."""
    lyrics = re.sub(r'^.*Contributors', '', lyrics, flags=re.DOTALL)
    lyrics = re.sub(r'Embed\s*$', '', lyrics, flags=re.MULTILINE)
    return lyrics

def remove_unwanted_phrases(lyrics):
    """Remove unwanted phrases and advertisements from the lyrics without removing the entire line."""
    patterns_to_remove = [
        r'You might also like.*?',
        r'See .*? LiveGet tickets as low as \$\d+',
        r'.*? Lyrics'
    ]
    
    # Remove each pattern, but only the matched part, not the entire line
    for pattern in patterns_to_remove:
        lyrics = re.sub(pattern, '', lyrics, flags=re.MULTILINE)
    
    return lyrics

def clean_lyrics(lyrics):
    """Clean the lyrics by removing contributors, embeds, and unwanted phrases."""
    lyrics = remove_contributors_and_embeds(lyrics)
    lyrics = remove_unwanted_phrases(lyrics)
    return lyrics
