# Project Chronicle / DiscordDailyPress

Project Chronicle is a Discord data collection and analysis system that is being built toward AI-assisted newspaper generation. It currently collects guild messages, preserves their raw records, provides channel-scoped analysis and statistics in Discord, and stores derived message translations without changing the source messages. Topic detection, summarization, and AI newspaper generation are not implemented yet.

## Current capabilities

- Collect Discord guild messages and retain edit and deletion history.
- Preserve deleted messages with soft delete rather than removing their database rows.
- Prevent duplicate Discord create events from creating duplicate rows or conversation entries.
- Group short message conversations in memory and detect their language.
- Restrict analysis to enabled `CollectionChannel` records and show KST-based statistics in Discord embeds.
- Queue translation work after conversation processing or message edits for enabled analysis channels.
- Translate with Gemini first and NVIDIA as fallback, rejecting outputs that alter protected Discord, URL, code, emoji, or Markdown tokens.
- Store translations in `message_translations` by source-content hash while preserving `messages.content`.
- Prepare analysis datasets with current translations when available, while retaining raw content, source language, and translation provenance explicitly.
- Manage the `messages.deleted_at` and `message_translations` schema changes with Alembic.

## Architecture at a glance

`Discord Gateway -> ChronicleBot -> MessageCollector -> DTO/Mapper -> MessageService -> Repository -> SQLite`

`ConversationBuffer` sits alongside message persistence for short-lived in-memory conversation grouping. Analysis resolves enabled channels through `CollectionChannel` and produces statistics from stored messages.

When at least one translation API key is configured, completed conversations produce bounded in-memory translation jobs. A single asynchronous worker calls the configured providers and stores current, non-deleted results as derived rows. Database work runs outside the Discord event loop.

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

The central development environment is the Ubuntu remote host `chronicle-dev` with
the repository at `/home/amadeus/projects/DiscordDailyPress`. Its environment is
managed with `uv`; it intentionally does not require `pip` inside `.venv`:

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r requirements-dev.txt
cp -n .env.example .env
```

On another Ubuntu/Linux host, a standard Python 3.11 virtual environment with
`pip` is also supported. Install the Ubuntu `python3.11-venv` package first when
needed, then use `python3.11 -m venv .venv` and install `requirements-dev.txt`.

`requirements-dev.txt` installs the runtime dependencies plus the test runner and
the legacy `langdetect` package used by the language-detection benchmark tests.
Use `requirements.txt` for a runtime-only installation.

Configure `.env` before running. At minimum, provide the Discord bot settings required by your deployment, including `DISCORD_BOT_TOKEN` and `DISCORD_GUILD_ID`. Other configured integration values should only be supplied when their corresponding integration is in use.

Run the bot:

```bash
.venv/bin/python main.py
```

Run tests:

```bash
.venv/bin/python -m pytest
```

Apply database migrations:

```bash
.venv/bin/python -m alembic upgrade head
```

The SQLite database is stored at `storage/database/chronicle.db`. For an existing database, apply migrations before running code that requires the newer schema. The Alembic baseline and migrations are designed to preserve existing rows and content.

## Data and time contracts

- Raw Discord messages are the source of truth. Derived work such as translation, summaries, statistics, and newspapers must not overwrite `messages.content`.
- Discord message deletion is a soft delete: the original message row and content remain, while deletion history is recorded.
- `CollectionChannel` identifies a channel included in analysis; it does not grant or deny message collection. Guild messages may be collected broadly.
- Internal database datetimes and query boundaries use UTC. User-entered periods, Discord-facing dates, and daily/hourly statistics use KST unless stated otherwise.

## Current status and roadmap

The implemented system covers collection, raw-data preservation, message lifecycle handling, language detection, scoped analysis and statistics, and the automatic translation producer/queue/worker/storage pipeline. Analysis dataset preparation resolves current translations in a batch and falls back to clearly marked raw source text when a translation is missing; stale translations are preserved but never selected. Topic detection and newspaper generation do not yet consume those prepared datasets, and the queue is in-memory with no restart recovery or automatic retry. Live Discord and external-provider validation on a new host requires an explicit operational approval because it can contact external services and incur cost.
