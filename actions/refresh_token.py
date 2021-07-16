import datetime
import requests

class Refresh:

    def __init__(self):
        self.access_token = ''
        self.refresh_token = '****'
        self.base_64 = '****'
        self.access_token_expires = datetime.datetime.now()

    def refresh(self):
        query = "https://accounts.spotify.com/api/token"
        response = requests.post(query,
                                 data={"grant_type": "refresh_token",
                                       "refresh_token": self.refresh_token},
                                 headers={"Authorization": "Basic " + self.base_64})

        response_json = response.json()
        now = datetime.datetime.now()
        expires_in = response_json['expires_in']
        self.access_token_expires = datetime.timedelta(seconds=expires_in) + now
        self.access_token = response_json['access_token']
        return self.access_token

    def get_access_token(self):
        now = datetime.datetime.now()
        if self.access_token_expires < now:
            return self.refresh()
        return self.access_token

