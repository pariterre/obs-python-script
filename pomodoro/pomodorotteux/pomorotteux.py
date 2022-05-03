import time
import socket
import re
import _thread

from .configuration import TwitchConfigurationInternal
from .pomodoro_user import PomodoroUsers
from .pomodoro_callbacks import PomodoroCallbacks


class Pomodorotteux:
    _config: TwitchConfigurationInternal

    _ping_time: float
    _irc_socket: socket
    _connexion_initialized: bool = False

    _users: PomodoroUsers

    def __init__(
        self,
        config: TwitchConfigurationInternal,
        callbacks: PomodoroCallbacks,
        ping_time: float = -1,
    ):
        self._config = config

        # If this should be completely ignored or not
        self._keep_twitch_connection_alive = True
        self._ping_time = ping_time
        self._callbacks = callbacks

        # Database information
        self._users = PomodoroUsers.load_database(self._config, self._callbacks)

        # Twitch information
        self._twitch_irc_connection()

        if self._ping_time > 0:
            _thread.start_new_thread(self._ping_connected_users, ())

    def __del__(self):
        self._irc_send_data(f"PART {self._config.channel_name}")

    def save_database(self):
        self._users.save_database(self._config)

    def end_session(self):
        self._users.disconnect_all_users()
        self._keep_twitch_connection_alive = False
        self._irc_send_data(f"PART {self._config.channel_name}", bypass_keep_alive=True)

    def clear_database(self):
        self._users.clear_database()

    def post_message(self, message):
        self._irc_send_data(f"PRIVMSG #{self._config.channel_name} :{message}")

    def add_tomato_to_connected_users(self):
        self._users.add_tomato_to_connected_users(self._config, self._callbacks)

    def _ping_connected_users(self):
        while self._keep_twitch_connection_alive:
            time.sleep(60)
            self._users.check_if_users_are_alive(self._ping_time, self._callbacks)

    def _irc_send_data(self, command, bypass_keep_alive: bool = False):
        # The bypass is a kind of mutex
        if self._connexion_initialized and self._keep_twitch_connection_alive or bypass_keep_alive:
            self._irc_socket.send((command + "\n").encode())

    def _twitch_irc_connection(self):
        self._irc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._irc_socket.connect((self._config.irc_server_address, self._config.irc_port))
        self._connexion_initialized = True
        self._irc_send_data(f"PASS {self._config.oauth_key}")
        self._irc_send_data(f"NICK {self._config.nickname}")
        self._irc_send_data(f"JOIN #{self._config.channel_name}")

        _thread.start_new_thread(self._twitch_callback, ())

    def _twitch_callback(self):
        while self._keep_twitch_connection_alive:
            time.sleep(1)
            buffer = self._irc_socket.recv(2 ** 12)
            irc_messages = buffer.decode().split("\r\n")
            for irc_message in irc_messages:
                # Keep liaison alive
                if irc_message == "PING :tmi.twitch.tv":
                    self._irc_send_data("PONG :tmi.twitch.tv")
                    continue
                elif len(re.split(r"^.*(Login authentication failed).*$", irc_message)) == 3:
                    raise ConnectionError(
                        "Unable to connect to Twitch, need another OAuth key?\n"
                        "Visit: https://twitchapps.com/tmi/#access_token=7ld7okcsiozvkrcjdwt3z9y31ajrzk&"
                        "scope=chat%3Aread+chat%3Aedit+channel%3Amoderate+whispers%3Aread+whispers%3Aedit+"
                        "channel_editor&token_type=bearer"
                    )

                # If we get another irc_message, check if it is an actual message
                message_split = re.split(r"^:(.*)!.*@.*PRIVMSG.*#.*:(.*)$", irc_message)
                sender_name = None if len(message_split) != 4 else message_split[1]
                # message = None if len(message_split) != 4 else message_split[2]

                # If it is a message, register the user if needed
                if sender_name:
                    self._users.declare_user_interaction(sender_name, self._config, self._callbacks)

    def __str__(self):
        return str(self._users)
