import berserk
import os
from dotenv import load_dotenv

load_dotenv()


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
