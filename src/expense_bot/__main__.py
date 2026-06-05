from expense_bot.config import load_config
from expense_bot.telegram_app import build_application

def main() -> None:
    config = load_config()
    application = build_application(config)
    application.run_polling()

if __name__ == "__main__":
    main()
