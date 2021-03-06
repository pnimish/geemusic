from os import environ
from gmusicapi import Mobileclient
from flask import current_app

class GMusicWrapper:
    def __init__(self, username, password):
        self._api = Mobileclient()
        success = self._api.login(username, password, Mobileclient.FROM_MAC_ADDRESS)

        if not success:
            raise Exception("Unsuccessful login. Aborting!")

    def _search(self, query_type, query):
        results = self._api.search(query)
        hits_key = "%s_hits" % query_type

        if hits_key not in results:
            return []

        # Ugh, Google had to make this schema nonstandard...
        if query_type == 'song':
            query_type = 'track'

        return map(lambda x: x[query_type], results[hits_key])

    def search_playlist(self, name):
        search = self._search("playlist", name)
        if len(search) == 0:
            return False
        
        tracks = self._api.get_shared_playlist_contents(search[0]['shareToken'])
        return tracks

    def get_artist(self, name, includeTracks=False):
        search = self._search("artist", name)

        if len(search) == 0:
            return False

        max_top_tracks = 100 if includeTracks else 1
        return self._api.get_artist_info(search[0]['artistId'], max_top_tracks=max_top_tracks)

    def search_station(self, name, seed_type=None):
        search = self._search("station", name)
        current_app.logger.debug("Found %d stations for %s" % (len(search), name))
        if not search:
            return False
        for station in search:
            #current_app.logger.debug("Station: %s" % station)
            artistId = station.get('seed', {}).get('artistId')
            if artistId:
                break
        current_app.logger.debug("Found artistId: %s" % artistId)
        if not artistId:
            return False
        return self._api.get_artist_info(artistId, max_top_tracks=1)

    def get_album(self, name, artist_name=None):
        if artist_name:
            name = "%s %s" % (name, artist_name)

        search = self._search("album", name)

        if len(search) == 0:
            return False

        return self._api.get_album_info(search[0]['albumId'])

    def get_song(self, name, artist_name=None):
        if artist_name:
            name = "%s %s" % (artist_name, name)

        search = self._search("song", name)

        if len(search) == 0:
            return False

        return search[0]

    def get_station(self, title, artist_id=None):
        if artist_id != None:
            return self._api.create_station(title, artist_id=artist_id)

    def get_station_tracks(self, station_id):
        return self._api.get_station_tracks(station_id)

    def get_google_stream_url(self, song_id):
        return self._api.get_stream_url(song_id)

    def get_stream_url(self, song_id):
        return "%s/stream/%s" % (environ['APP_URL'], song_id)

    def get_all_user_playlist_contents(self):
        return self._api.get_all_user_playlist_contents()

    @classmethod
    def generate_api(self):
        return self(environ['GOOGLE_EMAIL'], environ['GOOGLE_PASSWORD'])
