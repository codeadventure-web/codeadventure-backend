import requests
from django.conf import settings
from urllib.parse import urlencode

def get_google_auth_url():
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

def google_get_access_token(code):
    data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
    }
    response = requests.post("https://oauth2.googleapis.com/token", data=data)
    response.raise_for_status()
    return response.json()

def get_github_auth_url():
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
        "scope": "user:email",
    }
    return f"https://github.com/login/oauth/authorize?{urlencode(params)}"

def github_get_access_token(code):
    data = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
    }
    response = requests.post(
        "https://github.com/login/oauth/access_token",
        data=data,
        headers={"Accept": "application/json"},
    )
    response.raise_for_status()
    return response.json()
