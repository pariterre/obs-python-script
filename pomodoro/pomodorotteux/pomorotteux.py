import time
from typing import Callable
import os
import socket
import re
import _thread
import pickle

from .configuration import TwitchConfigurationInternal


class Pomodorotteux:
    _config: TwitchConfigurationInternal

    _ping_time: float
    _has_connected_callback: Callable
    _disconnect_user_callback: Callable
    _score_update_callback: Callable
    _irc_socket: socket
    _connexion_initialized: bool = False

    number_tomatoes_done: dict
    _connected_users: dict

    def __init__(
        self,
        config: TwitchConfigurationInternal,
        has_connected_callback: Callable,
        disconnect_user_callback: Callable,
        score_update_callback: Callable,
        ping_time: float = -1,
    ):
        self._config = config

        # If this should be completely ignored or not
        self._keep_twitch_connection_alive = True
        self._ping_time = ping_time
        if self._ping_time > 0:
            _thread.start_new_thread(self._ping_connected_users, ())
        self._has_connected_callback = has_connected_callback
        self._disconnect_user_callback = disconnect_user_callback
        self._score_update_callback = score_update_callback

        # Database information
        self._connected_users = {}
        self._read_database()
        self._score_update_callback(self.number_tomatoes_done, self._connected_users)

        # Twitch information
        self._twitch_irc_connection()

    def __del__(self):
        self._irc_send_data(f"PART {self._config.channel_name}")

    def add_tomato_to_connected_users(self):
        for name in self._connected_users:
            self.number_tomatoes_done[name] += 1

        self._score_update_callback(self.number_tomatoes_done, self._connected_users)
        self.save_database()

    def end_session(self):
        self._connected_users = {}
        self._irc_send_data(f"PART {self._config.channel_name}")
        self._keep_twitch_connection_alive = False

    def clear_database(self):
        self.number_tomatoes_done = {}

    def post_message(self, message):
        self._irc_send_data(f"PRIVMSG #{self._config.channel_name} :{message}")

    def _ping_connected_users(self):
        while self._keep_twitch_connection_alive:
            time.sleep(60)
            current_time = time.time()
            for user in list(self._connected_users.keys()):
                if current_time - self._connected_users[user] > self._ping_time:
                    del self._connected_users[user]
                    self._disconnect_user_callback(user)

    def _connect_user(self, name):
        # Set the time for the user to now
        self._connected_users[name] = time.time()

        if name not in self.number_tomatoes_done:
            self.number_tomatoes_done[name] = 0
        self._has_connected_callback(name, self.number_tomatoes_done)
        self._score_update_callback(self.number_tomatoes_done, self._connected_users)

        self.save_database()

    def _read_database(self):
        dir_path = os.path.dirname(self._config.database_path)
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

        if not os.path.exists(self._config.database_path):
            self.number_tomatoes_done = {}
            return

        with open(self._config.database_path, "rb") as file:
            self.number_tomatoes_done = pickle.load(file)

        # Do a backup of the database just to make sure
        with open(self._config.database_path + ".bak", "wb") as file:
            pickle.dump(self.number_tomatoes_done, file)

    def save_database(self):
        with open(self._config.database_path, "wb") as file:
            pickle.dump(self.number_tomatoes_done, file)

    def _irc_send_data(self, command):
        if self._connexion_initialized and self._keep_twitch_connection_alive:
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
                    self._connect_user(sender_name)

    def __str__(self):
        return str(self.number_tomatoes_done)
