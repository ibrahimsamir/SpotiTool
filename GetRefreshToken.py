import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

from dotenv import load_dotenv

load_dotenv()

# Set your Spotify credentials (replace with your actual values)
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:9090"
SCOPE = "playlist-modify-public playlist-modify-private"

# Get token
auth_manager = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="playlist-modify-public playlist-modify-private"
)
sp = spotipy.Spotify(auth_manager=auth_manager)

token = sp.auth_manager.get_access_token(as_dict=False)

print(f"Your refresh token: {token}")