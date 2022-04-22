# This file produces a valid credential file required by Pomodorotteux to connect to twitch IRC server
# To get a valid OAuth key, you can visit the following website
# https://twitchapps.com/tmi/#access_token=7ld7okcsiozvkrcjdwt3z9y31ajrzk&scope=chat%3Aread+chat%3Aedit+channel%3Amoderate+whispers%3Aread+whispers%3Aedit+channel_editor&token_type=bearer
from pomodorotteux import TwitchConfiguration


CHANNEL = 'THE_CHANNEL_NAME_HERE'
AUTHORIZATION_OAUTH = "oauth:MY_KEY_HERE"


def main():
    TwitchConfiguration.generate_file(
        path="my_config_file.key",
        channel_name=CHANNEL,
        oauth_key=AUTHORIZATION_OAUTH,
    )


if __name__ == "__main__":
    main()
