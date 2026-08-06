from app.bot.bot import ChronicleBot
from app.core.bootstrap import bootstrap
from app.core.config import config


def main():
    bootstrap()

    bot = ChronicleBot()

    bot.run(config.discord_bot_token)


if __name__ == "__main__":
    main()