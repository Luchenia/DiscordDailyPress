from app.core.config import config


def main():
    print("=" * 50)
    print(" Project Chronicle ")
    print("=" * 50)

    print(f"Storage : {config.storage_dir}")
    print(f"Database : {config.database_dir}")

    print("\nBootstrap Success!")


if __name__ == "__main__":
    main()