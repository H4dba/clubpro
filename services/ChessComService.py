import requests
from typing import Optional, Dict, Any

API_BASE = 'https://api.chess.com/pub/player'
HEADERS = {
    'Accept': 'application/json',
    # Chess.com may return 403 when requests don't send a descriptive User-Agent.
    'User-Agent': 'AXM-ClubPro/1.0 (https://clubpro.local; contact: admin@clubpro.local)',
}


class ChessComApi:
    """Thin wrapper around the public Chess.com API (no auth required)."""

    @staticmethod
    def get_player_stats(username: str) -> Optional[Dict[str, Any]]:
        """GET /pub/player/{username}/stats"""
        try:
            resp = requests.get(f'{API_BASE}/{username}/stats', headers=HEADERS, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f'[ChessComApi] Error fetching stats for {username}: {e}')
            return None

    @staticmethod
    def get_player_profile(username: str) -> Optional[Dict[str, Any]]:
        """GET /pub/player/{username}"""
        try:
            resp = requests.get(f'{API_BASE}/{username}', headers=HEADERS, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f'[ChessComApi] Error fetching profile for {username}: {e}')
            return None

    @staticmethod
    def username_exists(username: str) -> bool:
        """Checks whether a Chess.com username exists."""
        try:
            # Primary check by profile endpoint.
            resp_profile = requests.get(f'{API_BASE}/{username}', headers=HEADERS, timeout=10)
            if resp_profile.status_code == 200:
                return True

            # Fallback by stats endpoint (some edge cases can differ).
            resp_stats = requests.get(f'{API_BASE}/{username}/stats', headers=HEADERS, timeout=10)
            return resp_stats.status_code == 200
        except requests.RequestException:
            return False
