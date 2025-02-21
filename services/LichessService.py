import berserk
import os
from typing import Optional, Dict, Any

class LichessApi:
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.session = berserk.TokenSession(token)
        self.client = berserk.Client(session=self.session)

    def get_user_info(self, username: str) -> Dict[str, Any]:
        try:
            return self.client.users.get_by_id(username)
        except Exception as e:
            print(f"Error fetching user info: {e}")
            return None

    def get_user_games(self, username: str, max_games: int = 10):
        try:
            return self.client.games.export_by_player(username, max=max_games)
        except Exception as e:
            print(f"Error fetching games: {e}")
            return []

    def get_user_current_games(self, username: str):
        try:
            return self.client.games.get_ongoing(username)
        except Exception as e:
            print(f"Error fetching current games: {e}")
            return []

    def get_tournament_results(self, username: str):
        try:
            return self.client.tournaments.get_results(username)
        except Exception as e:
            print(f"Error fetching tournament results: {e}")
            return []