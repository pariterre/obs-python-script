from pathlib import Path
from dataclasses import dataclass
import json


@dataclass
class TwitchConfigurationInternal:
    nickname: str
    channel_name: str
    database_path: str
    oauth_key: str = None
    irc_server_address: str = "irc.chat.twitch.tv"
    irc_port: int = 6667

    def __post_init__(self):
        if self.nickname is None:
            self.nickname = self.channel_name

        if self.oauth_key is None:
            raise ConnectionError(
                "No 'oauth_key 'provided, please generate one using the following link\n"
                "Visit: https://twitchapps.com/tmi/#access_token=7ld7okcsiozvkrcjdwt3z9y31ajrzk&"
                "scope=chat%3Aread+chat%3Aedit+channel%3Amoderate+whispers%3Aread+whispers%3Aedit+"
                "channel_editor&token_type=bearer"
            )

        self.oauth_key = self.oauth_key if self.oauth_key[:6] == "oauth:" else "oauth:" + self.oauth_key


class TwitchConfiguration:
    @staticmethod
    def generate_file(
        path: str,
        channel_name: str,
        nickname: str = None,
        database_path: str = None,
        oauth_key: str = None,
    ):
        if database_path is None:
            database_path = str(Path.home()) + "/.config/Pomodoro/database.pomo"

        config = TwitchConfigurationInternal(nickname, channel_name, database_path, oauth_key)
        with open(path, "w") as f:
            json.dump(config.__dict__, f, indent=2)

    @staticmethod
    def load_configuration(path: str) -> TwitchConfigurationInternal:
        with open(path, "r") as f:
            return TwitchConfigurationInternal(**json.load(f))
