import time

from pomodorotteux import Pomodorotteux, TwitchConfiguration, PomodoroCallbacks


def main():
    def has_connected_callback(name: str, users: dict):
        if users[name].initial_number_of_tomatoes == 0:
            pomo.post_message(
                f"Message de la tomate : {name} s'est connecté(e) pour la première fois! Bienvenue parmi nous!"
            )
        else:
            pomo.post_message(f"Message de la tomate : {name} s'est connecté(e) aux tomates!")

    def disconnect_user_callback(name: str, users: dict):
        pomo.post_message(f"Message de la tomate : {name} a été bien silencieux(se)! Tu es toujours là?")

    def score_callback(users: dict):
        for name in users:
            print(f"{users[name].pseudo} a fait : {users[name].number_of_tomato_done} "
                  f"pour un total de {users[name].total_number_of_tomatoes}")
        print(f"Total de tomates aujourd'hui: {sum(users[name].number_of_tomato_done for name in users)}")
        print("")

    pomo = Pomodorotteux(
        config=TwitchConfiguration.load_configuration("my_config_file.key"),
        callbacks=PomodoroCallbacks(has_connected_callback, disconnect_user_callback, score_callback),
        ping_time=60*60,
    )

    # Simulate someone who is posting a message to the chat to connect
    pomo._users.declare_user_interaction("tata", pomo._config, pomo._callbacks)
    pomo._users.disconnect_user("tata", pomo._callbacks)

    try:
        while True:
            time.sleep(3)
            print("Tomate faite!")
            pomo.add_tomato_to_connected_users()
            break
    finally:
        # Ensure for proper disconnection from the IRC server
        pomo.end_session()
        pomo.save_database()


if __name__ == "__main__":
    main()
