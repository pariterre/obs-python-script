from typing import Callable


class PomodoroCallbacks:
    has_connected_callback: Callable
    disconnect_user_callback: Callable
    score_update_callback: Callable

    def __init__(self, has_connected, has_disconnected, score_update):
        self.has_connected_callback = has_connected
        self.disconnect_user_callback = has_disconnected
        self.score_update_callback = score_update
