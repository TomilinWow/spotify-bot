import requests
import json
from .refresh_token import Refresh
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

refresh = Refresh()

class ToolWorkMusic:
    """
    Class for getting device id, play music, search response
    """

    def __init__(self, token):
        self.spotify_token = token

    def get_device(self):
        """
        Method for getting the device id
        return: request response or id device
        """
        response = requests.get('https://api.spotify.com/v1/me/player/devices',
                                headers={"Authorization": "Bearer {}".format(self.spotify_token),
                                         "Content-Type": "application/json"})

        if response:
            if len(response.json()['devices']) > 0:
                id_device = response.json()['devices'][0]['id']
            else:
                id_device = response
            return id_device
        else:
            return response

    def play_music(self, id_device, uris, type_uris):
        """
        Music playback method
        id_device: Id of the current active device
        uris: path uri of the music
        type_uris: type of music uri - playlist or song
        return: response of request
        """
        request_body = json.dumps({
            type_uris: uris,
            "offset": {
                "position": 0
            },
            "position_ms": 0
        })

        # run track in your device
        query_play_music = 'https://api.spotify.com/v1/me/player/play?device_id={}'.format(id_device)
        response = requests.put(query_play_music,
                                data=request_body,
                                headers={"Authorization": "Bearer {}".format(self.spotify_token),
                                         "Content-Type": "application/json"})
        return response

    def play_content(self, content, type):
        """
        Сontent playback method
        content: path uri of the music
        type: type of music uri - playlist or song
        """
        # get id device
        id_device = self.get_device()
        if not id_device:
            return id_device
        # play song from your player
        return self.play_music(id_device, content, type)  # response

    def search_content(self, name, type):
        """
        Method of searching for content on Spotify
        name: name of content
        type: type of content
        return: request response
        """
        query_search_track = f'https://api.spotify.com/v1/search?q={name}&type={type}&limit=1'
        response = requests.get(query_search_track,
                                headers={"Authorization": "Bearer {}".format(self.spotify_token),
                                         "Content-Type": "application/json"})
        return response

    def get_errors(self, response):
        """
        Мethod that determines the chat-bot's response
        return: response for action-dispatcher
        """
        if response.status_code == 400:
            return 'utter_search_error'
        elif response.status_code == 403:
            return 'utter_spotify_premium_error'
        elif response.status_code == 404:
            return 'utter_spotify_no_active_error'
        else:
            return 'utter_enjoy_music'


class ActionPlayMusic(Action):
    """
    Class for search and playing music
    """

    def name(self):
        return "action_play_music"

    def get_track(self, json):
        """
        Method of getting the track
        json: result of request
        return: track-uri
        """
        try:
            tracks = [track for track in json['tracks']['items']]
            return tracks[0]['uri']
        except Exception:
            return False

    def play_track(self, json):
        """
        Track playback method
        """

        track = self.get_track(json)
        if not track:
            return 'utter_search_error'
        response = self.tools_work_music.play_content([track], "uris")  # 'uris' - type play for tracks
        return f"{self.tools_work_music.get_errors(response)}"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):

        self.spotify_token = refresh.get_access_token()

        # branch song-entity message
        if len(tracker.latest_message['entities']) == 0:
            dispatcher.utter_message(response='utter_clarify_error')
            return []

        entity = tracker.latest_message['entities'][0]
        dispatcher.utter_message(response="utter_second")
        # track from message
        track = tracker.latest_message['text'][entity['end']:].replace(' ', '', 1)
        self.tools_work_music = ToolWorkMusic(self.spotify_token)
        response = self.tools_work_music.search_content(track, 'track')
        if response:
            # search track
            response = self.play_track(response.json())
            dispatcher.utter_message(response=response)
        else:
            # search track second chance
            track = tracker.latest_message['text'][entity['start']:].replace(' ', '', 1)
            response = self.tools_work_music.search_content(track, 'track')
            if response:
                response = self.play_track(response.json())
                dispatcher.utter_message(response=response)
            else:
                dispatcher.utter_message(response=f"{self.tools_work_music.get_errors(response)}")
        return []


