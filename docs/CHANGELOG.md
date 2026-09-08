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
