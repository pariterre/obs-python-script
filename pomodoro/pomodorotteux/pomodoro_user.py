import os
import pickle
import time
from typing import Union
from copy import deepcopy

from .configuration import TwitchConfigurationInternal
from .pomodoro_callbacks import PomodoroCallbacks


class PomodoroUser:
    pseudo: str
    is_connected: bool
    initial_number_of_tomatoes: int
    number_of_tomato_done: int
    last_time_interacted: float

    def __init__(self, _pseudo: str = "", _initial_number_of_tomatoes: int = 0):
        self.pseudo = _pseudo
        self.initial_number_of_tomatoes = _initial_number_of_tomatoes

        self.is_connected = False
        self.number_of_tomato_done = 0
        self.last_time_interacted = time.time()

    @property
    def total_number_of_tomatoes(self):
        return self.initial_number_of_tomatoes + self.number_of_tomato_done

    def compile_tomatoes(self):
        self.initial_number_of_tomatoes += self.number_of_tomato_done
        self.number_of_tomato_done = 0

    def disconnect(self):
        self.is_connected = False
        self.last_time_interacted = 0


class PomodoroUsers:
    _users: dict

    def __init__(self):
        self._users = {}

    @staticmethod
    def load_database(config: TwitchConfigurationInternal, callbacks: PomodoroCallbacks):
        dir_path = os.path.dirname(config.database_path)
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

        if not os.path.exists(config.database_path):
            # Create a new database
            output = PomodoroUsers()
        else:
            with open(config.database_path, "rb") as file:
                # Load an existing database
                output = PomodoroUsers()
                output._users = pickle.load(file)
                for user in output._users:
                    output._users[user].disconnect()
        callbacks.score_update_callback(output._users)

        # Do a backup of the database just to make sure
        output.save_database(config, False)
        return output

    def save_database(self, config: TwitchConfigurationInternal, is_backup: bool = False):
        # Move the tomato from done today to initial
        users = deepcopy(self._users)
        for user in users:
            users[user].compile_tomatoes()
            users[user].disconnect()

        database_path = config.database_path + (".bak" if is_backup else "")
        with open(database_path, "wb") as file:
            pickle.dump(users, file)

    def declare_user_interaction(self, name, config: TwitchConfigurationInternal, callbacks: PomodoroCallbacks):
        if name not in list(self._users.keys()):
            self._users[name] = PomodoroUser(_pseudo=name)

        if not self._users[name].is_connected:
            self._users[name].is_connected = True
            callbacks.has_connected_callback(name, self._users)
            callbacks.score_update_callback(self._users)
            self.save_database(config)

        self._users[name].last_time_interacted = time.time()

    def add_tomato_to_connected_users(self, config: TwitchConfigurationInternal, callbacks: PomodoroCallbacks):
        for name in list(self._users):
            if self._users[name].is_connected:
                self._users[name].number_of_tomato_done += 1

        callbacks.score_update_callback(self._users)
        self.save_database(config)

    def check_if_users_are_alive(self, max_ping_time: float, callbacks: PomodoroCallbacks):
        current_time = time.time()
        for name in self._users:
            if not self._users[name].is_connected:
                continue
            if current_time - self._users[name].last_time_interacted > max_ping_time:
                self.disconnect_user(name, callbacks)

    def disconnect_user(self, name, callbacks: Union[PomodoroCallbacks, None]):
        if not self._users[name].is_connected:
            return

        self._users[name].disconnect()
        if callbacks is not None:
            callbacks.disconnect_user_callback(name, self._users)

    def disconnect_all_users(self):
        for name in self._users:
            self.disconnect_user(name, None)

    def clear_database(self):
        self._users = {}

    def __str__(self):
        return str(self._users)
