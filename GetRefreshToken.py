import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
import os

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

scope = "playlist-modify-public playlist-modify-private"

auth_manager = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=scope
)

sp = spotipy.Spotify(auth_manager=auth_manager)

# Retrieve and print the refresh token
token_info = auth_manager.get_cached_token()

if token_info:
    print(f"✅ Access Token: {token_info['access_token']}")
    print(f"✅ Refresh Token: {token_info['refresh_token']}")  # Make sure this gets printed!
else:
    print("❌ No token found. Try re-authorizing the app.")