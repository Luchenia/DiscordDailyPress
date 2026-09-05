# Architecture

## Runtime flow

Discord Gateway events are received by `ChronicleBot`. The bot delegates message events to `MessageCollector`, which converts Discord payloads into DTOs and passes them through the mapper and service layer:

`Discord Gateway -> ChronicleBot -> MessageCollector -> DTO / Mapper -> MessageService -> Repository -> SQLite`

`MessageService` owns message lifecycle rules and coordinates repositories. Repositories perform SQLite persistence through SQLAlchemy. Command handlers remain thin and delegate business behavior to services where practical.

## Message collection and lifecycle

- `MessageCollector` handles create, edit, and delete event flows.
- Discord DTOs retain UTC-aware event datetimes where provided. Mapper and service code normalize stored/comparison values to UTC.
- `MessageService` persists new messages, records edits through message history, and handles deletes as an atomic logical operation.
- A Discord delete creates `MessageDeleteHistory` and sets `messages.deleted_at`; it does not hard-delete the `messages` row or clear `messages.content`.
- Repeated delete events are idempotent: an already deleted message is not damaged or given duplicate deletion history.
- `discord_message_id` remains unique. On a duplicate create race, the repository rolls back the failed insert and returns the existing row as an existing result. The service does not overwrite its content or add it to `ConversationBuffer` again.

## ConversationBuffer and language detection

`ConversationBuffer` is an in-memory buffer keyed by conversation/session identity. It groups short-lived message sequences, flushes expired sessions, flushes an old session before accepting a late new message, and flushes remaining sessions during bot shutdown. Cleanup and shutdown share centralized flush behavior; handler failures are logged without terminating future cleanup cycles.

On flush, the current language detection path uses the fastText-backed `fasttext-langdetect` integration through the language service. This is language metadata processing, not a translation pipeline.

## Analysis scope and statistics

Collection and analysis are intentionally separate:

- Guild messages may be collected broadly.
- `CollectionChannel` means an enabled analysis target, not collection permission.
- `AnalysisScopeResolver` resolves enabled channels for the requested guild and creates the analysis scope.
- `AnalysisService` queries that scope, while `StatisticsService` aggregates authors, channels, dates, hours, and language data.
- Normal analysis queries exclude soft-deleted messages with `deleted_at IS NULL`; raw-data access can still retrieve preserved deleted rows when needed.

Analysis commands render results in Discord embeds. They present user-facing dates and times in KST.

## Database, migrations, and time contract

SQLite is the current persistence store. The application bootstrap creates tables for a new local database, while Alembic tracks schema evolution for existing installations. The current migration baseline supports databases that were previously initialized by the ORM, and the forward migration adds nullable `messages.deleted_at` without rewriting or deleting existing SQLite data.

The time contract is:

- Store, compare, and query database timestamps in UTC.
- Interpret user-specified analysis periods as KST, then convert their boundaries to UTC before querying.
- Convert UTC timestamps to KST for Discord-facing display and daily/hourly statistical grouping.
- SQLite legacy values that lack timezone metadata are handled at a single datetime helper boundary as UTC values; no bulk legacy timestamp rewrite is performed.

## Data principles

- Raw message records are the source of truth.
- `messages.content` is immutable with respect to translation and other derived processing.
- Translation, summaries, statistics, and newspapers are derived and regenerable data.
- Discord deletion is soft delete, preserving the original row/content and recording deletion history.
- Collection policy and analysis inclusion are separate concerns.

Automatic translation and AI newspaper generation are project goals, not current production architecture.
