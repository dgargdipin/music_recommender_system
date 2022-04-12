import enum
import json
from flask import Flask, request, redirect, g, render_template
import requests
from urllib.parse import quote
import dotenv
import os
from recommender import getPandasFrame, recommend_songs
# Authentication Steps, paramaters, and responses are defined at https://developer.spotify.com/web-api/authorization-guide/
# Visit this url to see all the steps, parameters, and expected response.


app = Flask(__name__)
dotenv.load_dotenv()
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)
user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
# Server-side Parameters
CLIENT_SIDE_URL = "http://127.0.0.1"
PORT = 8080
REDIRECT_URI = "{}:{}/callback/q".format(CLIENT_SIDE_URL, PORT)
SCOPE = "user-top-read user-read-email user-read-private"
STATE = ""
# SHOW_DIALOG_bool = True
# SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()

auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    "client_id": CLIENT_ID,
}
class Timerange(enum.Enum):
    LONG_TERM="long_term"
    MEDIUM_TERM="medium_term"
    SHORT_TERM="short_term"


def get_profile_data(auth_headers):
    profile_response = requests.get(user_profile_api_endpoint, headers=auth_headers)

    print(profile_response.text)
    return json.loads(profile_response.text)
def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def get_track_info(song_list,auth_headers):
    
    chunked_list=list(chunks(song_list,50))
    song_data=[]
    for song_list in chunked_list:
        song_id_list = ""
        print("Getting song info of ",len(song_list))
        for song in song_list:
            song_id_list += song["id"] + ","
        feature_url = "{}/tracks".format(SPOTIFY_API_URL)
        print("Song ids",song_id_list)
        query_param = {"ids": song_id_list[:-1]}
        response = requests.get(feature_url, headers=auth_headers, params=query_param)
        print(response.text)
        feature_data = json.loads(response.text)
        song_data.append(feature_data)
        
        # print(feature_data)
    print(song_data)
    with open("rec_song_data.json", "w") as f:
            json.dump(song_data, f)
    return song_data

def get_audio_features(song_list, auth_headers):
    song_id_list = ""
    for song in song_list:
        song_id_list += song["id"] + ","
    feature_url = "{}/audio-features".format(SPOTIFY_API_URL)
    query_param = {"ids": song_id_list[:-1]}
    response = requests.get(feature_url, headers=auth_headers, params=query_param)
    feature_data = json.loads(response.text)
    return feature_data["audio_features"]

def parse_year(year):
    return int(year[:4])
def get_top_songs(auth_headers,timerange=Timerange.LONG_TERM):
    top_songs_url = "{}/top/tracks".format(user_profile_api_endpoint)
    query_params = {"time_range": timerange.value}

    songs_response = requests.get(
        top_songs_url, headers=auth_headers, params=query_params
    )
    song_response_dict = json.loads(songs_response.text)
    response_list = []
    list_of_ids = []
    with open("data_song.json", "w") as f:
        json.dump(song_response_dict, f)
    for song_item in song_response_dict["items"]:
        # print(song_item)
        song_id = song_item["id"]
        song_name = song_item["name"]
        artist_object = song_item["artists"][0]
        artist_name = artist_object["name"]
        track_url = song_item["external_urls"]["spotify"]
        year=parse_year(song_item["album"]["release_date"])
        popularity=song_item["popularity"]
        explicit=int(song_item["explicit"])
        song_dict = {
            "id": song_id,
            "song_name": song_name,
            "artist_name": artist_name,
            "track_url": track_url,
            "year":year,
            "popularity":popularity,
            "explicit":explicit
        }
        list_of_ids.append(song_id)
        response_list.append(song_dict)

    top_songs_stats = get_audio_features(response_list, auth_headers)
    for response_obj, top_song in zip(response_list, top_songs_stats):
        response_obj.update(top_song)
    with open("data_feature.json", "w") as f:
        json.dump(response_list, f)
    # print(response_list)
    with open('response_list','w') as f:
        f.write(str(type(response_list)))
        f.write(str(response_list))
    
    return response_list


@app.route("/")
def index():
    # Auth Step 1: Authorization
    url_args = "&".join(
        ["{}={}".format(key, quote(val)) for key, val in auth_query_parameters.items()]
    )
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    print("Redirecting to auth url")
    return redirect(auth_url)


@app.route("/callback/q")
def callback():
    # Auth Step 4: Requests refresh and access tokens
    auth_token = request.args["code"]
    # print("auth_token", auth_token)
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload)

    # Auth Step 5: Tokens are Returned to Application
    response_data = json.loads(post_request.text)
    try:
        access_token = response_data["access_token"]
        refresh_token = response_data["refresh_token"]
        token_type = response_data["token_type"]
        expires_in = response_data["expires_in"]
    except:
        # print(response_data)
        return "Not found", 400

    # Auth Step 6: Use the access token to access Spotify API
    authorization_header = {"Authorization": "Bearer {}".format(access_token)}
    print(access_token)
    # Get profile data
    profile_data = get_profile_data(auth_headers=authorization_header)
    top_songs = get_top_songs(auth_headers=authorization_header)
    
    with open("data.json", "w") as f:
        json.dump(top_songs, f)
    rec_songs=recommend_songs(top_songs)
    rec_song_data=get_track_info(rec_songs,auth_headers=authorization_header)
    # Combine profile and playlist data to display
    return render_template("index.html", profile=profile_data,songs=rec_song_data[0]["tracks"])


if __name__ == "__main__":
    app.run(debug=True, port=PORT)
