import berserk
import os
from dotenv import load_dotenv

load_dotenv()

import base64
import hashlib
import secrets
import requests
from django.conf import settings
from django.urls import reverse

LICHESS_OAUTH_URL = "https://lichess.org/oauth"
LICHESS_TOKEN_URL = "https://lichess.org/api/token"
SCOPES = ["email:read"]
CLIENT_ID = "https://c737-179-125-52-238.ngrok-free.app"  # Change this to your domain


class LichessApi:
    def __init__(self):
        self.token = os.getenv('LICHESS_API_TOKEN')
        self.session = berserk.TokenSession(self.token)
        self.client = berserk.Client(session=self.session)

    def get_user_info(self, username):
        try:
            return self.client.users.get_public_data(username)
        except Exception as e:
            print(f"Erro ao pegar dado de usuario: {e}")
            return None
class LichessOAuth:
    @staticmethod
    def generate_code_verifier():
        """Generate a secure code_verifier"""
        code_verifier = secrets.token_urlsafe(64)
        return code_verifier

    @staticmethod
    def get_redirect_uri():
        """Dynamically generate the redirect URI to avoid circular import issues."""
        return CLIENT_ID + reverse("lichess_callback")

    @staticmethod
    def generate_code_challenge(code_verifier):
        """Create a code_challenge from the code_verifier"""
        sha256 = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        code_challenge = base64.urlsafe_b64encode(sha256).decode("utf-8").rstrip("=")
        return code_challenge

    @staticmethod
    def generate_state():
        """Generate a random state string for CSRF protection"""
        return secrets.token_urlsafe(16)

    @staticmethod
    def get_authorization_url(request):
        """Step 1: Generate OAuth URL and store state + code_verifier in session"""
        code_verifier = LichessOAuth.generate_code_verifier()
        code_challenge = LichessOAuth.generate_code_challenge(code_verifier)
        state = LichessOAuth.generate_state()

        # Store in session for later verification
        request.session["lichess_code_verifier"] = code_verifier
        request.session["lichess_state"] = state

        params = {
            "response_type": "code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "scope": " ".join(SCOPES),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        auth_url = f"{LICHESS_OAUTH_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
        return auth_url

    @staticmethod
    def exchange_code_for_token(request, code, state):
        """Step 2: Exchange authorization code for access token"""
        stored_state = request.session.pop("lichess_state", None)
        code_verifier = request.session.pop("lichess_code_verifier", None)

        if not stored_state or stored_state != state:
            raise ValueError("State mismatch, potential CSRF attack!")

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "code_verifier": code_verifier,
        }

        response = requests.post(LICHESS_TOKEN_URL, data=data)
        token_data = response.json()

        if "access_token" not in token_data:
            raise ValueError("Failed to obtain access token: " + str(token_data))

        return token_data  # Contains access_token, expires_in, refresh_token (if applicable)

    @staticmethod
    def revoke_token(access_token):
        """Step 3: Revoke access token"""
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.delete(LICHESS_TOKEN_URL, headers=headers)

        return response.status_code == 200