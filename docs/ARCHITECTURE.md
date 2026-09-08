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

## Translation production and analysis consumption

Translation is derived processing and never changes `messages.content`. Conversation
completion and message edits can enqueue bounded in-memory jobs for enabled analysis
channels. The asynchronous worker uses configured translation providers and stores
results in `message_translations`, identified by message, target language, and exact
source-content hash.

`AnalysisTextResolver` is the read boundary between stored translations and analysis
preparation. It computes current source hashes, reads translation candidates for all
eligible messages in one repository call, and selects only exact hash matches. The
resulting `AnalysisMessageDTO` keeps `content` and `language` as raw-source fields and
exposes the selected `analysis_content`, `analysis_language`, source kind, current
source hash, and optional translation ID separately.

- Same-language messages use raw content without a translation lookup.
- Missing or blank translations use the configured missing-translation policy; the
  default policy keeps analysis available with explicitly marked raw text.
- Historical nullable or blank source-language values are normalized to the existing
  `unknown` analysis contract at this read boundary; stored message rows are untouched.
- Stale translation rows remain preserved for history but are never selected.
- Soft-deleted messages remain excluded by normal analysis scope queries and are also
  rejected by the text resolver if passed directly.
- Analysis preparation performs database reads only. It does not call translation
  providers or any external network API.

## Topic detection foundation

`TopicDetectionService` consumes an already prepared `AnalysisDatasetDTO`. It maps
each analysis message to an immutable provider input containing
`analysis_content`, analysis/source languages, message identity, and translation
provenance. Raw `content` is deliberately absent from the provider contract.

The provider-independent boundary returns opaque topic IDs, optional labels,
message memberships, and explicit unassigned/noise message IDs. Before returning a
result, the service verifies that provider output is an exact partition of the
input dataset: IDs outside the dataset, duplicate topic or message assignments, and
omitted messages are rejected. This keeps soft-deleted messages excluded by the
upstream analysis policy and prevents a provider from reintroducing them.

No production detector, clustering policy, external provider, or persistence path
is selected yet. Topic count, hierarchy, thresholds, and provider choice remain
behind the provider interface.

## Topic summarization foundation

`TopicSummarizationService` consumes a validated `TopicDetectionResultDTO` and
creates immutable provider inputs for each detected topic. Inputs contain only the
prepared `TopicDetectionMessageDTO` records, the topic identity and optional label,
and an explicit output language. Topic members are ordered by `created_at` and then
message ID before the provider boundary. Raw `messages.content` is not part of this
contract.

The provider returns a summary and evidence message IDs for every detected topic.
The service rejects blank summaries, empty or duplicate evidence, evidence outside
the corresponding topic, and duplicate, unknown, or omitted topic summaries. It
materializes results in detected-topic order while retaining every prepared topic
message, source-content hash, translation ID, detector/summarizer identity, analysis
scope, output language, and explicit unassigned/noise messages.

No production summarizer, persistence path, bot wiring, or newspaper composition is
selected yet.

## Analysis-run orchestration foundation

`AnalysisRunService` is the application boundary from an `AnalysisRequestDTO` to
validated topic summaries. It calls `AnalysisService.prepare_dataset` through
`asyncio.to_thread`, keeping the existing synchronous SQLite repository layer out
of a future async caller's event-loop thread. It then invokes the injected
`TopicDetectionService` and passes that validated result to the injected
`TopicSummarizationService`.

Every run requires explicit positive message-count and prepared-text character
limits. The service measures `analysis_content`, rejects an oversized dataset before
either AI provider is invoked, and does not define production limits, tokens,
pricing, or batching policy. Analysis-scope repository reads are ordered by
`created_at` and then Discord message ID.

The provider-independent run result contains dataset metadata, measured input size,
the applied limits, scope, output language, detector/summarizer identity, validated
topic summaries with prepared-message provenance, and explicit unassigned/noise
messages. It does not expose the raw `AnalysisDatasetDTO` to a future newspaper
composer.

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

Automatic translation production, current-translation analysis preparation, and
provider-independent topic detection, summarization, and analysis-run orchestration
contracts are implemented. Production topic/summarization providers and AI
newspaper generation remain future architecture.