class ActionAddCurrentTrack(Action):
    """
    Class for adding the current track
    """
    def name(self):
        return "action_add_current_track"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):

        spotify_token = refresh.get_access_token()

        query_add_favourites = 'https://api.spotify.com/v1/me/player'
        response = requests.get(query_add_favourites,
                                headers={"Authorization": "Bearer {}".format(spotify_token),
                                         "Content-Type": "application/json"}, )
        try:
            current_song_player = response.json()['item']['id']
        except Exception:
            dispatcher.utter_message(text='Не включен плеер')
            return []

        dispatcher.utter_message(response="utter_second")
        query_favourites_songs = f'https://api.spotify.com/v1/me/tracks?ids={current_song_player}'
        response = requests.put(query_favourites_songs,
                                headers={"Authorization": "Bearer {}".format(spotify_token),
                                         "Content-Type": "application/json"})
        if response:
            dispatcher.utter_message(response="utter_add_track_ok")
        else:
            dispatcher.utter_message(response="utter_add_track_error")
        return []


class PlayPlaylist(Action):
    """
    Playlist playback class
    """
    def name(self):
        return "action_play_custom_playlist"

    def play_playlist(self, spotify_token, playlist):
        """
        Playlist playback method, in case of failure - music
        playlist: name of playlist
        """

        tools_work_music = ToolWorkMusic(spotify_token)
        response = tools_work_music.search_content(playlist, 'playlist')

        if response:
            if len(response.json()['playlists']['items']) > 0:
                playlist_uri = response.json()['playlists']['items'][0]['uri']
                response = tools_work_music.play_content(playlist_uri, 'context_uri')
                return f"{tools_work_music.get_errors(response)}"
            else:
                response = tools_work_music.search_content(playlist, 'track')
                if response:
                    if len(response.json()['tracks']['items']) > 0:
                        track_uri = response.json()['tracks']['items'][0]['uri']
                        response = tools_work_music.play_content([track_uri], "uris")
                        return f"{tools_work_music.get_errors(response)}"
                    else:
                        return 'utter_search_error'
        else:
            return f"{tools_work_music.get_errors(response)}"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):

        spotify_token = refresh.get_access_token()

        if len(tracker.latest_message['entities']) == 0:
            dispatcher.utter_message(response='utter_clarify_error')
            return []

        dispatcher.utter_message(response="utter_second")
        entity = tracker.latest_message['entities'][0]
        playlist = tracker.latest_message['text'][entity['end']:].replace(' ', '', 1)
        response = self.play_playlist(spotify_token, playlist)
        dispatcher.utter_message(response=response)

        return []


class GetCustomPlaylist(Action):
    """
    Search class for top playlists
    """
    def name(self):
        return "action_get_custom_playlist"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        spotify_token = refresh.get_access_token()
        query_get_features = 'https://api.spotify.com/v1/browse/featured-playlists?limit=5&country=RU'
        response = requests.get(query_get_features,
                                headers={"Authorization": "Bearer {}".format(spotify_token),
                                         "Content-Type": "application/json"})
        if response:
            playlists = [playlist for playlist in response.json()['playlists']['items']]

            dispatcher.utter_message(text="Есть следующие плейлисты:")
            for playlist in playlists:
                dispatcher.utter_message(playlist['name'])
            return [SlotSet('is_get_playlist', True)]
        else:
            dispatcher.utter_message(text=f'Ошибка {response.status_code}')


class ActionPlayContent(Action):
    """
    Audio Content Playback Class
    """
    def name(self):
        return "action_play_content"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        spotify_token = refresh.get_access_token()
        name_from_text = ''

        # it works in most cases
        for entity in tracker.latest_message['entities']:
            if entity['entity'] == 'name_content':
                name_from_text = tracker.latest_message['text'][entity['start']:]
                break

        if name_from_text == '':
            text = tracker.latest_message['text']
            name_from_text = ' '.join(text.split(' ')[1:])

        play_playlist = PlayPlaylist()
        response = play_playlist.play_playlist(spotify_token, name_from_text)
        dispatcher.utter_message(response=response)

        return []
