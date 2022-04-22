import time

from pomodorotteux import Pomodorotteux, TwitchConfiguration


def main():
    def has_connected_callback(name: str, tomato_done: dict):
        if tomato_done[name] == 0:
            pomo.post_message(
                f"Message de la tomate : {name} s'est connecté(e) pour la première fois! Bienvenue parmi nous!"
            )
        else:
            pomo.post_message(f"Message de la tomate : {name} s'est connecté(e) aux tomates!")

    def disconnect_user_callback(name: str):
        pomo.post_message(f"Message de la tomate : {name} a été bien silencieux(se)! Tu es toujours là?")

    def score_callback(score: dict):
        print(score)

    pomo = Pomodorotteux(
        config=TwitchConfiguration.load_configuration("my_config_file.key"),
        has_connected_callback=has_connected_callback,
        disconnect_user_callback=disconnect_user_callback,
        score_update_callback=score_callback,
        ping_time=60*60,
    )
    pomo._connect_user("coucou")  # Simulate someone who is posting a message to the chat
    pomo.post_message("coucou3")

    try:
        while True:
            time.sleep(10)
            print("Tomate faite!")
            pomo.add_tomato_to_connected_users()
    finally:
        # Ensure for proper disconnection from the IRC server
        pomo.end_session()
        pomo.clear_database()


if __name__ == "__main__":
    main()
