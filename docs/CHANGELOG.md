# Changelog

## Unreleased

### Translation

- Added derived `message_translations` storage keyed by message, target language, and source-content hash without overwriting raw message content.
- Added a bounded translation queue and single asynchronous worker with stale-source, edit, delete, duplicate, and shutdown handling.
- Added Gemini and NVIDIA translation providers in fallback order, with protected-token output integrity validation.
- Connected conversation completion and message edits to translation job production for enabled analysis channels.
- Added an integration test covering conversation flush through derived translation persistence.

### Analysis translation consumption

- Added a batch repository read that selects translations matching each message's current source-content hash while preserving stale rows.
- Added an analysis text resolver with an isolated missing-translation policy and raw-source fallback.
- Extended analysis messages with explicit prepared text, language, source kind, current hash, and translation provenance without changing raw fields.
- Connected `AnalysisRequestDTO.output_language` to AnalysisDataset preparation while keeping existing source-language statistics unchanged.
- Normalized historical nullable or blank source-language values to the existing `unknown` contract during analysis preparation without updating stored messages.

### Topic detection foundation

- Added provider-independent DTO and asynchronous service contracts that consume prepared `analysis_content` without exposing raw message content to detectors.
- Preserved message identity, analysis/source languages, current-content hash, and translation provenance in topic membership results.
- Added strict partition validation for topic membership and explicit unassigned/noise messages, rejecting unknown, duplicate, or omitted message IDs.
- Added deterministic provider tests without external API calls or persistence changes.

### Topic summarization foundation

- Added immutable provider inputs that carry detected topic identity, optional labels, explicit output language, and prepared analysis messages without raw message content.
- Added an asynchronous provider boundary and service that require exactly one nonblank, evidence-linked summary per detected topic.
- Added strict validation for duplicate, unknown, or omitted topics and for empty, duplicate, or cross-topic evidence message IDs.
- Preserved analysis scope, detector/summarizer identity, output language, prepared source hashes, translation provenance, and explicit unassigned/noise messages in summary results.
- Added deterministic topic-message ordering and provider-independent tests without external API calls or persistence changes.

### Analysis-run orchestration foundation

- Added a provider-independent async service that composes prepared analysis datasets through topic detection and topic summarization.
- Moved synchronous scope resolution, SQLite reads, and translation selection off the future async caller thread with an application-level `asyncio.to_thread` boundary.
- Added mandatory caller-supplied message-count and prepared-text character limits that reject oversized runs before provider invocation.
- Ordered analysis-scope messages by creation time and Discord message ID for deterministic provider input.
- Preserved scope, output language, provider identities, dataset metadata, source hashes, translation provenance, evidence, and explicit unassigned/noise messages in the orchestration result.

### Deterministic newspaper composer foundation

- Added immutable provider-independent newspaper edition, topic section, and content-free message provenance DTOs.
- Added a pure in-memory composer from validated analysis-run results to deterministic Markdown without another AI generation stage.
- Ordered sections chronologically by earliest topic message time and stable message identity, with topic ID as a final tie-breaker.
- Derived edition dates and displayed scope boundaries in KST while retaining exact UTC scope boundaries for auditability.
- Preserved validated summaries, evidence IDs/counts, source hashes, translation provenance, and explicit unassigned/noise messages without rendering prepared or raw message content.
- Escaped dynamic HTML and Markdown syntax so provider-originated labels, summaries, and identifiers cannot alter the fixed edition structure.

### Development environment

- Declared runtime and test dependencies for the supported Python 3.11 environment.
- Documented the central Ubuntu `chronicle-dev` environment and its `uv`-managed setup.

### Stabilization

- Clarified that `CollectionChannel` selects analysis targets and does not control whether guild messages are collected.
- Added repository-level agent rules documenting raw-data preservation, soft-delete, layering, scope, and time contracts.
- Added atomic message soft delete with deletion history and a safe Alembic migration for nullable `messages.deleted_at`.
- Normalized UTC storage and query behavior while interpreting analysis inputs and presenting statistics in KST.
- Stabilized `ConversationBuffer` timeout, cleanup, flush, and shutdown lifecycle behavior.
- Made message creation idempotent across duplicate Discord create events, preserving original content and avoiding duplicate conversation buffering.
- Declared the `fasttext-langdetect` dependency used by the language detection path.
