# Changelog

## Unreleased

### Translation

- Added derived `message_translations` storage keyed by message, target language, and source-content hash without overwriting raw message content.
- Added a bounded translation queue and single asynchronous worker with stale-source, edit, delete, duplicate, and shutdown handling.
- Added Gemini and NVIDIA translation providers in fallback order, with protected-token output integrity validation.
- Connected conversation completion and message edits to translation job production for enabled analysis channels.
- Added an integration test covering conversation flush through derived translation persistence.

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
