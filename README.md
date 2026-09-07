# Project Chronicle / DiscordDailyPress

Project Chronicle is a Discord data collection and analysis system that is being built toward AI-assisted newspaper generation. It currently collects guild messages, preserves their raw records, and provides channel-scoped analysis and statistics in Discord. Automatic translation and AI newspaper generation are not implemented yet.

## Current capabilities

- Collect Discord guild messages and retain edit and deletion history.
- Preserve deleted messages with soft delete rather than removing their database rows.
- Prevent duplicate Discord create events from creating duplicate rows or conversation entries.
- Group short message conversations in memory and detect their language.
- Restrict analysis to enabled `CollectionChannel` records and show KST-based statistics in Discord embeds.
- Manage the `messages.deleted_at` schema change with Alembic.

## Architecture at a glance

`Discord Gateway -> ChronicleBot -> MessageCollector -> DTO/Mapper -> MessageService -> Repository -> SQLite`

`ConversationBuffer` sits alongside message persistence for short-lived in-memory conversation grouping. Analysis resolves enabled channels through `CollectionChannel` and produces statistics from stored messages.

## Development setup

Project Chronicle targets Python 3.11.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

This activation-free PowerShell setup also works when script execution policy blocks
`Activate.ps1`. Use `.\.venv\Scripts\python.exe` in place of `python` for the
commands below if the environment is not activated.

On Ubuntu/Linux, ensure Python 3.11 includes venv support (`python3.11-venv` in
Ubuntu packages), then run:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
```

`requirements-dev.txt` installs the runtime dependencies plus the test runner and
the legacy `langdetect` package used by the language-detection benchmark tests.
Use `requirements.txt` for a runtime-only installation.

Configure `.env` before running. At minimum, provide the Discord bot settings required by your deployment, including `DISCORD_BOT_TOKEN` and `DISCORD_GUILD_ID`. Other configured integration values should only be supplied when their corresponding integration is in use.

Run the bot:

```powershell
python main.py
```

Run tests:

```powershell
python -m pytest
```

Apply database migrations:

```powershell
python -m alembic upgrade head
```

The SQLite database is stored at `storage/database/chronicle.db`. For an existing database, apply migrations before running code that requires the newer schema. The Alembic baseline and migrations are designed to preserve existing rows and content.

## Data and time contracts

- Raw Discord messages are the source of truth. Derived work such as translation, summaries, statistics, and newspapers must not overwrite `messages.content`.
- Discord message deletion is a soft delete: the original message row and content remain, while deletion history is recorded.
- `CollectionChannel` identifies a channel included in analysis; it does not grant or deny message collection. Guild messages may be collected broadly.
- Internal database datetimes and query boundaries use UTC. User-entered periods, Discord-facing dates, and daily/hourly statistics use KST unless stated otherwise.

## Current status and roadmap

The implemented system covers collection, raw-data preservation, message lifecycle handling, language detection, scoped analysis, and statistics. Translation workflows and automated AI newspaper generation remain future work; they are not represented as completed features in this repository.
