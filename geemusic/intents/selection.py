from flask_ask import statement, audio
from os import environ
from geemusic import ask, app, queue
from geemusic.utils.music import GMusicWrapper
from geemusic.utils.mappings import MAPPINGS
from fuzzywuzzy import fuzz

@ask.intent("GeeMusicPlayArtistIntent")
def play_artist(artist_name):
    api = GMusicWrapper.generate_api()

    app.logger.debug("Fetching artist: %s" % artist_name)
    request_name = artist_name.lower().replace(" ", "")
    artist_name = MAPPINGS.get(request_name, artist_name)
    app.logger.debug("Fetching artist after mapping %s" % artist_name)
    # Fetch the artist
    artist = api.get_artist(artist_name, includeTracks=True)

    if artist == False:
        return statement("Sorry, I couldn't find that artist")

    # Setup the queue
    first_song_id = queue.reset(artist['topTracks'])

    # Get a streaming URL for the top song
    stream_url = api.get_stream_url(first_song_id)

    speech_text = "Playing top tracks from %s" % artist['name']
    return audio(speech_text).play(stream_url)

@ask.intent("GeeMusicPlayAlbumIntent")
def play_album(album_name, artist_name):
    api = GMusicWrapper.generate_api()

    app.logger.debug("Fetching album %s by %s" % (album_name, artist_name))

    # Fetch the album
    album = api.get_album(album_name, artist_name=artist_name)

    if album == False:
        return statement("Sorry, I couldn't find that album")

    # Setup the queue
    first_song_id = queue.reset(album['tracks'])

    # Start streaming the first track
    stream_url = api.get_stream_url(first_song_id)

    speech_text = "Playing album %s by %s" % (album['name'], album['albumArtist'])
    return audio(speech_text).play(stream_url)

@ask.intent("GeeMusicPlaySongIntent")
def play_song(song_name, artist_name):
    api = GMusicWrapper.generate_api()
    queue.reset()

    app.logger.debug("Fetching song %s by %s" % (song_name, artist_name))

    # Fetch the song
    song = api.get_song(song_name, artist_name=artist_name)

    if song == False:
        return statement("Sorry, I couldn't find that song")

    # Start streaming the first track
    stream_url = api.get_stream_url(song['storeId'])

    speech_text = "Playing song %s by %s" % (song['title'], song['artist'])
    return audio(speech_text).play(stream_url)

@ask.intent("GeeMusicPlayArtistRadioIntent")
def play_artist_radio(artist_name):
    api = GMusicWrapper.generate_api()
    request_name = artist_name.lower().replace(" ", "")
    artist_name = MAPPINGS.get(request_name, artist_name)
    app.logger.debug("Looking for radio stations for [%s]" % (artist_name))

    # Fetch the artist
    artist = api.get_artist(artist_name, includeTracks=False)

    if artist == False:
        app.logger.debug("Cannot find artist: %s. Looking for station." % artist_name)
        ## Look for station
        artist = api.search_station(artist_name, 'artist')
        if not artist:
            return statement("Sorry, I couldn't find artist %s." % (artist_name))

    station_id = api.get_station("%s Radio" % artist['name'], artist_id=artist['artistId'])
    # TODO: Handle track duplicates
    tracks = api.get_station_tracks(station_id)

    first_song_id = queue.reset(tracks)

    # Get a streaming URL for the top song
    stream_url = api.get_stream_url(first_song_id)

    speech_text = "Playing %s radio" % artist['name']
    return audio(speech_text).play(stream_url)

@ask.intent("GeeMusicPlayPlaylistIntent")
def play_playlist(playlist_name):
    app.logger.debug("Fetching playlist %s" % playlist_name)
    request_name = playlist_name.lower().replace(" ", "")
    playlist_name = MAPPINGS.get(request_name, playlist_name)
    app.logger.debug("Fetching playlist after mapping %s" % playlist_name)
    api = GMusicWrapper.generate_api()

    # Retreve the content of all playlists in a users library
    all_playlists = api.get_all_user_playlist_contents()
    app.logger.debug("Found %d playlists. [%s]" % (len(all_playlists), [ x['name'] for x in all_playlists ]))

    # Give each playlist a score based on its similarity to the requested 
    # playlist name
    request_name = playlist_name.lower().replace(" ", "")
    scored_playlists = []
    for i, playlist in enumerate(all_playlists):
        name = playlist['name'].lower().replace(" ", "")
        scored_playlists.append({
            'index': i,
            'name': name,
            'score': fuzz.ratio(name, request_name)
        })

    sorted_playlists = sorted(scored_playlists, lambda a, b: b['score'] - a['score'])
    top_scoring = sorted_playlists[0]
    best_match = all_playlists[top_scoring['index']]

    app.logger.debug("Top score: [%s, %s]" % (top_scoring['score'], best_match['name']))
    # Make sure we have a decent match (the score is n where 0 <= n <= 100)
    if top_scoring['score'] < 50:
        return statement("Sorry, I couldn't find that playlist in your library.")

    # Add songs from the playlist onto our queue
    app.logger.debug("Added %d tracks from playlist: %s" % (len(best_match['tracks']), best_match['name']))
    first_song_id = queue.reset(best_match['tracks'])

    # Get a streaming URL for the first song in the playlist
    stream_url = api.get_stream_url(first_song_id)
    app.logger.debug("Stream url: %s" % stream_url)

    speech_text = "Playing songs from %s" % (best_match['name'])
    return audio(speech_text).play(stream_url) \
        .simple_card(title="Gee Music",
                     content=speech_text)

@ask.intent("GeeMusicPlayIFLRadioIntent")
def play_artist_radio(artist_name):
    api = GMusicWrapper.generate_api()
    # TODO: Handle track duplicates?
    tracks = api.get_station_tracks("IFL")

    # Get a streaming URL for the first song
    first_song_id = queue.reset(tracks)
    stream_url = api.get_stream_url(first_song_id)

    speech_text = "Playing music from your personalized station"
    return audio(speech_text).play(stream_url)
