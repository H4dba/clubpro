import secrets
import base64
import hashlib
from django.conf import settings
import requests

class LichessOAuth:
    def __init__(self):
        self.client_id = settings.LICHESS_CLIENT_ID
        self.redirect_uri = settings.LICHESS_REDIRECT_URI

    def generate_code_verifier(self):
        # Generate a random code verifier
        code_verifier = secrets.token_urlsafe(64)
        return code_verifier[:128]  # Truncate to maximum 128 characters

    def generate_code_challenge(self, code_verifier):
        # Create code challenge using SHA256
        code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8')
        return code_challenge.rstrip('=')  # Remove padding

    def get_authorization_url(self, request):
        # Generate and store PKCE values in session
        code_verifier = self.generate_code_verifier()
        code_challenge = self.generate_code_challenge(code_verifier)
        
        # Store the code verifier in session for later use
        request.session['code_verifier'] = code_verifier
        
        # Build authorization URL with PKCE
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'scope': 'preference:read email:read challenge:read challenge:write puzzle:read'
        }
        
        query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        return f"https://lichess.org/oauth?{query_string}"

    def get_access_token(self, request, code):
        # Get stored code verifier from session
        code_verifier = request.session.get('code_verifier')
        if not code_verifier:
            raise ValueError("Code verifier not found in session")

        # Exchange code for token using code verifier
        response = requests.post(
            'https://lichess.org/api/token',
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'client_id': self.client_id,
                'code_verifier': code_verifier,
                'redirect_uri': self.redirect_uri,
            }
        )
        
        # Clean up session
        del request.session['code_verifier']
        
        if response.status_code != 200:
            raise Exception(f"Token exchange failed: {response.text}")
            
        return response.json().get('access_token') 